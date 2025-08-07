from fastapi import APIRouter, HTTPException
import yt_dlp
import requests
import os
import logging
from bs4 import BeautifulSoup
from urllib.parse import urlparse

router = APIRouter(
    prefix="/instagram",
    tags=["Instagram Downloader"]
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔹 Size formatting helper
def format_bytes(size):
    if not size:
        return "N/A"
    size_kb = size / 1024
    return f"{round(size_kb / 1024, 2)} MB" if size_kb >= 1024 else f"{round(size_kb, 2)} KB"

# 🔹 File size via HEAD request
def get_file_size_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
        if "Content-Length" in r.headers:
            return format_bytes(int(r.headers["Content-Length"]))
    except:
        pass
    return "Unknown"

# 🔹 Format from URL path
def get_file_format(url):
    try:
        parsed = urlparse(url)
        path = parsed.path
        if '.' in path:
            return path.split('.')[-1].lower()
    except:
        pass
    return "unknown"

# 🔹 BeautifulSoup to extract full image (uncropped)
def extract_full_image_url(insta_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(insta_url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                return og_img["content"]
    except Exception as e:
        logger.warning(f"Image extraction failed: {e}")
    return None

# 🔹 Main Endpoint
@router.get("/download")
async def download_instagram(url: str):
    if not url.startswith(('https://www.instagram.com/', 'http://www.instagram.com/')):
        raise HTTPException(status_code=400, detail="Invalid Instagram URL")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'cookiefile': 'cookies.txt' if os.path.exists('cookies.txt') else None,
        'forcejson': True,
        'skip_download': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # ✅ Handle Video Post
        if info.get("formats"):
            results = {
                'type': 'video',
                'title': info.get('title', 'Instagram Video'),
                'thumbnail': info.get('thumbnail'),
                'formats': []
            }

            # Best video+audio
            video_with_audio = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            if video_with_audio:
                best = max(video_with_audio, key=lambda x: x.get("height", 0))
                url_v = best.get("url")
                results['formats'].append({
                    "quality": f"{best.get('height', '')}p (with audio)",
                    "url": url_v,
                    "size": get_file_size_from_url(url_v),
                    "format": get_file_format(url_v),
                    "type": "video+audio"
                })

            # Audio only
            audio_only = [f for f in info['formats'] if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            if audio_only:
                best_audio = max(audio_only, key=lambda x: x.get("abr", 0))
                url_a = best_audio.get("url")
                results['formats'].append({
                    "quality": f"Audio ({best_audio.get('abr', 0)}kbps)",
                    "url": url_a,
                    "size": get_file_size_from_url(url_a),
                    "format": get_file_format(url_a),
                    "type": "audio"
                })

            return results

        # ✅ Handle Image Post (fallback if no formats)
        image_url = extract_full_image_url(url)
        if image_url:
            return {
                "type": "image",
                "title": info.get("title", "Instagram Image"),
                "thumbnail": image_url,
                "formats": [
                    {
                        "quality": "Original Image",
                        "file_size": get_file_size_from_url(image_url),
                        "download_url": image_url,
                        "format": get_file_format(image_url),
                        "type": "image"
                    }
                ]
            }

        raise HTTPException(status_code=404, detail="Image not found (maybe private or unsupported).")

    except yt_dlp.utils.DownloadError as e:
        logger.warning(f"yt-dlp failed: {e}")
        image_url = extract_full_image_url(url)
        if image_url:
            return {
                "type": "image",
                "title": "Instagram Image",
                "thumbnail": image_url,
                "formats": [
                    {
                        "quality": "Original Image",
                        "file_size": get_file_size_from_url(image_url),
                        "download_url": image_url,
                        "format": get_file_format(image_url),
                        "type": "image"
                    }
                ]
            }
        raise HTTPException(status_code=500, detail="Image not found (maybe private or unsupported).")

    except Exception as e:
        logger.exception("Server error:")
        raise HTTPException(status_code=500, detail="Internal server error")