#YouTube Video Downloader

A modern, sleek, and high-performance YouTube video downloader built in Python using **CustomTkinter** for the user interface and **yt-dlp** as the extraction engine.

## Features
- **Sleek UI**: Premium dark mode first interface with custom accents, rounded corners, and animations.
- **Asynchronous Execution**: Details fetching and media downloading run on background threads, keeping the GUI smooth and responsive at all times.
- **Rich Previews**: Downloads and renders video thumbnails, durations, views, and channel information.
- **Format Flexibility**: Separates downloads into combined formats, video-only files, or audio-only files.
- **Smart Fallback**: Handles cases where `ffmpeg` is missing by offering high-quality pre-merged streams (typically up to 720p) and clear prompts on how to unlock HD resolutions.
- **Action Buttons**: Directly play the downloaded file or open its containing folder in File Explorer once finished.

---

## How to Set Up and Run

### 1. Prerequisites
Ensure you have **Python 3.8+** installed. You can check your version by running:
```bash
python --version
```

### 2. Install Dependencies
Install all required libraries from the terminal using `pip`:
```bash
pip install -r requirements.txt
```

### 3. Run the Application
Start the downloader by running:
```bash
python app.py
```

---

## Unlocking Full HD Merging (Optional)

YouTube distributes high-definition media (1080p, 1440p, 4K) as separate video-only and audio-only streams. To download and automatically merge these into a single playable MP4 file, this app requires **FFmpeg** on your system.

### How to Install FFmpeg on Windows:
1. Open PowerShell or Command Prompt as **Administrator**.
2. Run the command:
   ```powershell
   winget install GnuWin32.FFmpeg
   ```
3. Close the terminal, restart this application, and you'll see **"FFmpeg Status: Detected (Full HD Unlocked)"** in the left sidebar!
