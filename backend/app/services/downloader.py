import os
import re
import uuid
import shutil
import json
import tempfile
import requests
import yt_dlp

def get_ffmpeg_path():
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which('ffmpeg')

FFMPEG_PATH = get_ffmpeg_path()
GLOBAL_COOKIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'cookies.txt')

def get_default_ydl_opts(user_cookies=None, cookie_file_path=None):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'nocolor': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'mweb', 'android', 'tv']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        }
    }
    
    if cookie_file_path and os.path.exists(cookie_file_path):
        opts['cookiefile'] = cookie_file_path
    elif user_cookies and user_cookies.strip():
        temp_cookie = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        temp_cookie.write(user_cookies)
        temp_cookie.close()
        opts['cookiefile'] = temp_cookie.name
    elif os.path.exists(GLOBAL_COOKIES_PATH):
        opts['cookiefile'] = GLOBAL_COOKIES_PATH

    if shutil.which('node'):
        opts['js_runtimes'] = {'node': {}}
        
    return opts

class MediaDownloader:
    def extract_info(self, url: str, user_cookies: str = None):
        """Extract metadata for YouTube, Instagram, or Spotify URLs."""
        url_lower = url.lower().strip()
        if 'spotify.com' in url_lower or 'spotify.link' in url_lower:
            return self._extract_spotify_info(url, user_cookies)
        elif 'instagram.com' in url_lower or 'instagr.am' in url_lower:
            return self._extract_instagram_info(url, user_cookies)
        else:
            return self._extract_youtube_info(url, user_cookies)

    def _extract_youtube_info(self, url: str, user_cookies: str = None):
        info = None
        client_configs = [
            ['ios', 'mweb', 'android', 'tv'],
            ['tv', 'mweb'],
            ['web_creator', 'android']
        ]

        last_error = None
        for clients in client_configs:
            ydl_opts = get_default_ydl_opts(user_cookies=user_cookies)
            ydl_opts['extract_flat'] = 'in_playlist'
            ydl_opts['skip_download'] = True
            ydl_opts['extractor_args'] = {'youtube': {'player_client': clients}}
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                if info:
                    break
            except Exception as e:
                last_error = e

        if not info and last_error:
            err_msg = str(last_error)
            if 'list=' not in url and ('Sign in to confirm' in err_msg or 'unavailable' in err_msg or 'ERROR' in err_msg):
                match = re.search(r'(?:v=|\/|be\/)([a-zA-Z0-9_-]{11})', url)
                if match:
                    video_id = match.group(1)
                    search_item = self._search_youtube_track(f"https://www.youtube.com/watch?v={video_id}", user_cookies=user_cookies)
                    if search_item:
                        return {
                            'is_playlist': False,
                            'title': search_item['title'],
                            'uploader': search_item['uploader'],
                            'thumbnail': search_item['thumbnail'],
                            'total_items': 1,
                            'items': [search_item]
                        }
            raise last_error

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

    def _extract_instagram_info(self, url: str, user_cookies: str = None):
        ydl_opts = get_default_ydl_opts(user_cookies=user_cookies)
        ydl_opts.update({'skip_download': True})
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        if not info:
            raise ValueError("Could not fetch Instagram details.")

        is_playlist = 'entries' in info and info['entries'] is not None
        items = []
        if is_playlist:
            title = info.get('title') or info.get('description') or 'Instagram Post'
            uploader = info.get('uploader') or info.get('uploader_id') or 'Instagram'
            thumbnail = info.get('thumbnail') or ''
            for idx, entry in enumerate(info['entries']):
                if not entry:
                    continue
                v_id = entry.get('id') or f"ig_{idx}"
                v_url = entry.get('webpage_url') or entry.get('url') or url
                thumb = entry.get('thumbnail') or thumbnail
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
            thumbnail = info.get('thumbnail') or ''
            video_id = info.get('id') or 'instagram_item'
            items.append({
                'index': 1,
                'id': video_id,
                'title': title,
                'uploader': uploader,
                'duration': info.get('duration') or 0,
                'thumbnail': thumbnail,
                'url': info.get('webpage_url') or url
            })

        return {
            'is_playlist': is_playlist and len(items) > 1,
            'title': title,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'total_items': len(items),
            'items': items
        }

    def _search_youtube_track(self, query: str, index: int = 1, user_cookies: str = None):
        ydl_opts = get_default_ydl_opts(user_cookies=user_cookies)
        ydl_opts.update({
            'extract_flat': True,
            'skip_download': True,
        })
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
            print(f"Error searching YouTube: {e}")
        return None

    def _extract_spotify_info(self, url: str, user_cookies: str = None):
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
            
            yt_item = self._search_youtube_track(title, user_cookies=user_cookies)
            if yt_item:
                yt_item['title'] = title
                if thumbnail:
                    yt_item['thumbnail'] = thumbnail
                items = [yt_item]
            else:
                raise ValueError(f"Could not find video for Spotify track '{title}'.")

            return {
                'is_playlist': False,
                'title': title,
                'uploader': 'Spotify',
                'thumbnail': thumbnail or yt_item['thumbnail'],
                'total_items': 1,
                'items': items
            }
        else:
            raise ValueError("Spotify playlists require API token configuration or direct track links.")
