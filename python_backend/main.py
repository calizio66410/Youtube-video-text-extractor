import os
import uuid
import asyncio
import shutil
from fastapi import FastAPI, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.pipeline import ExtractionPipeline

app = FastAPI(title="Video Text Extractor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("templates", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# In-memory storage for jobs status and websocket connections
jobs = {}
active_connections = {}

class ExtractRequest(BaseModel):
    url: str
    lang: str = "fra+eng"
    interval: float = 2.0
    fast_mode: bool = False

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/extract")
async def extract_text(req: ExtractRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "initialized",
        "progress": 0,
        "message": "Initializing...",
        "result": None,
        "error": None
    }
    
    pipeline = ExtractionPipeline(job_id, req.url, req.lang, req.interval, req.fast_mode)
    jobs[job_id]['pipeline'] = pipeline

    background_tasks.add_task(run_pipeline_background, job_id, pipeline)
    return {"job_id": job_id, "status": "started"}

async def run_pipeline_background(job_id: str, pipeline: ExtractionPipeline):
    try:
        jobs[job_id]["status"] = "processing"
        
        async def progress_callback(progress_data):
            jobs[job_id].update(progress_data)
            if job_id in active_connections:
                try:
                    await active_connections[job_id].send_json(progress_data)
                except:
                    pass
                    
        result = await pipeline.run(progress_callback)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["message"] = "Extraction finished successfully."
        jobs[job_id]["result"] = result
        
        if job_id in active_connections:
            await active_connections[job_id].send_json({
                "status": "completed",
                "progress": 100,
                "message": "Extraction finished successfully.",
                "result": result
            })
    except Exception as e:
        error_msg = str(e)
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = error_msg
        jobs[job_id]["message"] = f"Error: {error_msg}"
        if job_id in active_connections:
            try:
                await active_connections[job_id].send_json({
                    "status": "failed",
                    "error": error_msg,
                    "message": f"Error: {error_msg}"
                })
            except:
                pass

@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        return {"status": "not_found", "error": "Job ID not found"}
    response_data = {k: v for k, v in jobs[job_id].items() if k != 'pipeline'}
    return response_data

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await websocket.accept()
    active_connections[job_id] = websocket
    
    if job_id in jobs:
        current_status = {k: v for k, v in jobs[job_id].items() if k != 'pipeline'}
        await websocket.send_json(current_status)
        
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        if job_id in active_connections:
            del active_connections[job_id]
