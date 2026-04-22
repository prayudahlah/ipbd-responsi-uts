from fastapi import FastAPI
import os
import json

from fastapi.responses import RedirectResponse

app = FastAPI()

JSON_FILE = "./wired_articles_final.json"


def load_articles():
    if not os.path.exists(JSON_FILE):
        return []
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


articles = load_articles()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "API artikel wired.com berjalan dengan baik",
    }


@app.get("/")
async def root():
    return RedirectResponse(url="/health")


@app.get("/articles")
def get_all_articles():
    return articles
