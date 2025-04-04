import os
import re
import subprocess
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

def sanitize_filename(title):
    """Remove invalid characters from filenames"""
    return re.sub(r'[\\/*?:"<>|]', "", title)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        sanitized_title = sanitize_filename(url.split("=")[-1])  
        final_path = os.path.join(DOWNLOAD_FOLDER, f"{sanitized_title}.mp4")

        ydl_opts = {
            "outtmpl": final_path.replace(".mp4", ".%(ext)s"),  
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best",  # Ensure correct video & audio format
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4",  # Convert & merge into MP4
                }
            ],
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(final_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/download_audio", methods=["POST"])
def download_audio():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        sanitized_title = sanitize_filename(url.split("=")[-1])
        final_path = os.path.join(DOWNLOAD_FOLDER, f"{sanitized_title}.mp3")

        ydl_opts = {
            "outtmpl": final_path.replace(".mp3", ".%(ext)s"),  
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file(final_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
