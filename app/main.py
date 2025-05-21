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

from app.services.yt_dlp import (download_video,
                                 download_audio,
                                 validate,
                                 get_video_info,
                                 get_download_video_options,
                                 get_download_audio_options,
                                 progress_generator,
                                 delete_progress,
                                 unlock_file)
from fastapi.middleware.cors import CORSMiddleware
from app.utils.strings import (remove_trailing_spaces,
                              remove_leading_spaces)
from asyncio import sleep


app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite solicitudes desde cualquier origen
    allow_credentials=True,
    # Permite todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    allow_headers=["*"],  # Permite todos los encabezados
)

app.mount("/static", StaticFiles(directory="static"), name = 'static')

templates = Jinja2Templates(directory="app/templates")

@app.get('/', response_class=HTMLResponse)
def home_view(request: Request):
    return templates.TemplateResponse(
        request=request, name = 'home.html'
    )

@app.get('/download-options/', response_class=HTMLResponse)
async def download_options(request: Request, url: str):
    is_valid_url = validate(url)

    if not is_valid_url:
        return RedirectResponse(f'{request.base_url}error_invalid_url')
    else:

        fullname, formats, thumbnail = get_video_info(url)

        fullname = remove_trailing_spaces(fullname)

        video_options = [] #(CAMBIO)

        audio_options = [] #(CAMBIO)

        video_options = get_download_video_options(formats, url, request.base_url, fullname)
        
        audio_options = get_download_audio_options(formats, url, request.base_url, fullname)
        
        return templates.TemplateResponse(
            request = request,
            name = 'download_options.html',
            context={
                'fullname': fullname,
                'video_options': video_options,
                'audio_options': audio_options, #(CAMBIO)
                'thumbnail': thumbnail
            }
        )


@app.get('/download_video/', response_class=RedirectResponse | JSONResponse) #(CAMBIO OJO)
def download_video_file(request: Request,
                   url: str,
                   fullname: str,
                   format_id: str,
                   resolution: str):
    
    print(f'request.base_url===== {request.base_url}') #(CAMBIO)

    print(f'fullname without casting in download_video_file===== {fullname}***') #(CAMBIO)
    #Removing all whitespace characters from the right end of the string
    fullname = remove_trailing_spaces(fullname)
    print(f'fullname in download_video_file===== {fullname}***') #(CAMBIO)

    print(f'format_id without casting in download_video_file===== {format_id}') #(CAMBIO)
    #Removing all whitespace characters from the left end of the string
    format_id = remove_leading_spaces(format_id)
    print(f'format_id with casting in download_video_file===== {format_id}') #(CAMBIO)

    file_path = download_video(url, format_id, fullname, resolution)

    if file_path == 'error_invalid_url':
        return RedirectResponse(f'{request.base_url}{file_path}')

    return JSONResponse({'file_path': file_path}, status_code=200)


@app.get('/download_audio/', response_class=RedirectResponse | JSONResponse)
def download_audio_file(request: Request,
                   url: str,
                   fullname: str,
                   format_id: str,
                   code: int):
    
    print(f'request.base_url======== {request.base_url}') #(CAMBIO)

    print(f'fullname without casting in download_audio_file======== {fullname}***') #(CAMBIO)
    #Removing all whitespace characters from the right end of the string
    fullname = remove_trailing_spaces(fullname)
    print(f'fullname with casting in download_audio_file======== {fullname}***') #(CAMBIO)

    print(f'format_id without casting download_audio_file======== {format_id}') #(CAMBIO)
    #Removing all whitespace characters from the left end of the string
    format_id = remove_leading_spaces(format_id)
    print(f'format_id with casting in download_audio_file======== {format_id}') #(CAMBIO)

    file_path = download_audio(url, format_id, fullname, code)

    if file_path == 'error_invalid_url':
        return RedirectResponse(f'{request.base_url}{file_path}')

    return JSONResponse({'file_path': file_path}, status_code=200)

class ResourceLockedError(Exception):
    pass
class UnknownError(Exception):
    pass
@app.delete('/delete-file', response_class=Response) #(CANBIO POR FIN SOLUCION AL METODO delete)
async def delete_file(request: Request, file_path: str, event_name: str):
    # Deletes a file, waiting if it's being used by another process.
    max_retries = 10  # Number of times to check if the file is free
    wait_time = 1  # Seconds to wait between retries

    delete_progress(event_name)

    for lap in range(max_retries):
        try:
            os.remove(file_path)
            print(f"File '{file_path}' deleted successfully\n")
            return Response(status_code=status.HTTP_200_OK)
        except PermissionError:
            print(f"Waiting for '{file_path}' to be unlocked. Lap {lap}\n")
            unlock_file(file_path)
            time.sleep(wait_time)  # Wait and retry
        except FileNotFoundError:
            #raise HTTPException(status_code=404, detail="File not found")
            print("File not found. Could be already removed\n")
            return Response(status_code=status.HTTP_404_NOT_FOUND)
        except ResourceLockedError as e:
            print("The resource is locked and cannot be accessed {e}\n")
            return Response(status_code=status.HTTP_423_LOCKED)
    
    raise UnknownError(status_code=409, detail="Conflict: File could not be deleted")

"""    MUY INTEREANTE! 
from http import HTTPStatus

print(HTTPStatus.LOCKED)  # Output: HTTPStatus.LOCKED
print(HTTPStatus.LOCKED.value)  # Output: 423
print(HTTPStatus.LOCKED.phrase)  # Output: 'Locked'
print(HTTPStatus.LOCKED.description)  # Output: 'The resource is locked.'
"""

""""
@app.delete('/delete-file', response_class=Response)
def delete_static_file(request: Request, file_path: str): #(CAMBIO INTENTAR BORRAR EL DICHOSO ARCHIVO)

    try:
        delete_file(file_path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FileNotFoundError:
        print('File was already deleted.')
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        print(f'An unexpected error occurred= {e}')
        if(status == status.HTTP_409_CONFLICT):
            time.sleep(0.5)  #(CAMBIO) Pauses execution for 0.5 seconds
            delete_static_file(request, file_path) #(CAMBIO) Nested call
        return Response(status_code=status.HTTP_204_NO_CONTENT)
"""        


#from starlette.responses import StreamingResponse

# Dictionary to track progress for each active download event
#dl_progress = {}

@app.get('/get-progress')
async def get_progress(event_name: str):
    return StreamingResponse(progress_generator(event_name), media_type="text/event-stream")

"""ESTA ES LA MIA
@app.get('/get-progress')
async def get_progress(event_name: str):
    return StreamingResponse(progress_generator(event_name), media_type="text/event-stream")
"""

@app.get('/error_invalid_url')
def error_invalid_url(request: Request):
    return templates.TemplateResponse(
        request=request, name="error_invalid_url.html")
