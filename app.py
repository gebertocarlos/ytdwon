from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import os
import re
import logging
import tempfile
import shutil
from threading import Timer
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Youtube-dl options
YT_DLP_OPTIONS = [
    '--no-check-certificates',
    '--no-warnings',
    '--extract-audio',
    '--audio-format', 'mp3',
    '--audio-quality', '0',
    '--prefer-ffmpeg',
    '--no-playlist',
]

# Store temporary file mappings
temp_files = {}

@app.route('/')
def home():
    return jsonify({"status": "healthy", "message": "Service is running"}), 200

@app.route('/convert', methods=['POST'])
def convert():
    try:
        youtube_url = request.form.get('url')
        if not youtube_url:
            return jsonify({"success": False, "error": "YouTube URL is required"}), 400
        
        logger.info(f"Received YouTube URL: {youtube_url}")

        # Validate YouTube URL
        if not re.match(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$', youtube_url):
            return jsonify({"success": False, "error": "Invalid YouTube URL"}), 400

        # Create a temporary directory
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Get video title
            result = subprocess.run(
                ["yt-dlp", "--get-title"] + YT_DLP_OPTIONS + [youtube_url],
                capture_output=True,
                text=True,
                check=True
            )
            video_title = result.stdout.strip()
            logger.info(f"Extracted video title: {video_title}")

            # Sanitize the title
            sanitized_title = secure_filename(video_title)
            if not sanitized_title:
                sanitized_title = "audio"

            # Define output file path
            output_file = os.path.join(temp_dir, f"{sanitized_title}.mp3")

            # Download and convert
            subprocess.run(
                ["yt-dlp"] + YT_DLP_OPTIONS + ["-o", output_file, youtube_url],
                check=True,
                capture_output=True,
                text=True
            )

            logger.info(f"Audio downloaded successfully to: {output_file}")

            # Store the file mapping
            file_id = secure_filename(f"{sanitized_title}_{os.urandom(4).hex()}")
            temp_files[file_id] = {
                'path': output_file,
                'temp_dir': temp_dir,
                'title': sanitized_title
            }

            # Return the download URL
            download_url = f"/download/{file_id}"
            return jsonify({
                "success": True,
                "mp3Link": download_url,
                "title": video_title
            })

        except subprocess.CalledProcessError as e:
            logger.error(f"yt-dlp error: {e.stderr}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            if "Sign in to confirm you're not a bot" in str(e.stderr):
                return jsonify({
                    "success": False,
                    "error": "Service temporarily unavailable. Please try again later."
                }), 429
            
            return jsonify({
                "success": False,
                "error": "Failed to process video. Please try another URL."
            }), 500

    except Exception as e:
        logger.error(f"General error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "An unexpected error occurred"
        }), 500

@app.route('/download/<file_id>', methods=['GET'])
def download_file(file_id):
    try:
        if file_id not in temp_files:
            return jsonify({
                "success": False,
                "error": "Invalid or expired download link"
            }), 404

        file_info = temp_files[file_id]
        file_path = file_info['path']
        temp_dir = file_info['temp_dir']
        title = file_info['title']

        if not os.path.exists(file_path):
            return jsonify({
                "success": False,
                "error": "File not found"
            }), 404

        try:
            return send_file(
                file_path,
                as_attachment=True,
                download_name=f"{title}.mp3"
            )
        finally:
            # Clean up after sending the file
            try:
                del temp_files[file_id]
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Failed to download file"
        }), 500

# Cleanup function for expired files
def cleanup_temp_files():
    for file_id in list(temp_files.keys()):
        try:
            info = temp_files[file_id]
            shutil.rmtree(info['temp_dir'], ignore_errors=True)
            del temp_files[file_id]
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")

# Schedule cleanup every hour
def schedule_cleanup():
    cleanup_temp_files()
    Timer(3600, schedule_cleanup).start()

# Start cleanup scheduler
schedule_cleanup()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
