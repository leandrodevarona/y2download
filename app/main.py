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
                                 delete_file,
                                 progress_generator)
from fastapi.middleware.cors import CORSMiddleware
from app.utils.strings import (remove_trailing_spaces,
                              remove_leading_spaces)
import time


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


"""=================================================================(CAMBIO)
 Example usage
download_audio(
    'https://www.youtube.com/watch?v=example_video_id',
    'bestaudio',
    '/path/to/your/file.mp3',
    '4'
)
================================================================="""


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


@app.delete('/delete-file/', response_class=Response)
def delete_static_file(request: Request, file_path: str): #(CAMBIO INTENTAR BORRAR EL DICHOSO ARCHIVO)

    try:
        delete_file(file_path)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FileNotFoundError:
        print("Error: The file was not found.")
    except Exception as e:
        print(f'An unexpected error occurred===== {e}')
        #print("Let's wait a while and try again...")
        #time.sleep(0.5)  # Pauses execution for 0.5 seconds
        #time.sleep(5)  # Pauses execution for 5 seconds
        #delete_static_file(request, file_path)
        return Response(status_code=status.HTTP_409_CONFLICT)

@app.get('/get-progress')
async def get_progress(event_name: str):
    return StreamingResponse(progress_generator(event_name), media_type="text/event-stream")


@app.get('/error_invalid_url')
def error_invalid_url(request: Request):
    return templates.TemplateResponse(
        request=request, name="error_invalid_url.html")
