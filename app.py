import os
import sys
import subprocess
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from downloader import DownloadManager

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

dm = DownloadManager()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/default-folder', methods=['GET'])
def get_default_folder():
    default_dir = os.path.join(os.path.expanduser('~'), 'Downloads', 'PlaylistDownloads')
    return jsonify({'path': default_dir})

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
        return jsonify({'error': str(e)}), 500

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5050))
    print(f"\n========================================================")
    print(f" Playlist Downloader running at http://localhost:{port}")
    print(f"========================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
