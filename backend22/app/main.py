from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.routers import msmes, export
import os

app = FastAPI(title="KEPSA CircularMap API", version="0.1.0")

# Wide-open CORS for the demo. Tighten to the deployed frontend origin in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(msmes.router)
app.include_router(export.router)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Serve the frontend - must be after API routes
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend")
frontend_dir = os.path.normpath(frontend_dir)

if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_index():
        with open(os.path.join(frontend_dir, "index.html"), "r", encoding="utf-8") as f:
            return f.read()
