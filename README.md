# MediaFusion - Production Media & Playlist Downloader

A modern, scalable, full-stack application for downloading YouTube playlists, Spotify tracks, and Instagram reels.

## 🚀 Architecture Overview

- **Frontend**: Next.js 14, React 18, Tailwind CSS (Responsive dark glassmorphic UI)
- **Backend**: FastAPI (Python 3.11), REST API & WebSockets
- **Downloader Core**: `yt-dlp` with automated player client fallback strategies
- **Async Queue**: Celery worker powered by Redis
- **Reverse Proxy**: Nginx
- **Orchestration**: Docker & Docker Compose

---

## 🛠️ Quick Start (Docker Compose)

### Prerequisites
- Docker Engine & Docker Compose installed on your host machine / VPS.

### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/SnehMoradia/mediafusion.git
   cd mediafusion
   ```

2. Launch all services:
   ```bash
   docker-compose up -d --build
   ```

3. Open your browser and navigate to:
   - **App Interface**: `http://localhost` (or `http://your-vps-ip`)
   - **Backend API Docs**: `http://localhost/api/docs`

---

## 💻 Local Development (Without Docker)

### Backend Setup
1. Navigate to `backend`:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. Start FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup
1. Navigate to `frontend`:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
2. Open `http://localhost:3000` in your browser.

---

## 🔑 Custom Cookies Support
If YouTube presents bot check errors ("Sign in to confirm you're not a bot"), click the **Custom Cookies** button in the top right header of the web interface and paste your exported `cookies.txt` content. Custom cookies are securely passed with your download request to bypass datacenter IP restrictions.
