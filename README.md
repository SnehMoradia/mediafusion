# MediaFusion - Universal Media & Playlist Downloader

A fast, responsive web application for downloading YouTube playlists, single videos, audio tracks, and media with local and cloud support.

---

## 🚀 Features

- **Multi-Platform Support**: YouTube Playlists, Individual Videos, Audio extraction (MP3 / Best Quality).
- **Direct Browser Streaming & Local Folder Downloads**: Stream and download media directly in the browser or save to your local folder.
- **YouTube Authentication**: Automatic cookie file detection (`cookies.txt`) in the project root to handle age-restricted videos and bot checks.
- **Modern Responsive UI**: Clean, glassmorphic dark theme with live download progress tracking.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, `yt-dlp`
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

---

## 💻 Getting Started

### 1. Clone & Setup Virtual Environment
```bash
git clone https://github.com/SnehMoradia/mediafusion.git
cd mediafusion

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the Application
```bash
# Windows quick-start:
run.bat

# Or run directly with Python:
python app.py
```
Open your browser at `http://127.0.0.1:5050`.

---
