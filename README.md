# Universal Video Downloader

A lightweight, local web application that allows you to download videos and audio from YouTube and hundreds of other supported sites at maximum resolution. It uses a Flask backend and `yt-dlp` to fetch and merge high-quality video and audio streams.

## Features
- **High Resolution Downloads**: Supports downloading up to 4K resolution (or whatever maximum resolution the video provides).
- **Audio Only Extraction**: Option to download high-quality MP3 audio directly.
- **PWA Support**: Can be installed as a Progressive Web App (PWA) on your mobile device or desktop if hosted on a local network.
- **Bot Bypass Ready**: Built-in support for passing authentication cookies to bypass YouTube's aggressive bot-detection blocks.
- **Auto-Muxing**: Automatically uses FFmpeg to merge separated high-quality video and audio streams into a clean, unified MP4 file.

## Prerequisites
- Python 3.8 or higher
- The script automatically downloads the necessary `ffmpeg` binaries via `imageio-ffmpeg`, so you do not need to install FFmpeg globally on your system.

## Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sheikhabibi/all-video-downloader.git
   cd all-video-downloader
   ```

2. **Create a virtual environment (Recommended):**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Start the Flask server:
   ```bash
   python app.py
   ```
2. Open your web browser and go to `http://localhost:5000`.
3. Paste a YouTube URL into the input field and click "Get Options".
4. Select your desired resolution and click "Download".

## Important: Bypassing YouTube's Bot Block
If you encounter an error stating **"Sign in to confirm you're not a bot"**, YouTube is blocking the download request. To fix this, you must provide your browser cookies to authenticate the request.

1. Install a "Get cookies.txt" extension on your web browser.
2. Go to youtube.com and **play a video**.
3. While the video is playing, click the extension and export your cookies in Netscape format.
4. Save the file exactly as `cookies.txt` in the root directory of this project (next to `app.py`).
5. The application will automatically detect this file and use it to bypass the block!

## Technical Notes
- **Cloud Hosting**: Attempting to host this application on a free cloud provider (like Render, Heroku, etc.) will likely result in permanent YouTube blocks. YouTube actively flags datacenter IP addresses. It is highly recommended to run this application locally.
- **Temporary Files**: Downloads are processed in your system's temporary directory. Intermediate stream files (like `.f398` and `.f251`) are automatically merged and cleaned up.
