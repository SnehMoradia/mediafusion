# MediaFusion - Universal Media & Playlist Downloader

A fast, responsive web application for downloading YouTube playlists, single videos, audio tracks, and media. Deployed seamlessly to Vercel with local development support.

---

## 🚀 Features

- **Multi-Platform Support**: YouTube Playlists, Individual Videos, Audio extraction (MP3 / Best Quality).
- **Direct Browser Streaming**: Stream and download media directly in the browser on Vercel without local storage limits.
- **YouTube Bot Bypass**: Built-in cookie management and authentication support (`cookies.txt` and custom cookie injection) to bypass cloud datacenter IP blocks.
- **Modern Responsive UI**: Clean, glassmorphic dark theme with live download progress tracking.

---

## 🛠️ Tech Stack

- **Backend**: Python, Flask, `yt-dlp`
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: Vercel Serverless Functions (`vercel.json`, `api/index.py`)

---

## 💻 Local Development Setup

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

## ☁️ Vercel Deployment

1. Import your GitHub repository into [Vercel](https://vercel.com).
2. Set any optional environment variables in Vercel settings (e.g. `YOUTUBE_COOKIES`).
3. Deploy! Vercel will automatically configure the routing via `vercel.json` and `api/index.py`.

---

## 🔑 Custom Cookies Support
If YouTube presents bot check errors (*"Sign in to confirm you're not a bot"*), click the **Custom Cookies** button in the web interface and paste your exported Netscape-format `cookies.txt` or JSON cookies. Cookies are sent securely with your extraction and download requests.
