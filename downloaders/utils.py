import yt_dlp
import requests

def format_bytes(size):
    if not size:
        return "N/A"
    size_kb = size / 1024
    return f"{round(size_kb / 1024, 2)} MB" if size_kb >= 1024 else f"{round(size_kb, 2)} KB"

def get_file_size_from_url(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0',
        }
        r = requests.head(url, allow_redirects=True, timeout=10, headers=headers)
        if "Content-Length" in r.headers:
            return format_bytes(int(r.headers["Content-Length"]))
    except:
        pass
    return "N/A"

def extract_video_info(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'forcejson': True,
        'cookiefile': 'cookies.txt',
        'merge_output_format': 'mp4',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                if "There is no video in this post" in str(e):
                    info = {"error": "ImageOnly", "raw_url": url}
                else:
                    return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}

    title = info.get("title", "Instagram Post")
    thumbnail = info.get("thumbnail")
    formats = []

    # ✅ VIDEO + AUDIO formats
    for f in info.get("formats", []):
        if f.get("acodec") != "none" and (f.get("vcodec") != "none" or f.get("ext") in ("m3u8", "mpd")):
            height = f.get("height")
            quality = f"{height}p" if height else f.get("format_id")
            url_f = f.get("url")
            size = format_bytes(f.get("filesize")) if f.get("filesize") else get_file_size_from_url(url_f)
            formats.append({
                "quality": quality,
                "file_size": size,
                "download_url": url_f
            })

    # ✅ AUDIO ONLY (MP3 fallback)
    for f in info.get("formats", []):
        if f.get("vcodec") == "none" and f.get("acodec") != "none":
            size = format_bytes(f.get("filesize")) if f.get("filesize") else get_file_size_from_url(f.get("url"))
            formats.append({
                "quality": "MP3 Audio",
                "file_size": size,
                "download_url": f.get("url")
            })
            break

    # ✅ FINAL FALLBACK: Try to extract image-only content
    if not formats:
        image_url = None

        if info.get("error") == "ImageOnly":
            image_url = info.get("raw_url")
        elif not thumbnail or thumbnail == "null":
            image_url = (
                info.get("display_url") or
                (info.get("thumbnails", [{}])[-1].get("url") if info.get("thumbnails") else None)
            )
        if not image_url and thumbnail:
            image_url = thumbnail

        if image_url:
            size = get_file_size_from_url(image_url)
            formats.append({
                "quality": "Image",
                "file_size": size,
                "download_url": image_url
            })
            thumbnail = image_url

    return {
        "title": title,
        "thumbnail": thumbnail,
        "formats": formats
    }