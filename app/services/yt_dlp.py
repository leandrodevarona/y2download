import os
import yt_dlp as yt
from app.utils.data import bytes_to_megabytes
from app.utils.strings import (clean_file_name, 
                               filter_numeric_format_id,
                               filter_format_id
                               ) 
from asyncio import sleep
from fastapi.responses import (HTMLResponse,
                               RedirectResponse,
                               JSONResponse,
                               Response,
                               StreamingResponse)
from fastapi import (FastAPI, Request, status)


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
    # Create an instance of yt_dlp.YoutubeDL  with the propper options
    ydl_opts = {
        'quiet': True,       # For not to show to much info in terminal
        'extract_flat': True # Don't download the file
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Get only file info, don't download it
        info_dict = ydl.extract_info(url, download=False)
        # Get all available display_ids list
        video_id = info_dict["display_id"]
        # Get and clean up file fulltitle
        fullname = info_dict.get("fulltitle", video_id)
        fullname = clean_file_name(fullname)
        # Get file thumbnail 
        thumbnail = f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'
        # Get the formats list
        formats = info_dict.get("formats", [])

        return [fullname, formats, thumbnail]

# Uniques video options with the lowest bit rates sorted by resolution
def get_download_video_options(formats: list,
                         video_url: str,
                         base_url: str,
                         fullname: str):

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

        file_approx = bytes_to_megabytes(file_approx)

        format_id = f.get("format_id", '137')

        resolution = f'{f.get("height", None)}p'

        if file_approx > 0: # Zero not allowed

            options.append(
                {
                    'name': resolution,
                    'format_id': format_id,
                    'file_approx': file_approx,
                    'size': f'{"Unk" if file_approx == 0 else file_approx}Mb',
                    'url': f'{base_url}download_video?format_id={format_id}&fullname={fullname}&resolution={resolution}&url={video_url}'
                }
            )

    options = filter_numeric_format_id(options)

    options = filter_format_id(options)

    options.sort(key=lambda format: format['file_approx'], reverse = True)

    return options


# Uniques and standard audio options sorted by resolution
def get_download_audio_options(formats: list,
                         audio_url: str,
                         base_url: str,
                         fullname: str):

    available_audio = [f for f in formats if f.get('height', None) is None]

    options = []

    for f in available_audio:
        
        file_approx = f.get("filesize_approx", 0)

        file_approx = bytes_to_megabytes(file_approx)

        format_id = f.get("format_id", '233')

        code = f.get("quality", '0')

        extension = f.get("ext", 'mp3')

        if file_approx > 0: # Zero not allowed

            options.append(
                {
                    'name': f'(Qty{code}){extension}',
                    'code': code,
                    'format_id': format_id,
                    'file_approx': file_approx,
                    'size': f'{"Unk" if file_approx == 0 else file_approx}Mb',
                    'url': f'{base_url}download_audio?format_id={format_id}&fullname={fullname}&url={audio_url}&code={code}'
                }
            )

    
    options = filter_numeric_format_id(options)

    options = filter_format_id(options)

    options.sort(key=lambda format: format['file_approx'], reverse = True)

    return options


def download_video(url: str, format_id: str, fullname: str, resolution: str):

    try:

        ffmpeg_path = os.path.join(os.path.dirname(
            __file__), 'ffmpeg', 'bin', 'ffmpeg.exe')
        
        ydl_opts = {
            'format': format_id,                  # Use the specified format ID
            'ffmpeg_location': ffmpeg_path,
            # Save file with the desired fullname in \static\
            'outtmpl': f'static/{fullname}({resolution}).' + '%(ext)s',
            'progress_hooks': [dl_progress_hook], # Invoques fun 'dl_progress_hook'
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
        print(f'Download error. {e}')


def download_audio(url: str, format_id: str, fullname: str, code: str):

    ydl_opts = {
        'format': format_id,                  # Use the specified format ID
        'extractaudio': True,                 # Extract audio only
        # Save file with the desired fullname in \static\
        'outtmpl': f'static/{fullname}(Qty{code}).' + '%(ext)s',
        'progress_hooks': [dl_progress_hook], # Invoques fun 'dl_progress_hook'
    }

    try:
        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict["extractor"] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])
       
            ext = info_dict["ext"]

            file_path = f'static/{fullname}(Qty{code}).{ext}'

            return file_path
        
    except Exception as e:
        print(f'Download error. {e}')


dl_progress = {}  # Global dictionary to store progress for each button/event

async def progress_generator(event_name: str):
    if event_name not in dl_progress:
            dl_progress[event_name] = 0  # Initialize progress

    while dl_progress.get(event_name, 0) <= 100:
        yield f"event: {event_name}\ndata: {dl_progress.get(event_name, 0)}\n\n"
        await sleep(1.0)      


def dl_progress_hook(d):
    info_dict = d.get("info_dict")  

    if not info_dict:
        return
    
    format_id =  info_dict.get('format_id')
    event_name = 'progressUpdate_' + format_id # Unique key per download event

    if not format_id:
        return
    
    if d["status"] == "downloading":
        dl_progress[event_name] = round(d["_percent"], 1)
    else:
        dl_progress[event_name] = 100  # Mark as complete


def delete_progress(event_name: str):
    try:
        del dl_progress[event_name] # Removes item from dict when download ends
    except:
        print(f'Progress delete error= ', { event_name })


class ResourceLockedError(Exception):
    pass
def unlock_file(file_path):
    try:
        os.unlink(file_path)
        print(f"File '{file_path}' unlocked successfully\n")
        return Response(status_code=status.HTTP_200_OK)
    except FileNotFoundError:
            #raise HTTPException(status_code=404, detail="File not found")
            print("File not found. Could be already removed\n")
            return Response(status_code=status.HTTP_404_NOT_FOUND)
    except ResourceLockedError as e:
        print(e)
        return Response(status_code=status.HTTP_423_LOCKED)
