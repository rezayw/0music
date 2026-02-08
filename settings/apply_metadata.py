# settings/apply_metadata.py

from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen.mp3 import MP3
import os
import mimetypes

def apply_metadata(file_path, title, artist, album, thumbnail_path=None):
    try:
        audio = MP3(file_path, ID3=ID3)

        if audio.tags is None:
            audio.add_tags()

        audio["TIT2"] = TIT2(encoding=3, text=title or "Unknown Title")
        audio["TPE1"] = TPE1(encoding=3, text=artist or "Unknown Artist")
        audio["TALB"] = TALB(encoding=3, text=album or "Unknown Album")

        if thumbnail_path and os.path.exists(thumbnail_path):
            with open(thumbnail_path, 'rb') as img:
                # Detect MIME type from file extension
                mime_type, _ = mimetypes.guess_type(thumbnail_path)
                if not mime_type or not mime_type.startswith('image/'):
                    mime_type = 'image/jpeg'  # Default fallback

                audio["APIC"] = APIC(
                    encoding=3,
                    mime=mime_type,
                    type=3,
                    desc=u"Cover",
                    data=img.read()
                )

        audio.save()
        print(f"Metadata successfully applied to: {file_path}")

    except Exception as e:
        print(f"[ERROR] Failed to apply metadata: {e}")
