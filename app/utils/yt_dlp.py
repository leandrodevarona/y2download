import os
import yt_dlp as yt
from app.utils.random_name import get_random_name
from app.utils.types.yt_dlp import Quality

def validate(url):
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            'outtmpl': 'example' + '%(ext)s'
        }

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if info_dict['extractor'] is 'youtube': 
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
    

def download(url, quality: Quality = Quality.HIGHT):
    try:
        name = get_random_name()

        ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'bin', 'ffmpeg.exe')

        str_quality = ''

        if quality != Quality.HIGHT:
            str_quality = f'[height<={quality.value}]'

        format = f"137+ba[ext=m4a]{str_quality}/137+ba/bv*[ext=mp4]{str_quality}+ba[ext=m4a]/b[ext=mp4]{str_quality}/bv*+ba/b"

        print(format)

        ydl_opts = {
            "format": format,
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