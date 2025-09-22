import os
import time
import yt_dlp as yt
from app.utils.data import bytes_to_megabytes
from app.utils.strings import (clean_file_name, 
                               filter_numeric_format_id,
                               filter_format_id,
                               get_random_string
                               ) 
from asyncio import sleep
from fastapi.responses import Response
from fastapi import status

dl_progress = {}  # Global dictionary to store progress for each button/event

def validate(url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": 'example' + '%(ext)s'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            ydl.close()

            if info_dict["extractor"] == 'youtube':
                return True
        return False

    except Exception as e:
        print(e)
        return False

def get_file_info(url: str):
    # Create an instance of yt_dlp.YoutubeDL  with the propper options
    ydl_opts = {
        'quiet': True,       # For not to show to much info in terminal
        'extract_flat': True # Don't download the file
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Get only file info, don't download it
        info_dict = ydl.extract_info(url, download=False)
        # Get all available display_ids list
        #video_id = info_dict["display_id"]
        video_id = info_dict.get("display_id")
        # Get and clean up file fulltitle
        fullname = info_dict.get("fulltitle", video_id)
        fullname = clean_file_name(fullname)
        # Get file thumbnail
        if os.path.exists(f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg'):
            thumbnail = os.path
        else:
            #set default logo        
            thumbnail = info_dict.get("thumbnail", video_id)
        # Get the formats list
        formats = info_dict.get("formats", [])

        ydl.close()

        return [fullname, formats, thumbnail]

# Uniques video options with the lowest bit rates sorted by resolution
def get_download_video_options(formats: list,
                         video_url: str,
                         base_url: str,
                         fullname: str,
                         ):

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

        resolution = f.get("height", None)

        extension = f.get("ext", 'mp4')

        random_str = get_random_string(4)

        event_name = f'progressEvent_{format_id}_{random_str}'

        if file_approx > 0: # Zero not allowed

            options.append(
                {
                    'event_name': event_name,
                    'extension': extension,
                    'resolution': resolution,
                    'res_str': f'{resolution}px',
                    'format_id': format_id,
                    'file_approx': file_approx,
                    'size': f'{"Unk" if file_approx == 0 else file_approx}Mb',
                    'url': f'{base_url}download_video?format_id={format_id}&fullname={fullname}&resolution={resolution}&url={video_url}&event_name={event_name}'
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
                         fullname: str,
                         ):

    available_audio = [f for f in formats if f.get('height', None) is None]

    options = []

    for f in available_audio:
        
        file_approx = f.get("filesize_approx", 0)

        file_approx = bytes_to_megabytes(file_approx)

        format_id = f.get("format_id", '233')

        quality = f.get("quality", '0')

        extension = f.get("ext", 'mp3')

        random_str = get_random_string(4)

        event_name = f'progressEvent_{format_id}_{random_str}'

        if file_approx > 0: # Zero not allowed

            options.append(
                {
                    'event_name': event_name,
                    'extension': extension,
                    'quality': quality,
                    'qty_str': f'Qty({quality})',
                    'format_id': format_id,
                    'file_approx': file_approx,
                    'size': f'{"Unk" if file_approx == 0 else file_approx}Mb',
                    'url': f'{base_url}download_audio?format_id={format_id}&fullname={fullname}&quality={quality}&url={audio_url}&event_name={event_name}'
                }
            )

    options = filter_numeric_format_id(options)

    options = filter_format_id(options)

    options.sort(key=lambda format: format['file_approx'], reverse = True)

    return options


def get_format_video_str(format_id: str):

    format_video_str = f"{format_id}+ba[ext=m4a]/{format_id}\
        +ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    return format_video_str


def download_video(url: str, format_id: str, fullname: str, resolution: str, event_name: str):
    print('\nfullname = ', fullname)
    try:

        ffmpeg_path = os.path.join(os.path.dirname(
            __file__), 'ffmpeg', 'bin', 'ffmpeg.exe')
        
        format_str = get_format_video_str(format_id)
        
        ydl_opts = {
            'format': format_str,               # Use the specified format_str
            'ffmpeg_location': ffmpeg_path,
            'outtmpl': f'static/{fullname}({resolution}px).' + '%(ext)s', # Save file with the desired fullname in \static\
            'progress_hooks': [wrapper_progress_hook(event_name)], # Invoques fun 'dl_progress_hook'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict["extractor"] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])

            file_path = ydl.prepare_filename(info_dict)

            ydl.close()

            return file_path
        
    except Exception as e:
        print(f'\nDownload error: {e}')


def download_audio(url: str, format_id: str, fullname: str, quality: str, event_name: str):

    try:
        ydl_opts = {
            'format': format_id,                # Use the specified format ID
            'extractaudio': True,               # Extract audio only
            'outtmpl': f'static/{fullname}(Qty{quality}).' + '%(ext)s', # Save file with the desired fullname in \static\
            'progress_hooks': [wrapper_progress_hook(event_name)], # Invoques fun 'dl_progress_hook'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            is_valid_url = info_dict["extractor"] == 'youtube'

            if not is_valid_url:
                return 'error_invalid_url'

            ydl.download([url])
       
            file_path = ydl.prepare_filename(info_dict)

            ydl.close()

            return file_path
        
    except Exception as e:
        print(f'\nDownload error: {e}')


async def progress_generator(event_name: str):
    if event_name not in dl_progress:
            dl_progress[event_name] = 0  # Initialize progress

    while dl_progress.get(event_name, 0) <= 100:
        if dl_progress[event_name] != -1:
            yield f"event: {event_name}\ndata: {dl_progress.get(event_name, 0)}\n\n"
            await sleep(0.5)
        else:
            # Stop event processing (I guess!)
            dl_progress[event_name] = 100
            yield f"event: {event_name}\ndata: {dl_progress.get(event_name, 0)}\n\n"


def wrapper_progress_hook(event_name, max_retries=3, delay=2):
    def dl_progress_hook(d):
        status = d.get("status")
        try:
            if status in ["downloading", "extracting", "post-processing"]:
                dl_progress[event_name] = round(d["_percent"], 1)
            elif status in ["finished", "done"]:
                dl_progress[event_name] = 100  # Mark as complete
                print(f"[{event_name}] download COMPLITED!")
            elif status == 'error':
                dl_error = d.get('error', 'Unknown error')
                raise Exception(f"An error has occurred: {dl_error}")
                print(f"An error has occurred: {dl_error}")
            elif status == 'cancelled':
                raise Exception("Download canceled.")
            else:
                print(f"[{event_name}] Status '{status}', progress: {dl_progress.get(event_name, 0)}")
                print(f"[youtube ERROR]: Failed to extract any player response... {status}, {dl_error}\n")
        except Exception as e:
            print(f"[{event_name}] Exception: {e}")
            # Retrying
            nonlocal max_retries
            if max_retries > 0:
                max_retries -= 1
                print(f"[{event_name}] Retrying in {delay} seconds... ({max_retries} Retries)")
                time.sleep(delay)
            else:
                print(f"[{event_name}] Retries exhausted.")
                dl_progress[event_name] = -1  # Mark as error
    return dl_progress_hook

def delete_progress(event_name: str):
    try:
        del dl_progress[event_name] # Removes item from dict when download ends
    except:
        print(f'Progress delete error: ', { event_name })

""" NOT NECESSARY
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
"""