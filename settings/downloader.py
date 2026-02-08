# settings/downloader.py

from yt_dlp import YoutubeDL
from PIL import Image
import requests
from io import BytesIO
from .utils import sanitize_filename
from .config import OUTPUT_DIR
from .database import add_song
from datetime import datetime

def get_ydl_opts(quiet=True):
    """Get common yt-dlp options with bot bypass settings."""
    return {
        'quiet': quiet,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'android'],
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
        }
    }

def extract_video_info(url):
    """Extract video metadata including thumbnail, title, author, and stream URL."""
    ydl_opts = get_ydl_opts()
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # Get thumbnail
        thumb_url = info.get('thumbnail')
        img = None
        if thumb_url:
            response = requests.get(thumb_url)
            img = Image.open(BytesIO(response.content))
            img.thumbnail((320, 180))
        
        # Get audio stream URL
        stream_url = None
        formats = info.get('formats', [])
        # Try to get best audio-only format
        for f in formats:
            if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                stream_url = f.get('url')
                break
        # Fallback to any format with audio
        if not stream_url:
            for f in formats:
                if f.get('acodec') != 'none':
                    stream_url = f.get('url')
                    break
        
        return {
            'thumbnail': img,
            'title': info.get('title', ''),
            'author': info.get('uploader', '') or info.get('channel', ''),
            'stream_url': stream_url
        }


# Keep old function name for backward compatibility
def extract_thumbnail(url):
    info = extract_video_info(url)
    return info.get('thumbnail')

def download_audio(url, custom_title=None, custom_author=None):
    try:
        info_opts = get_ydl_opts()
        with YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        display_title = custom_title or info['title']
        safe_title = sanitize_filename(display_title)
        outtmpl = f"{OUTPUT_DIR}/{safe_title}.%(ext)s"

        ydl_opts = get_ydl_opts()
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        filename = f"{safe_title}.mp3"
        add_song(display_title, filename, author=custom_author, downloaded=datetime.now(), lurl=url)
        return display_title
    except Exception as e:
        print(f"Error occurred during download: {e}")
        raise e