from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

from .indexer import load_index_json
from .routes import router

app = FastAPI(title="Markdown Knowledge Base Q&A Bot")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)

_CHAT_HTML = Path(__file__).resolve().parents[1] / "chat.html"

@app.get("/")
def serve_ui():
    return FileResponse(_CHAT_HTML)


@app.on_event("startup")
def load_persisted_index():
    load_index_json()
