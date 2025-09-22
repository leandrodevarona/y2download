import os
import time
from fastapi import (FastAPI, Request, status)
from fastapi.responses import (HTMLResponse,
                               RedirectResponse,
                               JSONResponse,
                               Response,
                               StreamingResponse)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from numerize import numerize

from app.services.yt_dlp import (download_video,
                                 download_audio,
                                 validate,
                                 get_file_info,
                                 get_download_video_options,
                                 get_download_audio_options,
                                 progress_generator,
                                 delete_progress
                                 )
from app.services import metadata

from fastapi.middleware.cors import CORSMiddleware
from app.utils.strings import (remove_trailing_spaces,
                              remove_leading_spaces)
                              

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any source
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

app.mount("/static", StaticFiles(directory="static"), name = 'static')

templates = Jinja2Templates(directory="app/templates")

@app.get('/', response_class=HTMLResponse)
def home_view(request: Request):
    meta = metadata.get_metadata()

    likes = numerize.numerize(meta.likes)
    dislikes = numerize.numerize(meta.dislikes)

    return templates.TemplateResponse(
        request=request, 
        name = 'home.html',
        context={
            "likes": likes,
            "dislikes": dislikes,
        }
    )

@app.get('/download-options/', response_class=HTMLResponse)
async def download_options(request: Request, url: str):
    is_valid_url = validate(url)

    if not is_valid_url:
        return RedirectResponse(f'{request.base_url}error_invalid_url')
    else:

        fullname, formats, thumbnail = get_file_info(url)

        fullname = remove_trailing_spaces(fullname)

        video_options = [] 

        audio_options = [] 

        video_options = get_download_video_options(formats, url, request.base_url, fullname)
        
        audio_options = get_download_audio_options(formats, url, request.base_url, fullname)
        
        return templates.TemplateResponse(
            request = request,
            name = 'download_options.html',
            context={
                'fullname': fullname,
                'video_options': video_options,
                'audio_options': audio_options,
                'thumbnail': thumbnail,
            }
        )


@app.get('/download_video/', response_class=RedirectResponse | JSONResponse)
def download_video_file(request: Request,
                   url: str,
                   fullname: str,
                   format_id: str,
                   resolution: str,
                   event_name: str
                   ):
    
    fullname = remove_trailing_spaces(fullname)

    format_id = remove_leading_spaces(format_id)

    file_path = download_video(url, format_id, fullname, resolution, event_name)

    if file_path == 'error_invalid_url':
        return RedirectResponse(f'{request.base_url}{file_path}')
    
    if file_path is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse({'file_path': file_path}, status_code=status.HTTP_200_OK)


@app.get('/download_audio/', response_class=RedirectResponse | JSONResponse)
def download_audio_file(request: Request,
                   url: str,
                   fullname: str,
                   format_id: str,
                   quality: str,
                   event_name: str
                   ):
    
    fullname = remove_trailing_spaces(fullname)

    format_id = remove_leading_spaces(format_id)

    file_path = download_audio(url, format_id, fullname, quality, event_name) 

    if file_path == 'error_invalid_url':
        return RedirectResponse(f'{request.base_url}{file_path}')
    
    if file_path is None:
        return Response(status_code=status.HTTP_404_NOT_FOUND)

    return JSONResponse({'file_path': file_path}, status_code=status.HTTP_200_OK)


class ResourceLockedError(Exception):
    pass
class UnknownError(Exception):
    pass
@app.delete('/delete-file', response_class=Response) #(CANBIO POR FIN SOLUCION AL METODO delete)
async def delete_file(request: Request, file_path: str, event_name: str):
    # Deletes a file, waiting if it's being used by another process.
    max_retries = 10  # Number of times to check if the file is free
    wait_time = 2  # Seconds to wait between retries

    delete_progress(event_name)

    for lap in range(max_retries):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully\n")
            return Response(status_code=status.HTTP_200_OK)
        except PermissionError:
            print(f"Waiting for '{file_path}' to be unlocked. Lap {lap}\n")
            # unlock_file(file_path)
            time.sleep(wait_time)  # Wait and retry
        except FileNotFoundError:
            # Raise HTTPException(status_code=404, detail="File not found")
            print("File not found. Could be already removed\n")
            return Response(status_code=status.HTTP_404_NOT_FOUND)
        except ResourceLockedError as e:
            print("The resource is locked and cannot be accessed {e}\n")
            return Response(status_code=status.HTTP_423_LOCKED)
    
    # raise UnknownError(status_code=409, detail="Conflict: File could not be deleted")


@app.get('/get-progress')
async def get_progress(event_name: str):
    return StreamingResponse(progress_generator(event_name), media_type="text/event-stream")


@app.get('/error_invalid_url')
def error_invalid_url(request: Request):
    return templates.TemplateResponse(
        request=request, name="error_invalid_url.html")


@app.put('/metadata/like')
def like():
    likes = metadata.like()
    likes = numerize.numerize(likes)

    return JSONResponse({'likes': likes}, status_code=status.HTTP_200_OK)

@app.put('/metadata/dislike')
def dislike():
    dislikes = metadata.dislike()
    dislikes = numerize.numerize(dislikes)
    
    return JSONResponse({'dislikes': dislikes}, status_code=status.HTTP_200_OK)