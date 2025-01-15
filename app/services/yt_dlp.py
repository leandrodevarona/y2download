import os
import yt_dlp as yt
from app.utils.data import bytes_to_megabytes
from app.utils.strings import clean_file_name


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

    except Exception as e:
        print(e)
        return False


def get_video_info(url: str):
    # Crear una instancia de yt_dlp.YoutubeDL con las opciones adecuadas
    ydl_opts = {
        'quiet': True,  # Para no mostrar demasiada salida en consola
        # Extraer solo la información sin descargar el video
        'extract_flat': True,
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Obtener la información del video
        # No descargar, solo obtener información
        info_dict = ydl.extract_info(url, download=False)

        video_id = info_dict['display_id']

        fullname = info_dict['fulltitle']

        fullname = clean_file_name(fullname)

        thumbnail = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'

        # Acceder a la lista de formatos
        formats = info_dict['formats']

        return [fullname, formats, thumbnail]


def get_download_options(formats: list,
                         video_url: str,
                         base_url: str,
                         fullname: str):
    available_resolutions = [f['height'] for f in formats if f['height']
                             is not None and f['tbr'] is not None]

    available_resolutions = set(available_resolutions)

    min_bitrate_formats = []

    for resolution in available_resolutions:
        filter_formats = [f for f in formats if f['height'] == resolution]

        min_bitrate = min(filter_formats, key=lambda format: format['tbr'])

        min_bitrate_formats.append(min_bitrate)

    options = []

    for f in min_bitrate_formats:
        file_approx = f['filesize_approx']

        file_approx = bytes_to_megabytes(file_approx)

        resolution = f'{f['height']}p'

        options.append(
            {
                'name': resolution,
                'size': f'{'_' if file_approx == 0 else file_approx} Mb',
                'url': f'{base_url}download?format_id=\
                    {f['format_id']}&fullname={fullname}\
                        &resolution={resolution}&url={video_url}',
            }
        )

    return options


def get_format_str(format_id: str):

    format_str = f"{format_id}+ba[ext=m4a]/{format_id}\
        +ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    return format_str


def download(url, format_id: int, fullname: str, resolution: str):
    try:

        ffmpeg_path = os.path.join(os.path.dirname(
            __file__), 'ffmpeg', 'bin', 'ffmpeg.exe')

        format_str = get_format_str(format_id)

        ydl_opts = {
            "format": format_str,
            "final_ext": "mp4",
            "ffmpeg_location": ffmpeg_path,
            'outtmpl': f'static/{fullname}({resolution}).' + '%(ext)s'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict['extractor'] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])

            ext = info_dict['ext']

            file_path = f'static/{fullname}({resolution}).{ext}'

            return file_path
    except Exception as e:
        print(e)
        return 'error_invalid_url'


def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.unlink(file_path)
    else:
        raise Exception({'details': 'No file found'})
