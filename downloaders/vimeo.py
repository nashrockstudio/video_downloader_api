from fastapi import APIRouter, Query
import yt_dlp
import requests

router = APIRouter()

@router.get("/download/vimeo")
def download_vimeo(url: str = Query(...)):
    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'forcejson': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            formats = []
            for f in info.get("formats", []):
                # ✅ Skip if no URL or only audio
                if not f.get("url"):
                    continue

                if f.get("vcodec") != "none" and f.get("acodec") != "none" and f.get("protocol") == "https":
                    label = f.get("format_note") or f.get("height", "Unknown")
                    if isinstance(label, int):
                        label = f"{label}p"

                    # 🔍 Try file size
                    file_size_bytes = f.get("filesize")
                    if not file_size_bytes:
                        try:
                            head = requests.head(f["url"], timeout=10, allow_redirects=True)
                            file_size_bytes = int(head.headers.get("Content-Length", 0))
                        except:
                            file_size_bytes = 0

                    file_size = f"{round(file_size_bytes / (1024 * 1024), 2)} MB" if file_size_bytes else "0.0 MB"

                    formats.append({
                        "quality": label,
                        "file_size": file_size,
                        "download_url": f["url"]
                    })

            return {
                "title": info.get("title", "download"),
                "thumbnail": info.get("thumbnail"),
                "formats": formats if formats else [{
                    "quality": "Unavailable",
                    "file_size": "-",
                    "download_url": "No valid video format found"
                }]
            }

    except Exception as e:
        return {
            "title": "download",
            "thumbnail": None,
            "formats": [{
                "quality": "Unavailable",
                "file_size": "-",
                "download_url": "Error occurred"
            }],
            "error": str(e)
        }