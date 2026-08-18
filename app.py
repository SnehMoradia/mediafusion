import os
import sys
import subprocess
import tempfile
import shutil
import urllib.parse
import yt_dlp
import requests
from flask import Flask, request, jsonify, render_template, send_file, after_this_request, Response, stream_with_context, redirect
from flask_cors import CORS
from downloader import DownloadManager, _get_default_ydl_opts, FFMPEG_PATH

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

dm = DownloadManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/default-folder', methods=['GET'])
def get_default_folder():
    host = request.host.lower()
    is_cloud = not ('localhost' in host or '127.0.0.1' in host)
    
    if is_cloud:
        return jsonify({'is_cloud': True, 'path': 'Browser Downloads Folder'})
    else:
        default_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'PlaylistDownloads')
        return jsonify({'is_cloud': False, 'path': default_dir})

import re
from downloader import resolve_cookie_file

def clean_error_message(e):
    err_str = str(e)
    clean_msg = re.sub(r'\x1b\[[0-9;]*[mGKS]', '', err_str).strip()
    
    if re.search(r"Sign in to confirm you['\u2019]re not a bot", clean_msg, re.IGNORECASE):
        return "YouTube restricted cloud/datacenter access for this video (Bot Check). To fix this on Vercel/Cloud: Add your exported YouTube cookies to the 'YOUTUBE_COOKIES' environment variable in Vercel settings (or paste into cookies.txt). Alternatively, run the app locally on localhost:5050."
    elif re.search(r"(?:This\s+)?video is unavailable", clean_msg, re.IGNORECASE):
        return "This video is unavailable or has been removed from YouTube."
    elif clean_msg.startswith("ERROR: [youtube]"):
        clean_msg = re.sub(r'^ERROR:\s*\[youtube\]\s*[\w-]+:\s*', '', clean_msg)
    
    return clean_msg

@app.route('/api/cookies/status', methods=['GET'])
def cookies_status():
    cookie_path = resolve_cookie_file()
    has_cookies = cookie_path is not None and os.path.exists(cookie_path)
    return jsonify({
        'has_cookies': has_cookies,
        'message': 'Cookies active and configured' if has_cookies else 'No active YouTube cookies configured'
    })

@app.route('/api/cookies/save', methods=['POST'])
def save_cookies():
    data = request.get_json() or {}
    raw_cookies = data.get('cookies', '').strip()
    if not raw_cookies:
        return jsonify({'success': False, 'error': 'Cookie content is empty'}), 400

    writable_cookie_path = os.path.join(tempfile.gettempdir(), 'yt_writable_cookies.txt')
    try:
        with open(writable_cookie_path, 'w', encoding='utf-8') as f:
            f.write(raw_cookies)
        return jsonify({'success': True, 'message': 'Cookies saved for this session'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/playlist-info', methods=['POST'])
def playlist_info():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'success': False, 'error': 'Please provide a valid URL'}), 200

    try:
        info = dm.extract_info(url)
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': clean_error_message(e)}), 200

@app.route('/api/download/start', methods=['POST'])
def start_download():
    data = request.get_json() or {}
    items = data.get('items', [])
    format_type = data.get('format', 'video')
    quality = data.get('quality', 'best')
    output_dir = data.get('output_dir', '').strip()

    if not items:
        return jsonify({'error': 'No items selected for download'}), 400

    if not output_dir:
        output_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'PlaylistDownloads')

    try:
        job_id, final_output_dir = dm.start_download_job(items, format_type, quality, output_dir)
        return jsonify({
            'success': True,
            'job_id': job_id,
            'output_dir': final_output_dir,
            'total_items': len(items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download/status/<job_id>', methods=['GET'])
def job_status(job_id):
    status = dm.get_job_status(job_id)
    if not status:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'success': True, 'job': status})

@app.route('/api/download/cancel/<job_id>', methods=['POST'])
def cancel_download(job_id):
    success = dm.cancel_job(job_id)
    return jsonify({'success': success})

@app.route('/api/open-folder', methods=['POST'])
def open_folder():
    data = request.get_json() or {}
    folder_path = data.get('path', '').strip()
    
    if not folder_path or not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)

    try:
        if sys.platform == 'win32':
            os.startfile(folder_path)
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', folder_path])
        else:
            subprocess.Popen(['xdg-open', folder_path])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _get_media_stream_url(video_url, format_type='video', quality='best'):
    def extract_stream_from_info(info):
        if not info:
            return None
        formats = info.get('formats', [])
        if not formats:
            return info.get('url')

        valid_formats = [f for f in formats if f.get('url') and f.get('url').startswith('http')]

        if format_type == 'audio':
            audio_formats = [f for f in valid_formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            if audio_formats:
                audio_formats.sort(key=lambda x: x.get('abr') or x.get('tbr') or 0, reverse=True)
                return audio_formats[0].get('url')
            for f in reversed(valid_formats):
                if f.get('acodec') != 'none':
                    return f.get('url')
        else:
            muxed_formats = [f for f in valid_formats if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            target_height = None
            if quality == '1080p': target_height = 1080
            elif quality == '720p': target_height = 720
            elif quality == '480p': target_height = 480
            elif quality == '360p': target_height = 360

            if muxed_formats:
                if target_height:
                    matching = [f for f in muxed_formats if (f.get('height') or 0) <= target_height]
                    if matching:
                        matching.sort(key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                        return matching[0].get('url')
                muxed_formats.sort(key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                return muxed_formats[0].get('url')

            video_formats = [f for f in valid_formats if f.get('vcodec') != 'none']
            if video_formats:
                video_formats.sort(key=lambda x: (x.get('height') or 0, x.get('tbr') or 0), reverse=True)
                return video_formats[0].get('url')

        return info.get('url') or (valid_formats[-1].get('url') if valid_formats else None)

    primary_err = None

    client_strategies = [
        ['android', 'ios'],
        ['ios', 'mweb', 'android', 'tv'],
        ['tv_embedded', 'mweb'],
        ['web_creator', 'android'],
        None
    ]

    for clients in client_strategies:
        try:
            ydl_opts = _get_default_ydl_opts()
            ydl_opts['skip_download'] = True
            if clients:
                ydl_opts.setdefault('extractor_args', {}).setdefault('youtube', {})['player_client'] = clients
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)
                url = extract_stream_from_info(info)
                if url:
                    title = info.get('title') or 'media'
                    return url, title
        except Exception as e:
            if not primary_err:
                primary_err = e

    # Strategy: Direct video ID search lookup fallback
    match = re.search(r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})', video_url)
    if match:
        v_id = match.group(1)
        for clients in client_strategies:
            try:
                search_opts = _get_default_ydl_opts()
                search_opts['skip_download'] = True
                if clients:
                    search_opts.setdefault('extractor_args', {}).setdefault('youtube', {})['player_client'] = clients
                with yt_dlp.YoutubeDL(search_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={v_id}", download=False)
                    url = extract_stream_from_info(info)
                    if url:
                        title = info.get('title') or 'media'
                        return url, title
            except Exception:
                pass

    raise primary_err or ValueError("Could not extract media stream")

@app.route('/api/download/direct', methods=['GET'])
def get_direct_stream_url():
    video_url = request.args.get('url', '').strip()
    format_type = request.args.get('format', 'video').strip()
    quality = request.args.get('quality', 'best').strip()

    if not video_url:
        return jsonify({'success': False, 'error': 'URL parameter is required'}), 200

    try:
        stream_url, title = _get_media_stream_url(video_url, format_type, quality)
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        ext = 'mp3' if format_type == 'audio' else 'mp4'
        filename = f"{clean_title}.{ext}"

        return jsonify({
            'success': True,
            'download_url': stream_url,
            'title': title,
            'filename': filename,
            'ext': ext
        })
    except Exception as e:
        return jsonify({'success': False, 'error': clean_error_message(e)}), 200

@app.route('/api/download/proxy', methods=['GET'])
def proxy_download():
    video_url = request.args.get('url', '').strip()
    format_type = request.args.get('format', 'video').strip()
    quality = request.args.get('quality', 'best').strip()

    if not video_url:
        return jsonify({'error': 'URL parameter is required'}), 400

    try:
        stream_url, title = _get_media_stream_url(video_url, format_type, quality)
        clean_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
        ext = 'mp3' if format_type == 'audio' else 'mp4'
        filename = f"{clean_title}.{ext}"

        r = requests.get(stream_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'}, timeout=20)

        def generate():
            for chunk in r.iter_content(chunk_size=65536):
                if chunk:
                    yield chunk

        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Type': 'application/octet-stream',
        }
        if 'Content-Length' in r.headers:
            headers['Content-Length'] = r.headers['Content-Length']

        return Response(stream_with_context(generate()), headers=headers)
    except Exception as e:
        return jsonify({'error': clean_error_message(e)}), 400


@app.route('/api/download/stream', methods=['GET'])
def stream_download():
    video_url = request.args.get('url', '').strip()
    format_type = request.args.get('format', 'audio')
    quality = request.args.get('quality', 'best')

    if not video_url:
        return jsonify({'error': 'URL is required'}), 400

    temp_dir = tempfile.mkdtemp()
    
    try:
        ydl_opts = _get_default_ydl_opts()
        out_tmpl = os.path.join(temp_dir, '%(title)s [%(id)s].%(ext)s')
        ydl_opts['outtmpl'] = out_tmpl

        if FFMPEG_PATH:
            ydl_opts['ffmpeg_location'] = FFMPEG_PATH

        if format_type == 'audio':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320' if quality == 'best' else '192',
            }]
        else:
            if quality == '1080p':
                ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
            elif quality == '720p':
                ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
            elif quality == '480p':
                ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            elif quality == '360p':
                ydl_opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]/best'
            else:
                ydl_opts['format'] = 'bestvideo+bestaudio/best'
            ydl_opts['merge_output_format'] = 'mp4'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        downloaded_files = [
            os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
            if not f.endswith('.part') and not f.endswith('.ytdl')
        ]
        if not downloaded_files:
            return jsonify({'error': 'Failed to process media file'}), 500

        target_file = downloaded_files[0]
        filename = os.path.basename(target_file)
        
        @after_this_request
        def cleanup(response):
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass
            return response

        return send_file(
            target_file,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return jsonify({'error': clean_error_message(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"\n========================================================")
    print(f" Playlist Downloader running at http://localhost:{port}")
    print(f"========================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
