import os
import yt_dlp as yt
from app.utils.data import bytes_to_megabytes
from app.utils.strings import clean_file_name
from asyncio import sleep

def validate(url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            'outtmpl': 'example' + '%(ext)s'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if info_dict["extractor"] == 'youtube':
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
        'extract_flat': True
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Obtener la información del video
        # No descargar, solo obtener información
        info_dict = ydl.extract_info(url, download=False)

        video_id = info_dict["display_id"]
        print((f'video_id============== {video_id}')) #(CAMBIO)

        fullname = info_dict.get("fulltitle", video_id)
        print((f'fullname============== {fullname}, ***')) #(CAMBIO)

        fullname = clean_file_name(fullname)

        thumbnail = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'

        # Acceder a la lista de formatos
        formats = info_dict.get("formats", [])

        return [fullname, formats, thumbnail]


def get_download_options(formats: list,
                         video_url: str,
                         base_url: str,
                         fullname: str):
    #pprint.pprint(formats)

    available_resolutions = [f["height"]
                             for f in formats if f.get("height", None)
                             is not None and f.get("tbr", None) is not None]

    available_resolutions = set(available_resolutions)

    min_bitrate_formats = []

    for resolution in available_resolutions:
        filter_formats = [f
                          for f in formats
                          if f.get("height", None) == resolution]

        min_bitrate = min(filter_formats, key=lambda format: format["tbr"])

        min_bitrate_formats.append(min_bitrate)

    options = []

    for f in min_bitrate_formats:
        
        file_approx = f.get("filesize_approx", 0)
        print((f'file_approx=========== {file_approx}'))
        #print((f'filesize_approx=========== {filesize_approx}'))

        file_approx = bytes_to_megabytes(file_approx)

        resolution = f'{f.get("height", None)}p'

        options.append(
            {
                'name': resolution,
                'size': f'{"unknow" if file_approx == 0 else file_approx} Mb',
                'url': f'{base_url}download?format_id=\
                    {f.get("format_id", 137)}&fullname={fullname}\
                        &resolution={resolution}&url={video_url}'
            }
        )

    return options


def get_download_audio_options(formats: list,
                         audio_url: str,
                         base_url: str,
                         fullname: str):

    available_audio = [f for f in formats if f.get("height", None) is None]
    #print(f'available_audio=====*** {available_audio}')

    options = []

    for f in available_audio:
        
        file_approx = f.get("filesize", 0)

        file_approx = bytes_to_megabytes(file_approx)

        format_id = f.get("format_id", 137)

        code = f.get('quality', 0) 

        format_id = f.get('format_id')

        options.append(
            {
                'name': f"mp3(ID:{format_id})",
                'size': f'{"unknow" if file_approx == 0 else file_approx} Mb',
                'url': f'{base_url}download_audio?format_id=\
                    {format_id}&fullname={fullname}\
                        &url={audio_url}&code={code}'
            }
        )

    return options


def get_format_str(format_id: str):

    format_str = f"{format_id}+ba[ext=m4a]/{format_id}\
        +ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    return format_str

def get_audio_format_str(format_id: str):

    audio_format_str = f"{format_id}/ba[ext=m4a]/b[ext=m4a]/ba/b"

    return audio_format_str

dl_progress = 0

async def progress_generator():
    while dl_progress <= 100:
        yield f"event: progressUpdate\ndata: {dl_progress}\n\n"
        await sleep(1)

def dl_progress_hook(d):
    global dl_progress
    if d["status"] == "downloading" and d["total_bytes"] > 0:
        dl_progress = int(d["downloaded_bytes"] / d["total_bytes"] * 100)
    else:
        dl_progress = -1

def download(url: str, format_id: str, fullname: str, resolution: str):

    try:

        ffmpeg_path = os.path.join(os.path.dirname(
            __file__), 'ffmpeg', 'bin', 'ffmpeg.exe')

        format_str = get_format_str(format_id)

        ydl_opts = {
            "format": format_str,
            "final_ext": "mp4",
            "ffmpeg_location": ffmpeg_path,
            'outtmpl': f'static/{fullname}({resolution}).' + '%(ext)s',
            "progress_hooks": [dl_progress_hook],
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict["extractor"] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])

            ext = info_dict["ext"]

            file_path = f'static/{fullname}({resolution}).{ext}'

            return file_path
        
    except Exception as e:
        print(f"An error occurred: {e}")
        #return 'error_invalid_url' (CAMBIO) Duplicado ya se validó

def download_audio(url: str, format_id: int, fullname: str, code: int): #(CAMBIO)
    """
    Downloads audio from a YouTube video using yt_dlp and saves it with a specific fullname.

    Parameters:
        url (str): The URL of the YouTube video.
        format_id (str): The format ID for the video/audio.
        fullname (str): The full name (including path) for saving the audio file.
        audio_quality (str): Desired audio quality (0=best, 9=worst).

    Returns:
        None
    """
    format_str = get_audio_format_str(format_id)

    options = {
        'format': format_str,          # Use the specified format ID
        'extractaudio': True,         # Extract audio only
        'audioquality': code,  # Set audio quality
        'audioformat': 'mp3',         # Save audio in MP3 format
        # Save file with the desired fullname in \static
        'outtmpl': f'static/{fullname}({code}).' + '%(ext)s'
    }

    try:
        with yt.YoutubeDL(options) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict["extractor"] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])
       
            ext = info_dict["ext"]

            file_path = f'static/{fullname}({code}).{ext}'

            return file_path
    except Exception as e:
        print(f"An error occurred: {e}")




def delete_file(file_path: str):
    if os.path.exists(file_path):
        os.unlink(file_path)
    else:
        raise Exception({'details': 'File not found'})
