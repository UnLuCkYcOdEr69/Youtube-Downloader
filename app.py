import os
import re
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)

DOWNLOAD_FOLDER = "downloads"
COOKIES_FILE = "cookies.txt"

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# ===============================
# Create cookies.txt from ENV (Render)
# ===============================
if not os.path.exists(COOKIES_FILE):
    cookies = os.environ.get("YT_COOKIES")
    if cookies:
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(cookies)

# ===============================
# Helpers
# ===============================
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# ===============================
# Routes
# ===============================
@app.route("/")
def index():
    return render_template("index.html")

# ===============================
# VIDEO DOWNLOAD (MP4 + AUDIO)
# ===============================
@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {
            "format": "bv*+ba/b",
            "merge_output_format": "mp4",
            "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
            "cookies": COOKIES_FILE,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            },
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            final_file = filename.rsplit(".", 1)[0] + ".mp4"

        return send_file(final_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===============================
# AUDIO DOWNLOAD (MP3)
# ===============================
@app.route("/download_audio", methods=["POST"])
def download_audio():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{DOWNLOAD_FOLDER}/%(title)s.%(ext)s",
            "cookies": COOKIES_FILE,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android"]
                }
            },
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            final_file = filename.rsplit(".", 1)[0] + ".mp3"

        return send_file(final_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ===============================
# Run App
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
