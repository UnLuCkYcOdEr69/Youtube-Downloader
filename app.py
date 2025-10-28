import os
import re
import uuid
import logging
from flask import Flask, render_template, request, send_file, jsonify, redirect, url_for, flash
import yt_dlp

# ----- Configuration -----
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "replace-this-secret")
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# logging (useful on Render)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- Helpers -----
def sanitize_filename(name: str) -> str:
    """Remove characters that are invalid for file names and trim."""
    if not name:
        return str(uuid.uuid4())
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.strip()
    return name or str(uuid.uuid4())

def find_downloaded_file(prefix: str) -> str | None:
    """Find a file in DOWNLOAD_FOLDER that starts with prefix."""
    for fname in os.listdir(DOWNLOAD_FOLDER):
        if fname.startswith(prefix + ".") or fname.startswith(prefix + "_"):
            return os.path.join(DOWNLOAD_FOLDER, fname)
    return None

# ----- Routes -----
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/download", methods=["POST"])
def download_video():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # Prepare unique prefix (avoid collisions). We'll name files as <prefix>.<ext>
    unique_prefix = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"{unique_prefix}.%(ext)s")

    # Option 2: use extractor_args to mimic browser clients
    extractor_args = {"youtube": {"player_client": ["android", "web"]}}

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestvideo+bestaudio/best",  # get best combined (will merge)
        "merge_output_format": "mp4",
        "extractor_args": extractor_args,
        "retries": 5,
        "nopart": True,   # avoid .part files
        "quiet": False,   # allow logging in server logs (set True to silence)
    }

    logger.info("Download (video) requested: %s", url)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Determine the actual downloaded file
        filepath = find_downloaded_file(unique_prefix)
        if not filepath:
            # fallback: try to construct using title if available
            title = sanitize_filename(info.get("title", unique_prefix))
            fallback = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp4")
            if os.path.exists(fallback):
                filepath = fallback

        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError("Downloaded file not found after yt-dlp finished.")

        safe_title = sanitize_filename(info.get("title", unique_prefix))
        download_name = f"{safe_title}.mp4"
        logger.info("Sending file %s as %s", filepath, download_name)
        return send_file(filepath, as_attachment=True, download_name=download_name)

    except Exception as e:
        logger.exception("Video download failed")
        return jsonify({"error": str(e)}), 500


@app.route("/download_audio", methods=["POST"])
def download_audio():
    url = request.form.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    unique_prefix = str(uuid.uuid4())
    outtmpl = os.path.join(DOWNLOAD_FOLDER, f"{unique_prefix}.%(ext)s")

    extractor_args = {"youtube": {"player_client": ["android", "web"]}}

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best",
        "extractor_args": extractor_args,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "retries": 5,
        "nopart": True,
        "quiet": False,
    }

    logger.info("Download (audio) requested: %s", url)
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        filepath = find_downloaded_file(unique_prefix)
        if not filepath:
            # fallback to title-based filename
            title = sanitize_filename(info.get("title", unique_prefix))
            fallback = os.path.join(DOWNLOAD_FOLDER, f"{title}.mp3")
            if os.path.exists(fallback):
                filepath = fallback

        if not filepath or not os.path.exists(filepath):
            raise FileNotFoundError("Downloaded audio file not found after yt-dlp finished.")

        safe_title = sanitize_filename(info.get("title", unique_prefix))
        download_name = f"{safe_title}.mp3"
        logger.info("Sending file %s as %s", filepath, download_name)
        return send_file(filepath, as_attachment=True, download_name=download_name)

    except Exception as e:
        logger.exception("Audio download failed")
        return jsonify({"error": str(e)}), 500


# ----- Run server (local debug) -----
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
