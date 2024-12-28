from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import subprocess
import os
import re
import sys
import logging
import tempfile
import shutil

app = Flask(__name__, template_folder='templates')
CORS(app)

logging.basicConfig(level=logging.INFO)

@app.route('/')
def home():
    return render_template('index.html')

# Keep other routes as they are...

@app.route('/convert', methods=['POST'])
def convert():
    try:
        youtube_url = request.form.get('url')
        if not youtube_url:
            return jsonify({"success": False, "error": "YouTube URL is required"}), 400

        logging.info(f"Received YouTube URL: {youtube_url}")

        # Create a temporary directory to store the downloaded file
        temp_dir = tempfile.mkdtemp()

        # Define the full path for the output file in the temporary directory
        output_file = os.path.join(temp_dir, "%(title)s.%(ext)s")

        # Configure yt-dlp options
        yt_dlp_opts = [
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",  # Convert to MP3
            "--no-check-certificates",  # Skip HTTPS certificate validation
            "--no-cache-dir",  # Disable cache
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "--add-header", "Accept-Language:en-US,en;q=0.9",
            "--geo-bypass",  # Bypass geo-restrictions
            "-o", output_file,  # Output template
            youtube_url  # URL to download
        ]

        # Run yt-dlp command
        subprocess.run(yt_dlp_opts, check=True)

        # Find the downloaded file
        downloaded_files = os.listdir(temp_dir)
        if not downloaded_files:
            raise Exception("No files were downloaded")

        mp3_file = os.path.join(temp_dir, downloaded_files[0])
        logging.info(f"Audio downloaded successfully to: {mp3_file}")

        # Get the filename without the temp directory path
        filename = os.path.basename(mp3_file)

        # Construct the download link
        download_url = f"/download/{filename}?temp_dir={temp_dir}"

        return jsonify({"success": True, "mp3Link": download_url})

    except subprocess.CalledProcessError as e:
        logging.error(f"yt-dlp error: {e.stderr}")
        return jsonify({"success": False, "error": f"yt-dlp error: {e.stderr}"}), 500

    except Exception as e:
        logging.error(f"General error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    try:
        temp_dir = request.args.get('temp_dir')  # Get the temp directory passed via query
        if not temp_dir or not os.path.exists(temp_dir):
            return jsonify({"success": False, "error": "Invalid or expired download directory"}), 400

        file_path = os.path.join(temp_dir, filename)

        if os.path.exists(file_path):
            logging.info(f"Serving file: {file_path}")
            response = send_file(file_path, as_attachment=True)

            # After sending the file, delete the temporary file to clean up
            os.remove(file_path)
            # Optionally remove the temp directory after file is downloaded
            if not os.listdir(temp_dir):  # Check if the temp directory is empty
                os.rmdir(temp_dir)

            return response
        else:
            logging.error(f"File not found: {file_path}")
            return jsonify({"success": False, "error": "File not found"}), 404

    except Exception as e:
        logging.error(f"Error in downloading file: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
