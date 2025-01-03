import os
import yt_dlp as yt
from app.utils.random_name import get_random_name
from app.utils.data import bytes_to_megabytes

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


def get_video_formats(url: str):
     # Crear una instancia de yt_dlp.YoutubeDL con las opciones adecuadas
    ydl_opts = {
        'quiet': True,  # Para no mostrar demasiada salida en consola
        'extract_flat': True,  # Extraer solo la información sin descargar el video
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Obtener la información del video
        info_dict = ydl.extract_info(url, download=False)  # No descargar, solo obtener información

        name = get_random_name()

        fullname = info_dict.get('fulltitle', name)
        
        # Acceder a la lista de formatos
        formats = info_dict.get('formats', [])

        return [fullname, formats]


def get_download_options(formats: list, video_url: str, base_url: str):
    available_resolutions = [f['height'] for f in formats if f.get('height', None) != None and f.get('tbr', None) != None ]

    available_resolutions = set(available_resolutions)

    min_bitrate_formats = []

    for resolution in available_resolutions:
        filter_formats = [f for f in formats if f.get('height', None) == resolution]

        min_bitrate = min(filter_formats, key=lambda format: format['tbr'])

        min_bitrate_formats.append(min_bitrate)

    options = []

    for f in min_bitrate_formats:
        file_approx = f.get('filesize_approx', 0)

        file_approx = bytes_to_megabytes(file_approx)

        options.append(
            {
                'name': f'{f.get('height', None)}p',
                'size': f'{'_' if file_approx == 0 else file_approx} Mb',
                'url': f'{base_url}download?format_id={f.get('format_id', 137)}&url={video_url}',
            }
        )
    
    return options


def get_format_str(format_id: str):

    format_str = f"{format_id}+ba[ext=m4a]/{format_id}+ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    return format_str


def download(url, format_id: int):
    try:
        name = get_random_name()

        ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'bin', 'ffmpeg.exe')

        format_str = get_format_str(format_id)

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