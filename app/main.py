from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.yt_dlp import (download, 
                                 validate, 
                                 get_thumbnail_url, 
                                 get_video_formats, 
                                 get_download_options)

app = FastAPI()

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

        thumbnail_url = get_thumbnail_url(url)

        formats = get_video_formats(url)

        options = get_download_options(formats, url, request.base_url)

        return templates.TemplateResponse(
            request=request, 
            name="download_options.html", 
            context = {  
                'video_options': options,
                'audio_option': 
                    {
                        'name': 'Audio (.m4a)',
                        'size': '3Mb',
                        'url': f'{request.base_url}download?is_audio=true&url={url}'
                    },
                'thumbnail': thumbnail_url
            }
        )


@app.get('/download/', response_class=RedirectResponse | FileResponse)
def download_video(request: Request, 
                   url: str, 
                   format_id: int, 
                   is_audio: bool = False):

    file_path = download(url, format_id)

    if file_path == 'error_invalid_url':
        return RedirectResponse(f'{request.base_url}{file_path}')

    file_name = file_path.split("/")[-1]

    return FileResponse(file_path, filename=file_name, media_type='video/mp4')


@app.get('/error_invalid_url')
def error_invalid_url(request: Request):
    return templates.TemplateResponse(
        request=request, name="error_invalid_url.html"
    )