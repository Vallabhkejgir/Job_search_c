from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess
import os
import sys

from dashboard_db import get_all_processed_jobs, get_all_messaged_users

app = FastAPI(title="LinkedIn Referral Agent Dashboard")

# Ensure templates directory exists
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# Global state to track background process
AGENT_PROCESS = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jobs = get_all_processed_jobs()
    users = get_all_messaged_users()

    is_running = AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "jobs": jobs,
            "users": users,
            "is_running": is_running
        }
    )

@app.post("/api/run")
async def run_agent():
    global AGENT_PROCESS

    # Check if already running
    if AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Agent is already running."})

    try:
        # Launch main.py as a background process using the current venv python
        python_executable = sys.executable
        AGENT_PROCESS = subprocess.Popen([python_executable, "main.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {"status": "success", "message": "Agent started successfully in the background."}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@app.get("/api/status")
async def check_status():
    is_running = AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None
    return {"is_running": is_running}