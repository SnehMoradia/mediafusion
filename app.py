import os
import sys
import subprocess
import tempfile
import shutil
import urllib.parse
import yt_dlp
import requests
from flask import Flask, request, jsonify, render_template, send_file, after_this_request, Response, stream_with_context
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

def clean_error_message(e):
    err_str = str(e)
    clean_msg = re.sub(r'\x1b\[[0-9;]*[mGKS]', '', err_str).strip()
    
    if "Sign in to confirm you're not a bot" in clean_msg:
        return "YouTube restricted access to this video. Please try a different public YouTube video or playlist link."
    elif "Video unavailable" in clean_msg or "This video is unavailable" in clean_msg:
        return "This video is unavailable or has been removed from YouTube."
    elif clean_msg.startswith("ERROR: [youtube]"):
        clean_msg = re.sub(r'^ERROR:\s*\[youtube\]\s*[\w-]+:\s*', '', clean_msg)
    
    return clean_msg

@app.route('/api/playlist-info', methods=['POST'])
def playlist_info():
    data = request.get_json() or {}
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'Please provide a valid URL'}), 400

    try:
        info = dm.extract_info(url)
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'error': clean_error_message(e)}), 400

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

from flask import Flask, request, jsonify, render_template, send_file, after_this_request, Response, stream_with_context

@app.route('/api/download/direct', methods=['GET'])
def get_direct_stream_url():
    video_url = request.args.get('url', '').strip()
    format_type = request.args.get('format', 'video').strip()
    quality = request.args.get('quality', 'best').strip()

    if not video_url:
        return jsonify({'error': 'URL parameter is required'}), 400

    try:
        ydl_opts = _get_default_ydl_opts()
        ydl_opts['skip_download'] = True
        
        if format_type == 'audio':
            ydl_opts['format'] = '140/ba/bestaudio/best'
        else:
            if quality == '1080p':
                ydl_opts['format'] = '22/bestvideo[height<=1080]+bestaudio/18/best'
            elif quality == '720p':
                ydl_opts['format'] = '22/bestvideo[height<=720]+bestaudio/18/best'
            elif quality == '480p':
                ydl_opts['format'] = '18/bestvideo[height<=480]+bestaudio/best'
            elif quality == '360p':
                ydl_opts['format'] = '18/best'
            else:
                ydl_opts['format'] = '22/18/best'

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

        if not info:
            return jsonify({'error': 'Could not extract media stream'}), 400

        stream_url = info.get('url')
        if not stream_url and info.get('requested_formats'):
            stream_url = info['requested_formats'][0].get('url')
        if not stream_url and info.get('formats'):
            for fmt in reversed(info['formats']):
                if fmt.get('url') and (fmt.get('vcodec') != 'none' or format_type == 'audio'):
                    stream_url = fmt['url']
                    break
            if not stream_url:
                stream_url = info['formats'][-1].get('url')

        if not stream_url:
            return jsonify({'error': 'Stream URL not available'}), 404

        title = info.get('title') or 'media'
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
        match = re.search(r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})', video_url)
        if match:
            v_id = match.group(1)
            try:
                with yt_dlp.YoutubeDL(_get_default_ydl_opts()) as ydl:
                    info = ydl.extract_info(f"ytsearch1:{v_id}", download=False)
                    if info and info.get('entries'):
                        entry = info['entries'][0]
                        stream_url = entry.get('url')
                        title = entry.get('title') or 'media'
                        clean_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
                        return jsonify({
                            'success': True,
                            'download_url': stream_url,
                            'title': title,
                            'filename': f"{clean_title}.mp4",
                            'ext': 'mp4'
                        })
            except Exception:
                pass
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
