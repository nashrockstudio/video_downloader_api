from fastapi import APIRouter, Query
import yt_dlp
import math

router = APIRouter()

@router.get("/download/reddit")
def download_reddit(url: str = Query(...)):
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "force_generic_extractor": False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        formats = []
        for f in info.get("formats", []):
            # Only include formats that have BOTH video and audio
            if f.get("vcodec", "none") != "none" and f.get("acodec", "none") != "none":
                filesize = f.get("filesize") or f.get("filesize_approx") or 0
                size_mb = round(int(filesize) / 1048576, 2) if filesize else 0.0
                formats.append({
                    "quality": f.get("format_note") or f.get("height", "Unknown"),
                    "file_size": f"{size_mb} MB",
                    "download_url": f.get("url")
                })

        if not formats:
            return {
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "formats": [{
                    "quality": "Unavailable",
                    "file_size": "-",
                    "download_url": "No valid direct video+audio format found"
                }]
            }

        return {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "formats": formats
        }

    except Exception as e:
        return {
            "title": "Reddit Video",
            "thumbnail": None,
            "formats": [{
                "quality": "Unavailable",
                "file_size": "-",
                "download_url": "No valid direct download link found"
            }],
            "error": str(e)
        }