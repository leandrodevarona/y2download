import os
from fastapi.responses import (HTMLResponse,
                               RedirectResponse,
                               JSONResponse,
                               Response,
                               StreamingResponse)
from fastapi import (FastAPI, Request, status)

dl_progress = {}

def handle_download(event_name):
    if event_name not in dl_progress:
        dl_progress[event_name] = 0  # Initialize progress

    while dl_progress[event_name] < 100:  # Simulating download progress
        dl_progress[event_name] += 10  # Increment progress (Adjust based on actual logic)

    print(f"\ndl_progress = {dl_progress}")

handle_download('event_name')