# 🎵 MediaFusion - Universal Media Downloader

<p align="center">
  <img src="https://fav.farm/🎵" width="80" alt="MediaFusion Logo" />
</p>

<p align="center">
  <b>A fast, modern, multi-platform media downloader for YouTube, Instagram, and Spotify.</b><br>
  Download playlists, videos, reels, and audio tracks in high-definition MP4 video or 320kbps MP3 audio.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Flask-3.0%2B-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/yt--dlp-Latest-red?style=for-the-badge&logo=youtube&logoColor=white" alt="yt-dlp" />
  <img src="https://img.shields.io/badge/FFmpeg-Supported-green?style=for-the-badge&logo=ffmpeg&logoColor=white" alt="FFmpeg" />
  <img src="https://img.shields.io/badge/Vercel-Configured-black?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel" />
</p>

---

## ✨ Features

- 🎥 **YouTube Downloader**: Download entire Playlists, single videos, YouTube Shorts, or channels in HD MP4 (1080p, 720p, 480p, 360p) or high-bitrate MP3.
- 📸 **Instagram Reels & Posts**: Download Instagram Reels, Video posts, and IGTV clips directly.
- 🎧 **Spotify Tracks, Playlists & Albums**: Paste any Spotify URL to extract track metadata and download pristine audio tracks.
- 🎼 **True MP3 Audio Extraction**: Automatic conversion using bundled **FFmpeg** (`imageio-ffmpeg`) for crisp, real `.mp3` files (not `.webm`).
- ⚡ **Real-Time Progress & Speed**: Live download speed (MB/s), percent completed, ETA countdown, and batch progress tracking.
- 🎨 **Glassmorphism UI**: Premium dark mode design built with modern CSS, vibrant gradients, and smooth micro-animations.
- 📂 **Custom Download Folder**: Choose custom save directories or auto-save directly to your system's `Downloads` folder.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, Flask, Flask-CORS
- **Download Engine**: `yt-dlp`, `imageio-ffmpeg` (bundled FFmpeg binary)
- **Metadata Parsers**: `requests`, Spotify oEmbed API & Embed Parser
- **Frontend**: Vanilla HTML5, Modern CSS3 (Glassmorphism design system), JavaScript (Async/Await Fetch & Polling API)

---

## 🚀 Quick Start (Local Setup)

### Option 1: Automatic 1-Click Launch (Windows)

Simply double-click `run.bat` or execute in terminal:

```cmd
.\run.bat
```

> **What `run.bat` does:**
> 1. Automatically creates a Python virtual environment (`venv`) if needed.
> 2. Installs required dependencies from `requirements.txt`.
> 3. Launches your browser to `http://localhost:5050`.
> 4. Starts the local Flask server.

---

### Option 2: Manual Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SnehMoradia/mediafusion.git
   cd mediafusion
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate

   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Flask application**:
   ```bash
   python app.py
   ```

5. Open [http://localhost:5050](http://localhost:5050) in your browser.

---

## 📂 Project Structure

```
playlistdownloader/
├── app.py                  # Main Flask application & API routes
├── downloader.py           # Multi-platform extraction & background download engine
├── requirements.txt        # Python dependencies
├── run.bat                 # Windows automatic launcher script
├── vercel.json             # Vercel Serverless deployment configuration
├── render.yaml             # Render 1-click cloud deployment manifest
├── .gitignore              # Git ignore rules
├── api/
│   └── index.py            # Vercel Serverless function entrypoint
├── static/
│   ├── css/
│   │   └── style.css       # Complete UI design system & Glassmorphism styles
│   └── js/
│       └── app.js          # Interactive frontend logic & progress tracking
└── templates/
    └── index.html          # Web application UI template
```

---

## ☁️ Deployment Guide

### Deploying to Vercel

1. Push your repository to GitHub.
2. Log into [Vercel](https://vercel.com/) and click **Add New Project**.
3. Import your `SnehMoradia/mediafusion` GitHub repository.
4. Vercel automatically detects `vercel.json` and builds the `@vercel/python` function.
5. Click **Deploy**!

### Deploying to Render / Railway / Koyeb

For long-running batch video downloads without serverless timeouts:
1. Connect your repository to **[Render.com](https://render.com/)**.
2. Render automatically reads `render.yaml` and deploys using `gunicorn app:app`.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<p align="center">
  Created with ❤️ by <b><a href="https://github.com/SnehMoradia">Sneh Moradia</a></b>
</p>
