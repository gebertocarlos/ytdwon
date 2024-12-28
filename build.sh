#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install system dependencies for yt-dlp
apt-get update
apt-get install -y ffmpeg python3-pip

# Install Python dependencies
pip install -r requirements.txt