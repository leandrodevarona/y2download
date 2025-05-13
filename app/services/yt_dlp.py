import os
import yt_dlp as yt
from app.utils.data import bytes_to_megabytes
from app.utils.strings import (clean_file_name, 
                               filter_numeric_format_id,
                               #keep_numbers_only, 
                               filter_format_id
                               ) 
from asyncio import sleep


def validate(url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": 'example' + '%(ext)s'
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
        'quiet': True,       # Para no mostrar demasiada salida en consola
        'extract_flat': True # Extraer solo la información sin descargar el video
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Obtener la información del video
        # No descargar, solo obtener información
        info_dict = ydl.extract_info(url, download=False)

        video_id = info_dict["display_id"]
        print((f'video_id===== {video_id}'))

        fullname = info_dict.get("fulltitle", video_id)
        print((f'fullname===== {fullname}***')) #(CAMBIO)

        fullname = clean_file_name(fullname)
        print((f'fullname===== {fullname}***')) #(CAMBIO)

        thumbnail = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'

        # Acceder a la lista de formatos
        formats = info_dict.get("formats", [])

        return [fullname, formats, thumbnail]


def get_download_video_options(formats: list,
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

        file_approx = bytes_to_megabytes(file_approx)

        format_id = f.get('format_id', 137)

        #format_id = keep_numbers_only(format_id) #(CAMBIO MEJORA)

        resolution = f'{f.get("height", None)}p'

        if file_approx > 0: #(CAMBIO file_approx NO PUEDE SER CERO)

            options.append(
                {
                    'name': resolution,
                    'format_id': format_id,
                    'file_approx': file_approx,
                    'size': f'{"Unk" if file_approx == 0 else file_approx} Mb',
                    'url': f'{base_url}download_video?format_id={format_id}&fullname={fullname}&resolution={resolution}&url={video_url}'
                }
            )

    #(CAMBIO ELIMINA LOS format_id QUE CONTIENEN NUMEROS)
    options = filter_numeric_format_id(options)

    #(CAMBIO ELIMINA LOS format_id DUPLICADOS, JUST IN CASE)
    options = filter_format_id(options)

    #(CAMBIO MEJOR ORDENAR POR file_approx QUE POR format_id)
    options.sort(key=lambda format: format['file_approx'], reverse = True)

    return options


def get_download_audio_options(formats: list,
                         audio_url: str,
                         base_url: str,
                         fullname: str):

    available_audio = [f for f in formats if f.get("height", None) is None]
    #print(f'available_audio===== {available_audio}')

    options = []

    for f in available_audio:
        
        file_approx = f.get('filesize_approx', 0)

        file_approx = bytes_to_megabytes(file_approx)

        format_id = f.get('format_id', 233)

        #format_id = keep_numbers_only(format_id) #(CAMBIO MEJORA)

        code = f.get('quality', 0)

        extension = f.get('ext', 'mp3')

        if file_approx > 0: #(CAMBIO file_approx NO PUEDE SER CERO)

            options.append(
                {
                    'name': f'({code}){extension}', #(CAMBIO TEMPORAL)
                    'code': code,
                    'format_id': format_id,
                    'file_approx': file_approx,
                    'size': f'{"Unk" if file_approx == 0 else file_approx} Mb',
                    'url': f'{base_url}download_audio?format_id={format_id}&fullname={fullname}&url={audio_url}&code={code}'
                }
            )

    
    #(CAMBIO ELIMINA LOS format_id QUE CONTIENEN NUMEROS)
    options = filter_numeric_format_id(options)

    #(CAMBIO ELIMINA LOS format_id DUPLICADOS, JUST IN CASE)
    options = filter_format_id(options)

    #(CAMBIO MEJOR ORDENAR POR file_approx QUE POR format_id)
    options.sort(key=lambda format: format['file_approx'], reverse = True)

    return options


def get_video_format_str(format_id: str):

    video_format_str = f"{format_id}+ba[ext=m4a]/{format_id}\
        +ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    return video_format_str

def get_audio_format_str(format_id: str):

    audio_format_str = f"{format_id}/ba[ext=m4a]/b[ext=m4a]/ba/b"

    return audio_format_str


def download_video(url: str, format_id: str, fullname: str, resolution: str):

    try:

        ffmpeg_path = os.path.join(os.path.dirname(
            __file__), 'ffmpeg', 'bin', 'ffmpeg.exe')

        format_str = get_video_format_str(format_id)

        ydl_opts = {
            'format': format_str,               # Use the specified format ID
            #'final_ext': 'mp4',                 # (CAMBIO INVENTO)
            'ffmpeg_location': ffmpeg_path,
            # Save file with the desired fullname in \static\
            #'outtmpl': f'static/{fullname}({resolution}).' + '%(ext)s',
            'outtmpl': f'static/{fullname}({resolution}).' + '%(ext)s',
            'progress_hooks': [dl_progress_hook] # Invoques fun 'dl_progress_hook'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict["extractor"] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])

            ext = info_dict["ext"]

            #file_path = f'static/{fullname}({resolution}).{ext}'
            file_path = f'static/{fullname}({resolution}).{ext}'

            return file_path
        
    except Exception as e:
        print(f'An error occurred===== : {e}')
        #return 'error_invalid_url' (CAMBIO) Duplicado ya se validó


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
def download_audio(url: str, format_id: str, fullname: str, code: str): #(CAMBIO)
    #format_str = get_audio_format_str(format_id) #(CAMBIO NO MORE COMPLICATIONS)

    ydl_opts = {
        #'format': format_str,          # Use the specified format ID #(CAMBIO NO MORE COMPLICATIONS)
        'format': format_id,            # Use the specified format ID
        'extractaudio': True,           # Extract audio only
        #'audioquality': code,          # Set audio quality #(CAMBIO ESTO NO FUNCIONA)
        #'audioformat': 'mp3',          # Save audio in MP3 format #(CAMBIO ESTO NO FUNCIONA)
        #'final_ext': 'mp3',            # (CAMBIO INVENTO)
        # Save file with the desired fullname in \static\
        #'outtmpl': f'static/{fullname}(Qty={code}).' + '%(ext)s',
        'outtmpl': f'static/{fullname}(Qty={code}).' + '%(ext)s',

        #'outtmpl': f'static/{fullname}({code}).' + '%(ext)s', # (CAMBIO AQUI PUEDE ESTAR EL PROB. DEL 'DELETE')
        'progress_hooks': [dl_progress_hook] # Invoques fun 'dl_progress_hook'
    }

    try:
        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict["extractor"] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])
       
            ext = info_dict["ext"]

            #file_path = f'static/{fullname}({code}).{ext}'
            file_path = f'static/{fullname}(Qty={code}).{ext}'

            return file_path
        
    except Exception as e:
        print(f'An error occurred===== : {e}')

dl_progress = 0

async def progress_generator(event_name: str):
    while dl_progress <= 100:
        yield f"event: {event_name}\ndata: {dl_progress}\n\n"
        await sleep(0.5)

def dl_progress_hook(d):
    global dl_progress
    
    print('El status...', d["status"])
    if d["status"] == "downloading":
        dl_progress = round(d["_percent"], 1) # (CAMBIO round 2)
    else:
        dl_progress = -1

def delete_file(file_path: str):
    if os.path.exists(file_path):
       os.unlink(file_path)
    else:
        raise Exception({'details===== ': 'File not found'})
