import yt_dlp as yt
from app.utils.types.yt_dlp import Quality

def get_video_approx_size(url, quality: Quality = Quality.HIGHT):
    try:

        format = "bestvideo/best"

        print(
            'La quality que llega',
            quality
        )

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

print(get_video_approx_size('https://www.youtube.com/shorts/bg4I_NtOshE', Quality.LOW))