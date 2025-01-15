from fastapi import FastAPI, Request
from fastapi.responses import (HTMLResponse,
                               RedirectResponse,
                               JSONResponse,
                               Response)
from fastapi import status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.yt_dlp import (download,
                                 validate,
                                 get_video_info,
                                 get_download_options,
                                 delete_file)
from fastapi.middleware.cors import CORSMiddleware

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

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.get('/', response_class=HTMLResponse)
def home_view(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html"
    )


@app.get('/download-options/', response_class=HTMLResponse)
async def download_options(request: Request, url: str):
    is_valid_url = validate(url)

    if not is_valid_url:
        return RedirectResponse(f'{request.base_url}error_invalid_url')
    else:

        fullname, formats, thumbnail = get_video_info(url)

        options = get_download_options(
            formats, url, request.base_url, fullname)

        return templates.TemplateResponse(
            request=request,
            name="download_options.html",
            context={
                'fullname': fullname,
                'video_options': options,
                'audio_option':
                    {
                        'name': 'Audio (.m4a)',
                        'size': '3Mb',
                        'url': f'{request.base_url}\
                            download?is_audio=true&url={url}'
                    },
                'thumbnail': thumbnail
            }
        )


@app.get('/download/', response_class=RedirectResponse | JSONResponse)
def download_video(request: Request,
                   url: str,
                   fullname: str,
                   format_id: int,
                   resolution: str,
                   is_audio: bool = False):

    file_path = download(url, format_id, fullname, resolution)

    if file_path == 'error_invalid_url':
        return RedirectResponse(f'{request.base_url}{file_path}')

    return JSONResponse({'file_path': file_path}, status_code=200)


@app.delete('/delete-file/', response_class=Response)
def delete_static_file(request: Request, file_path: str):

    try:
        delete_file(file_path)

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        print(e)
        return Response(status_code=status.HTTP_404_NOT_FOUND)


@app.get('/error_invalid_url')
def error_invalid_url(request: Request):
    return templates.TemplateResponse(
        request=request, name="error_invalid_url.html"
    )
