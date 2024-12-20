#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install ffmpeg
curl -O 'https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz'
tar xvf ffmpeg-git-amd64-static.tar.xz
cp ffmpeg-git-*/ffmpeg /usr/local/bin/
cp ffmpeg-git-*/ffprobe /usr/local/bin/

# Install Python dependencies
pip install -r requirements.txt