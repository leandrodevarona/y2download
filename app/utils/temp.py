import yt_dlp as yt
from app.utils.types.yt_dlp import Quality

def get_video_formats(url: str):
     # Crear una instancia de yt_dlp.YoutubeDL con las opciones adecuadas
    ydl_opts = {
        'quiet': True,  # Para no mostrar demasiada salida en consola
        'extract_flat': True,  # Extraer solo la información sin descargar el video
    }

    with yt.YoutubeDL(ydl_opts) as ydl:
        # Obtener la información del video
        info_dict = ydl.extract_info(url, download=False)  # No descargar, solo obtener información
        
        # Acceder a la lista de formatos
        formats = info_dict.get('formats', [])

        return formats
    

def get_format_str(formats: list, quality: Quality):

    filter_formats = [f for f in formats if f.get('height', None) == quality.value and f.get('tbr', None) != None]

    min_bitrate = min(filter_formats, key=lambda format: format['tbr'])

    format_id = min_bitrate.get('format_id', 137)

    format_str = f"{format_id}+ba[ext=m4a]/{format_id}+ba/bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/bv*+ba/b"

    return format_str

# URL del video de YouTube
url_video = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

formatos = get_video_formats(url_video)

format_str = get_format_str(formatos, Quality.MEDIUM)

print(format_str)