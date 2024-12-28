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

        # Use yt-dlp to extract the video title
        result = subprocess.run(
            ["yt-dlp", "--get-title", youtube_url],
            capture_output=True, text=True, check=True
        )
        video_title = result.stdout.strip()
        logging.info(f"Extracted video title: {video_title}")

        # Sanitize the video title to remove special characters
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "", video_title)

        # Create a temporary directory to store the downloaded file
        temp_dir = tempfile.mkdtemp()

        # Define the full path for the output file in the temporary directory
        output_file = os.path.join(temp_dir, f"{sanitized_title}.mp3")

        # Use yt-dlp to download the audio to the temp directory
        subprocess.run(
            ["yt-dlp", "-x", "--audio-format", "mp3", "-o", output_file, youtube_url],
            check=True
        )
        logging.info(f"Audio downloaded successfully to: {output_file}")

        # Construct the download link for the client
        download_url = f"http://127.0.0.1:5000/download/{sanitized_title}.mp3?temp_dir={temp_dir}"

        return jsonify({"success": True, "mp3Link": download_url})

    except subprocess.CalledProcessError as e:
        logging.error(f"Subprocess error: {e.stderr}")
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
