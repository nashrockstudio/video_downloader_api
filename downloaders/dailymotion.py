from fastapi import APIRouter, Query
from pydantic import BaseModel
import yt_dlp
import requests

router = APIRouter()

class Format(BaseModel):
    quality: str
    file_size: str
    download_url: str

class DownloadResponse(BaseModel):
    title: str
    thumbnail: str
    formats: list[Format]

def get_file_size(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=10)
        size = int(response.headers.get("Content-Length", 0))
        return round(size / (1024 * 1024), 2)  # MB
    except:
        return 0.0

@router.get("/download/dailymotion", response_model=DownloadResponse)
async def download_dailymotion(url: str = Query(..., description="Dailymotion video URL")):
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "forcejson": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception:
            return {
                "title": "Unavailable",
                "thumbnail": "",
                "formats": [{
                    "quality": "Unavailable",
                    "file_size": "0 MB",
                    "download_url": "No valid direct download link found"
                }]
            }

    formats = []
    for fmt in info.get("formats", []):
        if not fmt.get("url") or fmt.get("vcodec") == "none":
            continue

        quality = fmt.get("format_note") or fmt.get("height", "Unknown")
        size = fmt.get("filesize")
        if not size:
            size = get_file_size(fmt["url"])

        formats.append({
            "quality": f"{quality}p" if isinstance(quality, int) else quality,
            "file_size": f"{round(size / (1024 * 1024), 2)} MB" if size else "0.0 MB",
            "download_url": fmt["url"]
        })

    return {
        "title": info.get("title", "No Title"),
        "thumbnail": info.get("thumbnail", ""),
        "formats": formats
    }