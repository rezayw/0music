#!/bin/bash

# Build and Install Script for 0music
# This script builds the app and installs it to /Applications/

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
fi

# Ensure pyinstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing pyinstaller..."
    pip install pyinstaller
fi

echo "🧹 Cleaning old build artifacts..."
rm -rf build dist 0music.spec

echo "🔨 Building 0music.app..."
pyinstaller --name="0music" \
  --windowed \
  --icon="0music.icns" \
  --add-data="assets:assets" \
  --add-binary="bin/ffmpeg:bin" \
  --add-binary="bin/ffprobe:bin" \
  --hidden-import="PIL._tkinter_finder" \
  --hidden-import="tkinter" \
  --hidden-import="tkinter.ttk" \
  --hidden-import="vlc" \
  --hidden-import="mutagen" \
  --hidden-import="yt_dlp" \
  --collect-all="yt_dlp" \
  main.py

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"

    echo "📦 Installing to /Applications/..."
    # Remove old version if exists
    if [ -d "/Applications/0music.app" ]; then
        echo "🗑️  Removing old version..."
        rm -rf /Applications/0music.app
    fi

    # Copy new version
    cp -R dist/0music.app /Applications/

    echo "✅ Installation complete!"
    echo "🚀 0music.app is now in your Applications folder"
    echo ""
    echo "You can launch it from:"
    echo "  - Launchpad"
    echo "  - Spotlight (Cmd+Space, type '0music')"
    echo "  - /Applications/0music.app"
else
    echo "❌ Build failed!"
    exit 1
fi
