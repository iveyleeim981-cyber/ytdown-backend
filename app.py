from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import yt_dlp
import os
import uuid

app = FastAPI(title="YTDown Backend")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DownloadRequest(BaseModel):
    url: str
    format: str      # "mp4" or "mp3"
    quality: str = "best"

@app.get("/")
async def root():
    return {"status": "✅ YTDown Backend is running"}

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
            'http_chunk_size': 10485760,
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
            file_path = os.path.basename(filename)

            return {
                "success": True,
                "title": info.get('title', 'Video'),
                "duration": info.get('duration_string', 'N/A'),
                "thumbnail": info.get('thumbnail'),
                "download_url": f"/download/{file_path}",
                "format": request.format
            }

    except Exception as e:
        error_msg = str(e)
        if "Requested format is not available" in error_msg:
            error_msg = "Format not available. Try a different quality or video."
        raise HTTPException(status_code=400, detail=error_msg)
