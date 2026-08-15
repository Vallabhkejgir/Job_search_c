import os
import subprocess
import sys

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from dashboard_db import (
    get_all_messaged_users,
    get_all_processed_jobs,
    get_job_count,
    get_messaged_users_count,
)
from database import init_db

app = FastAPI(title="LinkedIn Referral Agent Dashboard")


@app.on_event("startup")
def startup_event():
    init_db()


@app.on_event("shutdown")
def shutdown_event():
    if AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None:
        AGENT_PROCESS.terminate()
        AGENT_PROCESS.wait()


# Ensure templates directory exists
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")

# Global state to track background process
AGENT_PROCESS = None


def is_agent_running():
    if AGENT_PROCESS is not None and AGENT_PROCESS.poll() is None:
        return True
    if os.path.exists("agent.lock"):
        try:
            with open("agent.lock", "r") as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)
            return True
        except (ValueError, OSError):
            return False
    return False


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    jobs = get_all_processed_jobs()
    users = get_all_messaged_users()

    total_jobs = get_job_count()
    total_users = get_messaged_users_count()

    is_running = is_agent_running()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "jobs": jobs,
            "users": users,
            "total_jobs": total_jobs,
            "total_users": total_users,
            "is_running": is_running,
        },
    )


@app.post("/api/run")
async def run_agent():
    global AGENT_PROCESS

    # Check if already running
    if is_agent_running():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Agent is already running."},
        )

    try:
        # Launch main.py as a background process using the current venv python
        python_executable = sys.executable
        AGENT_PROCESS = subprocess.Popen(  # noqa: ASYNC220
            [python_executable, "main.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return {
            "status": "success",
            "message": "Agent started successfully in the background.",
        }
    except Exception as e:  # noqa: BLE001
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@app.get("/api/status")
async def check_status():
    return {"is_running": is_agent_running()}
