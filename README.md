# Streamline YouTube Downloader

A Windows desktop downloader built with Python, Tkinter, and `yt-dlp`. It
supports selecting video or audio and choosing from the qualities available
for a YouTube URL.

## Features

- Modern maximized GUI
- Video or audio download mode
- Loads available quality options before downloading
- Selectable video resolution and audio bitrate
- Automatic video/audio merging through FFmpeg
- Download progress display
- Custom output folder
- Paste, clear, and new-download controls
- Command-line version included

## Requirements

- Windows 10 or later
- Python 3.10 or later
- FFmpeg
- Deno JavaScript runtime


## Installation

Open Command Prompt and run:

```bat
cd /d C:\Users\shail\Desktop\Downloader
python -m pip install -r requirements.txt
```

Install FFmpeg and Deno with Windows Package Manager:

```bat
winget install --id Gyan.FFmpeg.Shared -e
winget install --id DenoLand.Deno -e
```

Close and reopen Command Prompt after installing them so the updated PATH is
loaded. Verify the installations:

```bat
ffmpeg -version
deno --version
python -m yt_dlp --version
```

## Start the GUI

```bat
cd /d C:\Users\shail\Desktop\Downloader
python youtube_downloader_gui.py
```

### GUI workflow

1. Paste a YouTube URL, or use the **Paste** button.
2. Select **Video** or **Audio**.
3. Click **Load qualities**.
4. Select the desired quality.
5. Choose an output folder, if needed.
6. Click **Download selected quality**.
7. Use **New download** for another video.

The GUI downloads one final file per operation. For high-resolution video,
`yt-dlp` may download separate video and audio streams internally; FFmpeg
automatically merges them into the final file.

## Start the command-line version

```bat

python youtube_downloader.py
```

The CLI asks for:

1. A YouTube URL
2. Video or audio
3. An available video resolution or audio bitrate
4. An output folder

It downloads one selected final file. For high-resolution video, FFmpeg
automatically merges separate video and audio streams.

## Troubleshooting

### `requirements.txt` not found

Run the command from the project directory:

```bat

python -m pip install -r requirements.txt
```

### FFmpeg was not found

Install FFmpeg, close the current terminal, open a new one, and verify:

```bat
ffmpeg -version
```

FFmpeg is required when the selected video quality uses separate video and
audio streams.

### JavaScript runtime warning or HTTP 403

Update `yt-dlp`, install Deno, and restart Command Prompt:

```bat
python -m pip install --upgrade yt-dlp
winget install --id DenoLand.Deno -e
```

### The GUI does not show the latest changes

Close the old GUI window and start it again:

```bat
python youtube_downloader_gui.py
```

## Project files

- [youtube_downloader_gui.py](./youtube_downloader_gui.py): graphical
  downloader
- [youtube_downloader.py](./youtube_downloader.py): command-line downloader
- [requirements.txt](./requirements.txt): Python dependency list

## Responsible use

Download only content that you own or have permission to download. Follow
YouTube's Terms of Service and applicable copyright laws.
