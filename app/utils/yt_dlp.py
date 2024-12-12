import yt_dlp as yt
from app.utils.random_name import get_random_name

def download(url):
    name = get_random_name()

    ydl_opts = {
        # 'format': 'bestaudio/best',
        'format': 'bestvideo/best',
        'outtmpl': f'static/{name}.' + '%(ext)s',
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)

        if info_dict['extractor'] is not 'youtube':
            return 'error_invalid_url'
        
        ydl.download([url])

        ext = info_dict['ext']

        file_path = f'static/{name}.{ext}'

        return file_path