import os
import yt_dlp as yt
from app.utils.random_name import get_random_name

def download(url):
    try:
        name = get_random_name()

        ffmpeg_path = os.path.join(os.path.dirname(__file__), 'ffmpeg', 'bin', 'ffmpeg.exe')

        print('El path...', ffmpeg_path)

        ydl_opts = {
            "format": "137+ba[ext=m4a]/137+ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b",
            "final_ext": "mp4",
            "ffmpeg_location": ffmpeg_path,
            'outtmpl': f'static/{name}.' + '%(ext)s'
        }  

        with yt.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if info_dict['extractor'] is not 'youtube':
                return 'error_invalid_url'
            
            ydl.download([url])

            ext = info_dict['ext']

            file_path = f'static/{name}.{ext}'

            return file_path
    except:
        return 'error_invalid_url'
  