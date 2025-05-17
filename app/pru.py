import os
from fastapi.responses import (HTMLResponse,
                               RedirectResponse,
                               JSONResponse,
                               Response,
                               StreamingResponse)
from fastapi import (FastAPI, Request, status)


class ResourceLockedError(Exception):
    pass

try:
    status_code = 423  # Example scenario
    if status_code == 423:
        raise ResourceLockedError("The resource is locked and cannot be accessed.")
except ResourceLockedError as e:
    print(e)