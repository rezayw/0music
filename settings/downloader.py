# settings/downloader.py

from yt_dlp import YoutubeDL
from PIL import Image
import requests
from io import BytesIO
import os
import sys
import tempfile
from .utils import sanitize_filename
from .config import OUTPUT_DIR
from .database import add_song
from .apply_metadata import apply_metadata
from datetime import datetime

def get_ffmpeg_path():
    """Get the path to bundled ffmpeg binaries."""
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in development
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    bin_path = os.path.join(base_path, 'bin')
    return bin_path

def get_ydl_opts(quiet=True):
    """Get common yt-dlp options with bot bypass settings."""
    ffmpeg_location = get_ffmpeg_path()

    return {
        'quiet': quiet,
        'no_warnings': True,
        'ffmpeg_location': ffmpeg_location,
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

def download_thumbnail(thumb_url, save_path):
    """Download thumbnail image and save to file."""
    try:
        response = requests.get(thumb_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        # Convert to RGB (JPEG doesn't support alpha)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        # Resize to standard album cover size (square 500x500)
        size = min(img.width, img.height)
        left = (img.width - size) // 2
        top = (img.height - size) // 2
        img = img.crop((left, top, left + size, top + size))
        img = img.resize((500, 500), Image.LANCZOS)
        img.save(save_path, 'JPEG', quality=95)
        return save_path
    except Exception as e:
        print(f"Failed to download thumbnail: {e}")
        return None

def extract_video_info(url):
    """Extract video metadata including thumbnail, title, author, and stream URL."""
    ydl_opts = get_ydl_opts()
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        
        # Get thumbnail - try to get highest quality
        thumb_url = None
        thumbnails = info.get('thumbnails', [])
        if thumbnails:
            # Sort by resolution (prefer maxresdefault)
            sorted_thumbs = sorted(thumbnails, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
            thumb_url = sorted_thumbs[0].get('url') if sorted_thumbs else info.get('thumbnail')
        else:
            thumb_url = info.get('thumbnail')
        
        img = None
        if thumb_url:
            try:
                response = requests.get(thumb_url, timeout=10)
                img = Image.open(BytesIO(response.content))
                img.thumbnail((338, 190), Image.LANCZOS)  # 16:9 aspect ratio for preview
            except Exception as e:
                print(f"Thumbnail fetch error: {e}")
        
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
            'thumbnail_url': thumb_url,
            'title': info.get('title', ''),
            'author': info.get('uploader', '') or info.get('channel', ''),
            'album': info.get('album', '') or info.get('title', ''),  # Use track title as album fallback
            'stream_url': stream_url
        }


# Keep old function name for backward compatibility
def extract_thumbnail(url):
    info = extract_video_info(url)
    return info.get('thumbnail')

def download_audio(url, custom_title=None, custom_author=None):
    """Download audio from YouTube with full metadata and cover art."""
    temp_cover = None
    try:
        info_opts = get_ydl_opts()
        with YoutubeDL(info_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Get metadata
        display_title = custom_title or info.get('title', 'Unknown Title')
        display_author = custom_author or info.get('uploader', '') or info.get('channel', 'Unknown Artist')
        album = info.get('album', '') or display_title  # Use title as album if not available
        
        # Get best thumbnail URL
        thumb_url = None
        thumbnails = info.get('thumbnails', [])
        if thumbnails:
            sorted_thumbs = sorted(thumbnails, key=lambda x: x.get('width', 0) * x.get('height', 0), reverse=True)
            thumb_url = sorted_thumbs[0].get('url') if sorted_thumbs else info.get('thumbnail')
        else:
            thumb_url = info.get('thumbnail')
        
        safe_title = sanitize_filename(display_title)
        outtmpl = f"{OUTPUT_DIR}/{safe_title}.%(ext)s"

        ydl_opts = get_ydl_opts()
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',  # Higher quality
            }],
        })

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        filename = f"{safe_title}.mp3"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        # Download and embed cover art
        if thumb_url:
            temp_cover = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False).name
            cover_path = download_thumbnail(thumb_url, temp_cover)
            if cover_path and os.path.exists(filepath):
                apply_metadata(filepath, display_title, display_author, album, cover_path)
        else:
            # Apply metadata without cover
            if os.path.exists(filepath):
                apply_metadata(filepath, display_title, display_author, album, None)
        
        add_song(display_title, filename, author=display_author, downloaded=datetime.now(), lurl=url)
        return display_title
        
    except Exception as e:
        print(f"Error occurred during download: {e}")
        raise e
    finally:
        # Clean up temp cover file
        if temp_cover and os.path.exists(temp_cover):
            try:
                os.remove(temp_cover)
            except:
                pass