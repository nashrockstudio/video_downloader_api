from fastapi import APIRouter, Query
from downloaders.utils import extract_video_info

router = APIRouter()

@router.get("/download/linkedin")
def download_linkedin(url: str = Query(...)):
    try:
        return extract_video_info(url)
    except Exception as e:
        return {"error": str(e)}