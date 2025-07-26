from fastapi import APIRouter, Query
from downloaders.utils import extract_video_info

router = APIRouter()

@router.get("/download/instagram")
def download_instagram(url: str = Query(...)):
    try:
        return extract_video_info(url)
    except Exception as e:
        return {"error": str(e)}