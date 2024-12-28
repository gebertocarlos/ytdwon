#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Download and install ffmpeg binary
mkdir -p bin
curl -L https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz -o ffmpeg.tar.xz
tar xf ffmpeg.tar.xz
mv ffmpeg-master-latest-linux64-gpl/bin/ffmpeg bin/
mv ffmpeg-master-latest-linux64-gpl/bin/ffprobe bin/
rm -rf ffmpeg-master-latest-linux64-gpl ffmpeg.tar.xz

# Add bin to PATH
export PATH="$PATH:$PWD/bin"