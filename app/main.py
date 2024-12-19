from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.utils.yt_dlp import download, validate, get_thumbnail_url, get_video_approx_size
from app.utils.types.yt_dlp import Quality
from app.utils.data import bytes_to_megabytes

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="app/templates")

@app.get('/', response_class=HTMLResponse)
def home_view(request: Request):
    return templates.TemplateResponse(
        request=request, name="home.html"
    )


@app.get('/download-options/', response_class=HTMLResponse)
def download_options(request: Request, url: str):
    is_valid_url = validate(url)

    if not is_valid_url:
        return RedirectResponse(f'{request.base_url}error_invalid_url')
    else:

        thumbnail_url = get_thumbnail_url(url)

        hightSize = bytes_to_megabytes(get_video_approx_size(url))
        mediumSize = bytes_to_megabytes(get_video_approx_size(url, Quality.MEDIUM))
        lowSize = bytes_to_megabytes(get_video_approx_size(url, Quality.LOW))

        return templates.TemplateResponse(
            request=request, 
            name="download_options.html", 
            context = {  
                'video_options': [
                    {
                        'name': 'MP4 best quality',
                        'size': f'{hightSize}Mb',
                        'url': f'{request.base_url}download?url={url}&quality={Quality.HIGHT.value}',
                    },
                    {
                        'name': f'{Quality.MEDIUM.value}p (.mp4)',
                        'size': f'{mediumSize}Mb',
                        'url': f'{request.base_url}download?url={url}&quality={Quality.MEDIUM.value}'
                    },
                    {
                        'name': f'{Quality.LOW.value}p (.mp4)',
                        'size': f'{lowSize}Mb',
                        'url': f'{request.base_url}download?url={url}&quality={Quality.LOW.value}'
                    }
                ],
                'audio_option': 
                    {
                        'name': 'Audio (.m4a)',
                        'size': '3Mb',
                        'url': f'{request.base_url}download?url={url}&is_audio=true'
                    },
                'thumbnail': thumbnail_url
            }
        )


@app.get('/download/', response_class=RedirectResponse | FileResponse)
def download_video(request: Request, 
                   url: str, 
                   quality: int, 
                   is_audio: bool = False):
    
    quality = Quality.get_quality(quality)

    file_path = download(url, quality)

    if file_path == 'error_invalid_url':
        return RedirectResponse(f'{request.base_url}{file_path}')

    file_name = file_path.split("/")[-1]

    return FileResponse(file_path, filename=file_name, media_type='video/mp4')


@app.get('/error_invalid_url')
def error_invalid_url(request: Request):
    return templates.TemplateResponse(
        request=request, name="error_invalid_url.html"
    )