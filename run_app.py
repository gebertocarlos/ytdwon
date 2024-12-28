import os
import subprocess
import webbrowser
import time
from threading import Thread

# Function to run the Flask app in a separate thread
def run_flask_app():
    try:
        subprocess.run(["python", "server.py"])
    except Exception as e:
        print(f"Error starting Flask app: {e}")

# Function to open the frontend in the default web browser
def open_browser():
    # Wait a bit to make sure the Flask app starts before opening the browser
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # Create a thread for running the Flask app
    flask_thread = Thread(target=run_flask_app)
    flask_thread.start()

    # Open the browser
    open_browser()
