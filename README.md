# 🎵 0music Downloader

<p align="center">
<img src="https://blogger.googleusercontent.com/img/a/AVvXsEgiz-zCQAkhcdeRjOrXMNhI8A6KjJxQcUJ-ufU7BKPr8RlPus0crOjK2tgEqCISYdMx6x1lJ-SOSYz6kfvE4wcp9trMmidJNeA2IjxRBCbL0-Ns_T9KSI7I0zgWmiYeDBPegejdwKi6WyIULcuFxMGfsl2czSQWET-A28i2UADgvN9h8dRCe09HYkTk5ea_" width="320" alt="0music Logo" />
</p>

**0music Downloader** is a lightweight, offline music downloader built with Python, using `tkinter`, `sqlite`, and multimedia processing modules. This is a desktop application — **no browser, no authentication, no ads**. EXPERIMENTAL ONLY.

---

## 🚀 Features

- 📷 **Thumbnail Preview** - Auto-fetch and display YouTube video thumbnails
- 🎵 **Audio Preview** - Play/pause audio directly in the app using VLC
- 🔍 **Search Songs** - Filter downloaded songs by title or author
- 📝 **Auto-fill Metadata** - Automatically fetch title and author from URL
- 🎨 **Cover Art Embedding** - Download and embed album artwork into MP3 files
- 🏷️ **ID3 Tags** - Full metadata support (Title, Artist, Album, Cover Art)
- 🗃️ **SQLite Database** - Track all downloaded songs
- 🔄 **Auto Convert** - Convert to high-quality 320kbps MP3
- 📝 **Custom Title/Author** - Edit metadata before downloading

---

## ✅ Advantages

- 🔓 Bypasses Bot Protections
- ⚡ Lightweight and Fast
- ❌ No Ads
- 💡 Simple to Install & Use
- 🎧 Built-in Audio Preview
- 🖼️ Professional Album Artwork

---

## 🔧 Prerequisites

- Python 3.x
- `tkinter` (install via your package manager)
- VLC Media Player (for audio preview feature)
- FFmpeg (for audio conversion)

### macOS
```bash
brew install python-tk vlc ffmpeg
```

### Ubuntu/Debian
```bash
sudo apt install python3-tk vlc ffmpeg
```

---

## 🛠️ Installation

```bash
git clone https://github.com/rezayw/0music.git
cd 0music
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## ▶️ Run
```bash
python main.py
```

## 📦 Build & Install (macOS)

Build and automatically install to Applications folder:

```bash
./build_and_install.sh
```

This will:
- Clean previous build artifacts
- Build the macOS application bundle
- Install to `/Applications/0music.app`
- The app will save downloads to your Music app automatically

After installation, launch from:
- **Launchpad**
- **Spotlight** (⌘+Space, type "0music")
- `/Applications/0music.app`

---

## 📦 Dependencies

- `yt-dlp` - YouTube video/audio extraction
- `pillow` - Image processing
- `requests` - HTTP requests
- `mutagen` - MP3 metadata/ID3 tags
- `python-vlc` - Audio playback
