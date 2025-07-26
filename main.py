from fastapi import FastAPI
from downloaders import instagram, facebook, twitter, vimeo, youtube, dailymotion, tubidy, linkedin, reddit # 👈 Facebook router bhi import karo

app = FastAPI()

# ✅ Include routers
app.include_router(instagram.router)
app.include_router(facebook.router)
app.include_router(twitter.router)
app.include_router(vimeo.router)
app.include_router(youtube.router)
app.include_router(dailymotion.router)
app.include_router(tubidy.router)
app.include_router(linkedin.router)
app.include_router(reddit.router)


@app.get("/")
def home():
    return {"msg": "API is running"}