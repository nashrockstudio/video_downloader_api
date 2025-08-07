# routers/youtube_router.py
from fastapi import APIRouter, HTTPException
import yt_dlp
import logging
from typing import List, Dict, Optional

router = APIRouter()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sanitize_youtube_url(url: str) -> str:
    """Clean YouTube URL by removing tracking parameters"""
    if "youtu.be/" in url:
        return url.split('?')[0]
    elif "youtube.com/watch" in url:
        return url.split('&')[0]
    return url

def get_best_mp3(formats: List[Dict]) -> Optional[Dict]:
    """Find the highest quality MP3 audio format"""
    audio_formats = [f for f in formats 
                    if f.get('acodec') != 'none' 
                    and f.get('vcodec') == 'none'
                    and f.get('ext') == 'mp3']
    return max(audio_formats, key=lambda x: x.get('abr', 0)) if audio_formats else None

def get_all_video_formats(formats: List[Dict]) -> List[Dict]:
    """Get all unique video formats with audio"""
    seen = set()
    unique_formats = []
    for f in sorted(formats, key=lambda x: x.get('height', 0), reverse=True):
        if (f.get('vcodec') != 'none' 
            and f.get('acodec') != 'none'
            and f.get('height') not in seen):
            seen.add(f.get('height'))
            unique_formats.append(f)
    return unique_formats

@router.get("/download")
async def download_youtube(url: str):
    """Get YouTube video with all formats"""
    try:
        # Clean and validate URL
        clean_url = sanitize_youtube_url(url)
        if not any(x in clean_url for x in ["youtube.com/", "youtu.be/"]):
            raise HTTPException(status_code=400, detail="Invalid YouTube URL")

        # Configure yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        # Extract video info
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(clean_url, download=False)
                if not info:
                    raise HTTPException(status_code=404, detail="Video not found")
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Private video" in error_msg:
                raise HTTPException(status_code=403, detail="Private video - Login required")
            if "Video unavailable" in error_msg:
                raise HTTPException(status_code=404, detail="Video unavailable")
            raise HTTPException(status_code=400, detail=error_msg)

        # Prepare response
        response = {
            "title": info.get('title', 'YouTube Video'),
            "thumbnail": info.get('thumbnail'),
            "duration": info.get('duration'),
            "formats": {
                "audio": None,
                "videos": []
            }
        }

        formats = info.get('formats', [])
        
        # 1. Get best MP3 audio
        best_mp3 = get_best_mp3(formats)
        if best_mp3:
            response['formats']['audio'] = {
                "url": best_mp3['url'],
                "format": "mp3",
                "bitrate": f"{best_mp3.get('abr', 0)}kbps"
            }

        # 2. Get all video formats with audio
        video_formats = get_all_video_formats(formats)
        for fmt in video_formats:
            response['formats']['videos'].append({
                "url": fmt['url'],
                "quality": f"{fmt.get('height', 0)}p",
                "format": fmt.get('ext', 'mp4'),
                "fps": fmt.get('fps', 30)
            })

        if not response['formats']['audio'] and not response['formats']['videos']:
            raise HTTPException(status_code=404, detail="No playable formats found")

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process video")