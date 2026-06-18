from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI(title="YTDown Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    format: str
    quality: str = "best"

@app.get("/")
async def root():
    return {"status": "✅ Backend is running"}

@app.post("/fetch")
async def fetch_video(request: DownloadRequest):
    try:
        video_id = str(uuid.uuid4())[:8]
        
        ydl_opts = {
            'outtmpl': f"downloads/{video_id}_%(title)s.%(ext)s",
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
        }

        if request.format == "mp4":
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
        else:  # mp3
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(request.url, download=True)
            filename = ydl.prepare_filename(info)
            
            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "duration": info.get('duration_string', 'N/A'),
                "download_url": f"/download/{os.path.basename(filename)}"
            }

    except Exception as e:
        error = str(e)
        if "format is not available" in error.lower():
            error = "Requested quality not available. Try another quality."
        raise HTTPException(status_code=400, detail=error)
