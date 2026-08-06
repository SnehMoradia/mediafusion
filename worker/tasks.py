import os
import json
import redis
from celery import Celery
import yt_dlp
from backend.app.services.downloader import get_default_ydl_opts, FFMPEG_PATH

REDIS_URL = os.environ.get('REDIS_URL', 'redis://redis:6379/0')

celery_app = Celery('tasks', broker=REDIS_URL, backend=REDIS_URL)
redis_client = redis.Redis.from_url(REDIS_URL)

@celery_app.task(bind=True)
def download_media_item(self, job_id: str, video_id: str, video_url: str, format_type: str, quality: str, output_dir: str, cookies: str = None):
    def progress_hook(d):
        status = d.get('status')
        progress_data = {
            'job_id': job_id,
            'video_id': video_id,
            'status': status,
        }
        if status == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            downloaded = d.get('downloaded_bytes') or 0
            progress_data['downloaded_bytes'] = downloaded
            progress_data['total_bytes'] = total
            if total > 0:
                progress_data['progress'] = round((downloaded / total) * 100, 1)
            progress_data['speed'] = d.get('speed')
            progress_data['eta'] = d.get('eta')
        elif status == 'finished':
            progress_data['status'] = 'converting'
            progress_data['progress'] = 99.9

        redis_client.publish(f"job:{job_id}", json.dumps(progress_data))

    opts = get_default_ydl_opts(user_cookies=cookies)
    out_tmpl = os.path.join(output_dir, '%(title)s [%(id)s].%(ext)s')
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
        if quality == '1080p':
            opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
        elif quality == '720p':
            opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]/best'
        else:
            opts['format'] = 'bestvideo+bestaudio/best'
        opts['merge_output_format'] = 'mp4'

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([video_url])

    redis_client.publish(f"job:{job_id}", json.dumps({'job_id': job_id, 'video_id': video_id, 'status': 'completed', 'progress': 100}))
    return True
