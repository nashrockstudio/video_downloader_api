from fastapi import APIRouter, Query
from .utils import extract_video_info

router = APIRouter(prefix="/download", tags=["Facebook"])

@router.get("/facebook")
def download_facebook(url: str = Query(..., description="Facebook video URL")):
    try:
        result = extract_video_info(url)
        return result
    except Exception as e:
        return {"error": str(e)}