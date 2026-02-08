# settings/downloader.py

from yt_dlp import YoutubeDL
from PIL import Image
import requests
from io import BytesIO
from .utils import sanitize_filename
from .config import OUTPUT_DIR
from .database import add_song
from datetime import datetime

def extract_video_info(url):
    """Extract video metadata including thumbnail, title, and author."""
    with YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # Get thumbnail
        thumb_url = info.get('thumbnail')
        img = None
        if thumb_url:
            response = requests.get(thumb_url)
            img = Image.open(BytesIO(response.content))
            img.thumbnail((320, 180))
        
        return {
            'thumbnail': img,
            'title': info.get('title', ''),
            'author': info.get('uploader', '') or info.get('channel', '')
        }


# Keep old function name for backward compatibility
def extract_thumbnail(url):
    info = extract_video_info(url)
    return info.get('thumbnail')

def download_audio(url, custom_title=None, custom_author=None):
    try: # Kita tetap pertahankan try-except dasar di sini untuk menangkap kegagalan utama
        with YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)

        display_title = custom_title or info['title']
        safe_title = sanitize_filename(display_title)
        outtmpl = f"{OUTPUT_DIR}/{safe_title}.%(ext)s"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True, # Pastikan ini True untuk mengurangi output konsol
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        filename = f"{safe_title}.mp3"
        add_song(display_title, filename, author=custom_author, downloaded=datetime.now(), lurl=url)
        return display_title
    except Exception as e:
        # Ini adalah penanganan error umum yang akan dilempar kembali ke GUI
        print(f"Error occurred during download: {e}") # Log error ke konsol
        raise e # Lempar kembali error aslinya agar gui.py bisa menanganinya