from fastapi import APIRouter, Query, HTTPException
import yt_dlp

router = APIRouter()

@router.get("/download")
async def download_dailymotion(
    url: str = Query(..., description="Dailymotion URL (e.g., https://www.dailymotion.com/video/x8xxxxx)")
):
    try:
        # 1. STRICT Dailymotion URL validation
        if not ("dailymotion.com/video/" in url or "dai.ly/" in url):
            raise HTTPException(status_code=400, detail="URL must be from Dailymotion (e.g., https://www.dailymotion.com/video/x8xxxxx)")

        # 2. Configure yt-dlp to ONLY accept Dailymotion
        ydl_opts = {
            "quiet": True,
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
            "force_generic_extractor": False,  # Important!
            "allowed_extractors": ["dailymotion"],  # Only allow Dailymotion
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.dailymotion.com",
            },
        }

        # 3. Extract info with strict Dailymotion check
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Additional check to confirm it's Dailymotion
            if "dailymotion.com" not in info.get("webpage_url", "") and "dai.ly" not in info.get("webpage_url", ""):
                raise HTTPException(status_code=400, detail="This is not a valid Dailymotion video")

        # ... [rest of your code: format filtering, etc.] ...

    except yt_dlp.utils.DownloadError as e:
        if "Unsupported URL" in str(e):
            raise HTTPException(status_code=400, detail="This URL is not supported (must be Dailymotion)")
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")