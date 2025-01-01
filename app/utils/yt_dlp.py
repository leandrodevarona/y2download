import os
import yt_dlp as yt
from app.utils.random_name import get_random_name
from app.utils.types.yt_dlp import Quality
from app.utils.types.yt_qualities import YtQuality

def validate(url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            'outtmpl': 'example' + '%(ext)s'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if info_dict['extractor'] == 'youtube': 
                return True   
            
        return False    
    
    except:
        return False
    

def get_thumbnail_url(url):
    try:

        ydl_opts = {
            "format": "bestvideo/best",
            'outtmpl': 'example' + '%(ext)s'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            video_id = info_dict['display_id']

            return f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
    except:
        return None
    

def get_video_approx_size(url, quality: Quality = Quality.HIGHT):
    try:

        format = "bestvideo/best"

        if quality is not Quality.HIGHT:
            format = f'bestvideo[height<={quality.value}]'

        ydl_opts = {
            "format": format,
            'outtmpl': 'example' + '%(ext)s'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            return info_dict['filesize_approx']
    except:
        return None


def get_video_formats(url: str):
     # Crear una instancia de yt_dlp.YoutubeDL con las opciones adecuadas
    ydl_opts = {
        'quiet': True,  # Para no mostrar demasiada salida en consola
        'extract_flat': True,  # Extraer solo la información sin descargar el video
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Obtener la información del video
        info_dict = ydl.extract_info(url, download=False)  # No descargar, solo obtener información
        
        # Acceder a la lista de formatos
        formats = info_dict.get('formats', [])

        return formats
    

def get_format_str(formats: list, quality: Quality):

    filter_formats = [f for f in formats if f.get('height', None) is quality.value and f.get('tbr', None) is not None]

    min_bitrate = min(filter_formats, key=lambda format: format['tbr'])

    format_id = min_bitrate.get('format_id', 137)

    format_str = f"{format_id}+ba[ext=m4a]/{format_id}+ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    return format_str


def download(url, quality: Quality = Quality.HIGHT):
    try:
        name = get_random_name()

        ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'bin', 'ffmpeg.exe')

        formats = get_video_formats(url)

        format_str = get_format_str(formats, quality)

        ydl_opts = {
            "format": format_str,
            "final_ext": "mp4",
            "ffmpeg_location": ffmpeg_path,
            'outtmpl': f'static/{name}.' + '%(ext)s'
        }  

        with yt.YoutubeDL(ydl_opts) as ydl:
            is_valid_url = validate(url)

            if not is_valid_url:
                return 'error_invalid_url'
            
            info_dict = ydl.extract_info(url, download=True)

            ext = info_dict['ext']

            file_path = f'static/{name}.{ext}'

            return file_path
    except:
        return 'error_invalid_url'