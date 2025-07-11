from yt_dlp import YoutubeDL
from PIL import Image
import requests
from io import BytesIO
from .utils import sanitize_filename
from .config import OUTPUT_DIR
from .database import add_song
from datetime import datetime

def extract_thumbnail(url):
    with YoutubeDL({'quiet': True}) as ydl:
        info = ydl.extract_info(url, download=False)
        thumb_url = info.get('thumbnail')
        if not thumb_url:
            return None
        response = requests.get(thumb_url)
        img = Image.open(BytesIO(response.content))
        img.thumbnail((320, 180))
        return img

def download_audio(url, custom_title=None, custom_author=None):
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
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    filename = f"{safe_title}.mp3"
    add_song(display_title, filename, author=custom_author, downloaded=datetime.now(), lurl=url)
    return display_title
