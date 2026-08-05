import os
import time
import uuid
import threading
import shutil
import re
import json
import requests
import yt_dlp

# Detect ffmpeg binary path via imageio_ffmpeg or system PATH
def _get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which('ffmpeg')

FFMPEG_PATH = _get_ffmpeg_path()

def _get_default_ydl_opts():
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocolor': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
    }
    if shutil.which('node'):
        opts['js_runtimes'] = {'node': {}}
    return opts

class DownloadManager:
    def __init__(self):
        self.jobs = {}  # job_id -> job_info dict

    def extract_info(self, url):
        """Extract metadata for YouTube, Instagram, or Spotify URLs."""
        url_lower = url.lower().strip()
        
        if 'spotify.com' in url_lower or 'spotify.link' in url_lower:
            return self._extract_spotify_info(url)
        elif 'instagram.com' in url_lower or 'instagr.am' in url_lower:
            return self._extract_instagram_info(url)
        else:
            return self._extract_youtube_info(url)

    def _extract_youtube_info(self, url):
        """Extract metadata for a playlist or single video URL using yt-dlp."""
        ydl_opts = _get_default_ydl_opts()
        ydl_opts['extract_flat'] = 'in_playlist'
        ydl_opts['skip_download'] = True
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if not info:
            raise ValueError("Could not fetch information for the provided URL.")

        is_playlist = 'entries' in info and info['entries'] is not None

        items = []
        if is_playlist:
            playlist_title = info.get('title') or 'Playlist'
            uploader = info.get('uploader') or info.get('channel') or 'Unknown Uploader'
            thumbnail = info.get('thumbnails', [{}])[-1].get('url') if info.get('thumbnails') else ''
            
            for idx, entry in enumerate(info['entries']):
                if not entry:
                    continue
                video_id = entry.get('id')
                video_url = entry.get('url') or entry.get('webpage_url') or f"https://www.youtube.com/watch?v={video_id}"
                
                entry_thumb = entry.get('thumbnails', [{}])[-1].get('url') if entry.get('thumbnails') else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                
                items.append({
                    'index': idx + 1,
                    'id': video_id,
                    'title': entry.get('title') or f"Video {idx + 1}",
                    'uploader': entry.get('uploader') or entry.get('channel') or uploader,
                    'duration': entry.get('duration') or 0,
                    'thumbnail': entry_thumb,
                    'url': video_url
                })
        else:
            playlist_title = info.get('title') or 'Single Video'
            uploader = info.get('uploader') or info.get('channel') or 'Unknown Uploader'
            thumbnail = info.get('thumbnail') or (info.get('thumbnails', [{}])[-1].get('url') if info.get('thumbnails') else '')
            video_id = info.get('id')
            video_url = info.get('webpage_url') or url
            
            items.append({
                'index': 1,
                'id': video_id,
                'title': playlist_title,
                'uploader': uploader,
                'duration': info.get('duration') or 0,
                'thumbnail': thumbnail or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                'url': video_url
            })

        return {
            'is_playlist': is_playlist,
            'title': playlist_title,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'total_items': len(items),
            'items': items
        }

    def _extract_instagram_info(self, url):
        """Extract metadata for Instagram Reel, Post, or IGTV link."""
        ydl_opts = {
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if not info:
            raise ValueError("Could not fetch Instagram post details.")

        is_playlist = 'entries' in info and info['entries'] is not None
        items = []

        if is_playlist:
            title = info.get('title') or info.get('description') or 'Instagram Post'
            uploader = info.get('uploader') or info.get('uploader_id') or 'Instagram'
            thumbnail = info.get('thumbnail') or (info.get('thumbnails', [{}])[-1].get('url') if info.get('thumbnails') else '')
            for idx, entry in enumerate(info['entries']):
                if not entry:
                    continue
                v_id = entry.get('id') or f"ig_{idx}"
                v_url = entry.get('webpage_url') or entry.get('url') or url
                thumb = entry.get('thumbnail') or (entry.get('thumbnails', [{}])[-1].get('url') if entry.get('thumbnails') else thumbnail)
                items.append({
                    'index': idx + 1,
                    'id': v_id,
                    'title': entry.get('title') or entry.get('description') or f"Clip {idx + 1}",
                    'uploader': uploader,
                    'duration': entry.get('duration') or 0,
                    'thumbnail': thumb,
                    'url': v_url
                })
        else:
            title = info.get('title') or info.get('description') or 'Instagram Reel'
            if len(title) > 80:
                title = title[:77] + '...'
            uploader = info.get('uploader') or info.get('uploader_id') or 'Instagram'
            thumbnail = info.get('thumbnail') or (info.get('thumbnails', [{}])[-1].get('url') if info.get('thumbnails') else '')
            video_id = info.get('id') or 'instagram_item'
            video_url = info.get('webpage_url') or url

            items.append({
                'index': 1,
                'id': video_id,
                'title': title,
                'uploader': uploader,
                'duration': info.get('duration') or 0,
                'thumbnail': thumbnail,
                'url': video_url
            })

        return {
            'is_playlist': is_playlist and len(items) > 1,
            'title': title,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'total_items': len(items),
            'items': items
        }

    def _search_youtube_track(self, query, index=1):
        """Search YouTube for a Spotify track and return formatted item dict."""
        ydl_opts = {
            'extract_flat': True,
            'skip_download': True,
            'quiet': True,
            'no_warnings': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                res = ydl.extract_info(f"ytsearch1:{query}", download=False)
                if res and 'entries' in res and res['entries']:
                    entry = res['entries'][0]
                    video_id = entry.get('id')
                    video_url = entry.get('url') or f"https://www.youtube.com/watch?v={video_id}"
                    thumb = entry.get('thumbnails', [{}])[-1].get('url') if entry.get('thumbnails') else f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
                    return {
                        'index': index,
                        'id': video_id,
                        'title': entry.get('title') or query,
                        'uploader': entry.get('uploader') or entry.get('channel') or 'YouTube',
                        'duration': entry.get('duration') or 0,
                        'thumbnail': thumb,
                        'url': video_url
                    }
        except Exception as e:
            print(f"Error searching YouTube for '{query}': {e}")
        return None

    def _extract_spotify_info(self, url):
        """Extract metadata for Spotify Track, Playlist, or Album."""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        if '/track/' in url:
            oembed_url = f"https://open.spotify.com/oembed?url={url}"
            r = requests.get(oembed_url, headers=headers, timeout=10)
            if r.status_code != 200:
                raise ValueError("Could not fetch Spotify track details.")
            data = r.json()
            title = data.get('title') or 'Spotify Track'
            thumbnail = data.get('thumbnail_url') or ''
            
            yt_item = self._search_youtube_track(title)
            if yt_item:
                yt_item['title'] = title
                if thumbnail:
                    yt_item['thumbnail'] = thumbnail
                items = [yt_item]
            else:
                raise ValueError(f"Could not find matching video on YouTube for Spotify track '{title}'.")

            return {
                'is_playlist': False,
                'title': title,
                'uploader': 'Spotify',
                'thumbnail': thumbnail or yt_item['thumbnail'],
                'total_items': 1,
                'items': items
            }

        elif '/playlist/' in url or '/album/' in url:
            embed_type = 'playlist' if '/playlist/' in url else 'album'
            match_id = re.search(r'/(playlist|album)/([a-zA-Z0-9]+)', url)
            if not match_id:
                raise ValueError("Invalid Spotify URL format.")
            spotify_id = match_id.group(2)
            embed_url = f"https://open.spotify.com/embed/{embed_type}/{spotify_id}"
            
            r = requests.get(embed_url, headers=headers, timeout=10)
            if r.status_code != 200:
                raise ValueError("Could not fetch Spotify page.")
                
            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text, re.DOTALL)
            if not match:
                raise ValueError("Could not extract Spotify metadata.")
                
            data = json.loads(match.group(1))
            props = data.get('props', {}).get('pageProps', {})
            state = props.get('state', {})
            entity_data = state.get('data', {}).get('entity', {}) if isinstance(state, dict) else {}
            
            playlist_title = entity_data.get('name') or entity_data.get('title') or 'Spotify Collection'
            uploader = entity_data.get('subtitle') or 'Spotify'
            raw_tracks = entity_data.get('trackList', [])
            
            items = []
            for idx, trk in enumerate(raw_tracks):
                t_name = trk.get('title', '')
                t_artist = trk.get('subtitle', '')
                query = f"{t_artist} - {t_name}" if t_artist else t_name
                if not query.strip():
                    continue
                    
                yt_item = self._search_youtube_track(query, index=idx + 1)
                if yt_item:
                    yt_item['title'] = f"{t_artist} - {t_name}" if t_artist else t_name
                    items.append(yt_item)
                    
            if not items:
                raise ValueError("No matching tracks found for this Spotify collection.")
                
            return {
                'is_playlist': True,
                'title': playlist_title,
                'uploader': uploader,
                'thumbnail': items[0]['thumbnail'] if items else '',
                'total_items': len(items),
                'items': items
            }
        else:
            raise ValueError("Unsupported Spotify URL.")

    def start_download_job(self, items, format_type='video', quality='best', output_dir=None):
        """Start downloading selected items in a background thread."""
        if not output_dir:
            output_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'PlaylistDownloads')
        
        os.makedirs(output_dir, exist_ok=True)

        job_id = str(uuid.uuid4())
        
        job_state = {
            'job_id': job_id,
            'status': 'starting', # starting, downloading, completed, cancelled, error
            'total_items': len(items),
            'completed_items': 0,
            'failed_items': 0,
            'output_dir': output_dir,
            'format_type': format_type,
            'quality': quality,
            'cancelled': False,
            'items_status': {
                item['id']: {
                    'id': item['id'],
                    'title': item['title'],
                    'status': 'queued', # queued, downloading, converting, finished, error
                    'progress': 0,
                    'speed': '0 KB/s',
                    'eta': '00:00',
                    'downloaded_bytes': 0,
                    'total_bytes': 0,
                    'error': None
                } for item in items
            }
        }
        
        self.jobs[job_id] = job_state
        
        thread = threading.Thread(target=self._run_download_loop, args=(job_id, items), daemon=True)
        thread.start()
        
        return job_id, output_dir

    def _run_download_loop(self, job_id, items):
        job = self.jobs.get(job_id)
        if not job:
            return

        job['status'] = 'downloading'
        format_type = job['format_type']
        quality = job['quality']
        output_dir = job['output_dir']

        for item in items:
            if job['cancelled']:
                job['status'] = 'cancelled'
                break

            video_id = item['id']
            video_url = item['url']
            item_state = job['items_status'][video_id]
            item_state['status'] = 'downloading'

            # Construct yt-dlp format options
            ydl_opts = self._build_yt_dlp_opts(format_type, quality, output_dir, job_id, video_id)

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])

                if not job['cancelled'] and item_state['status'] != 'error':
                    item_state['status'] = 'finished'
                    item_state['progress'] = 100
                    job['completed_items'] += 1
            except Exception as e:
                item_state['status'] = 'error'
                item_state['error'] = str(e)
                job['failed_items'] += 1

        if not job['cancelled']:
            job['status'] = 'completed'

    def _build_yt_dlp_opts(self, format_type, quality, output_dir, job_id, video_id):
        # Progress hook function
        def progress_hook(d):
            job = self.jobs.get(job_id)
            if not job:
                return

            if job['cancelled']:
                raise Exception("Download cancelled by user.")

            item_state = job['items_status'].get(video_id)
            if not item_state:
                return

            status = d.get('status')
            if status == 'downloading':
                item_state['status'] = 'downloading'
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes') or 0
                item_state['downloaded_bytes'] = downloaded
                item_state['total_bytes'] = total
                
                if total > 0:
                    percent = round((downloaded / total) * 100, 1)
                    item_state['progress'] = min(percent, 99.9)

                speed = d.get('speed')
                if speed:
                    if speed > 1024 * 1024:
                        item_state['speed'] = f"{speed / (1024 * 1024):.1f} MB/s"
                    else:
                        item_state['speed'] = f"{speed / 1024:.1f} KB/s"

                eta = d.get('eta')
                if eta is not None:
                    m, s = divmod(int(eta), 60)
                    h, m = divmod(m, 60)
                    if h > 0:
                        item_state['eta'] = f"{h:02d}:{m:02d}:{s:02d}"
                    else:
                        item_state['eta'] = f"{m:02d}:{s:02d}"

            elif status == 'finished':
                item_state['status'] = 'converting'
                item_state['progress'] = 99.9
                item_state['speed'] = 'Processing...'

        # Base output template
        out_tmpl = os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s')

        opts = _get_default_ydl_opts()
        opts.update({
            'outtmpl': out_tmpl,
            'progress_hooks': [progress_hook],
            'ignoreerrors': True,
        })

        if FFMPEG_PATH:
            opts['ffmpeg_location'] = FFMPEG_PATH

        if format_type == 'audio':
            opts['format'] = 'bestaudio/best'
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320' if quality == 'best' else '192',
            }]
        else:
            # Video format selection
            if quality == '1080p':
                opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
            elif quality == '720p':
                opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
            elif quality == '480p':
                opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]/best'
            elif quality == '360p':
                opts['format'] = 'bestvideo[height<=360]+bestaudio/best[height<=360]/best'
            else:
                opts['format'] = 'bestvideo+bestaudio/best'

            opts['merge_output_format'] = 'mp4'

        return opts

    def get_job_status(self, job_id):
        return self.jobs.get(job_id)

    def cancel_job(self, job_id):
        job = self.jobs.get(job_id)
        if job:
            job['cancelled'] = True
            job['status'] = 'cancelled'
            return True
        return False
