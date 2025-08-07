from fastapi import APIRouter, HTTPException
import yt_dlp
import requests
from bs4 import BeautifulSoup

router = APIRouter(prefix="/facebook", tags=["Facebook"])

# ✅ Convert bytes to readable format
def format_bytes(size):
    if not size:
        return "N/A"
    size_kb = size / 1024
    return f"{round(size_kb / 1024, 2)} MB" if size_kb >= 1024 else f"{round(size_kb, 2)} KB"

# ✅ Get file size from URL
def get_file_size_from_url(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
        if "Content-Length" in r.headers:
            return format_bytes(int(r.headers["Content-Length"]))
    except:
        pass
    return "N/A"

# ✅ If yt-dlp fails, fallback to image-only
def extract_image_from_html(fb_url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(fb_url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            og_img = soup.find("meta", property="og:image")
            if og_img and og_img.get("content"):
                return og_img["content"]
    except:
        pass
    return None

# ✅ Main extractor
def extract_facebook_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'forcejson': True,
        'format': 'bestvideo*+bestaudio/best',  # ✅ all formats including high quality
        'cookiefile': 'cookies.txt',            # ✅ needed for 1080p+ formats
    }

    info = None
    error_message = ""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        error_message = str(e)

    formats = []
    title = "Facebook Post"
    thumbnail = None
    has_video = False

    if info:
        title = info.get("title", title)
        thumbnail = info.get("thumbnail")

        for f in info.get("formats", []):
            if f.get("acodec") != "none" and (f.get("vcodec") != "none" or f.get("ext") in ("m3u8", "mpd")):
                has_video = True
                height = f.get("height")
                width = f.get("width")
                format_note = f.get("format_note")
                if height and width:
                    quality = f"{height}p ({width}x{height})"
                elif format_note:
                    quality = format_note
                else:
                    quality = f.get("format_id", "Unknown")

                url_f = f.get("url")
                size = format_bytes(f.get("filesize")) if f.get("filesize") else get_file_size_from_url(url_f)

                formats.append({
                    "quality": quality,
                    "file_size": size,
                    "download_url": url_f
                })

        # ✅ MP3 Audio format (if audio-only present)
        for f in info.get("formats", []):
            if f.get("vcodec") == "none" and f.get("acodec") != "none":
                url_f = f.get("url")
                size = format_bytes(f.get("filesize")) if f.get("filesize") else get_file_size_from_url(url_f)
                formats.append({
                    "quality": "MP3 Audio",
                    "file_size": size,
                    "download_url": url_f
                })
                break

        # ✅ Sort formats by quality (height)
        def extract_height(quality_str):
            if "p" in quality_str:
                try:
                    return int(quality_str.split("p")[0])
                except:
                    return 0
            return 0

        formats = sorted(formats, key=lambda x: extract_height(x["quality"]), reverse=True)

    # ✅ Fallback to image-only if no video/audio formats
    if not has_video and not formats:
        image_url = None

        if thumbnail and "yt-dlp/wiki/FAQ" not in thumbnail:
            image_url = thumbnail
        else:
            image_url = extract_image_from_html(url)

        if image_url:
            size = get_file_size_from_url(image_url)
            formats.append({
                "quality": "Image",
                "file_size": size,
                "download_url": image_url
            })
            thumbnail = image_url
        else:
            return {"error": "Image not found. It may be private or unsupported."}

    return {
        "title": title,
        "thumbnail": thumbnail,
        "formats": formats
    }

# ✅ FastAPI endpoint
@router.get("/download")
def download_facebook(url: str):
    if "facebook.com" not in url:
        raise HTTPException(status_code=400, detail="Invalid Facebook URL")

    result = extract_facebook_info(url)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result