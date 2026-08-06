import os
import asyncio
import json
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.services.downloader import MediaDownloader, get_default_ydl_opts

app = FastAPI(
    title="MediaFusion API",
    description="Production-ready REST & WebSocket API for playlist downloader",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

downloader = MediaDownloader()

# Connection manager for WebSockets
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, job_id: str, websocket: WebSocket):
        await websocket.accept()
        if job_id not in self.active_connections:
            self.active_connections[job_id] = []
        self.active_connections[job_id].append(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket):
        if job_id in self.active_connections:
            if websocket in self.active_connections[job_id]:
                self.active_connections[job_id].remove(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]

    async def broadcast(self, job_id: str, message: dict):
        if job_id in self.active_connections:
            for connection in self.active_connections[job_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

# Data models
class ExtractRequest(BaseModel):
    url: str
    cookies: Optional[str] = None

class DownloadItem(BaseModel):
    id: str
    url: str
    title: str

class DownloadStartRequest(BaseModel):
    items: List[DownloadItem]
    format: str = "video"
    quality: str = "best"
    output_dir: Optional[str] = None
    cookies: Optional[str] = None

# Routes
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "MediaFusion API v2"}

@app.post("/api/extract")
def extract_media(req: ExtractRequest):
    if not req.url or not req.url.strip():
        raise HTTPException(status_code=400, detail="URL cannot be empty")
    try:
        data = downloader.extract_info(req.url.strip(), user_cookies=req.cookies)
        return {"success": True, "data": data}
    except Exception as e:
        clean_err = str(e)
        if "Sign in to confirm you're not a bot" in clean_err:
            clean_err = "YouTube bot check triggered. Please provide a cookies.txt string or run on localhost."
        return {"success": False, "error": clean_err}

@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
