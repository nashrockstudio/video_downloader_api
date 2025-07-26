from fastapi import APIRouter
from pydantic import HttpUrl
from fastapi.responses import JSONResponse
from downloaders.utils import extract_video_info

router = APIRouter()

@router.get("/download/youtube")
def download_youtube(url: HttpUrl):
    try:
        result = extract_video_info(str(url))
        return result
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)