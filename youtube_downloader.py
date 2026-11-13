"""Interactive command-line YouTube downloader."""

import shutil
from pathlib import Path
from urllib.parse import urlparse

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


def is_youtube_url(value: str) -> bool:
    """Return whether value is a YouTube URL."""
    parsed = urlparse(value)
    hostname = parsed.hostname.lower() if parsed.hostname else ""
    return parsed.scheme in {"http", "https"} and (
        hostname == "youtube.com"
        or hostname.endswith(".youtube.com")
        or hostname == "youtu.be"
    )


def video_quality_options(formats: list[dict]) -> list[tuple[str, str]]:
    """Return unique video qualities and their yt-dlp selectors."""
    choices: dict[str, tuple[int, str]] = {}
    for item in formats:
        height = item.get("height")
        format_id = item.get("format_id")
        if not height or not format_id or item.get("vcodec") == "none":
            continue
        fps = item.get("fps")
        fps_label = f", {fps:g} fps" if fps else ""
        label = f"{height}p{fps_label}"
        score = int(item.get("tbr") or 0)
        current = choices.get(label)
        if current is None or score > current[0]:
            choices[label] = (score, str(format_id))

    return [
        (label, f"{format_id}+bestaudio/best")
        for label, (_score, format_id) in sorted(
            choices.items(),
            key=lambda entry: int(entry[0].split("p")[0]),
            reverse=True,
        )
    ]


def audio_quality_options(formats: list[dict]) -> list[tuple[str, str]]:
    """Return unique audio qualities and their yt-dlp selectors."""
    choices: dict[str, tuple[int, str]] = {}
    for item in formats:
        abr = item.get("abr")
        format_id = item.get("format_id")
        if not abr or not format_id or item.get("acodec") == "none":
            continue
        extension = item.get("ext", "audio")
        label = f"{round(float(abr))} kbps ({extension})"
        score = int(item.get("asr") or 0)
        current = choices.get(label)
        if current is None or score > current[0]:
            choices[label] = (score, str(format_id))

    return [
        (label, format_id)
        for label, (_score, format_id) in sorted(
            choices.items(),
            key=lambda entry: float(entry[0].split()[0]),
            reverse=True,
        )
    ]


def choose_option(options: list[tuple[str, str]], title: str) -> str:
    """Print options and return the selected format selector."""
    if not options:
        raise ValueError(f"No {title.lower()} formats were found.")

    print(f"\nAvailable {title.lower()} qualities:")
    for number, (label, _selector) in enumerate(options, start=1):
        print(f"  {number}. {label}")

    while True:
        choice = input(f"Choose {title.lower()} (1-{len(options)}): ").strip()
        try:
            index = int(choice) - 1
            if 0 <= index < len(options):
                return options[index][1]
        except ValueError:
            pass
        print("Please enter a valid option number.")


def show_progress(status: dict) -> None:
    """Display download progress."""
    if status["status"] == "downloading":
        percent = status.get("_percent_str", "").strip()
        speed = status.get("_speed_str", "").strip()
        eta = status.get("_eta_str", "").strip()
        print(f"\rDownloading: {percent} | {speed} | ETA {eta}", end="", flush=True)
    elif status["status"] == "finished":
        print("\nFinishing selected file...")


def download_video(
    url: str, output_folder: Path, format_selector: str
) -> None:
    """Download one selected format."""
    output_folder.mkdir(parents=True, exist_ok=True)
    if "+" in format_selector and not shutil.which("ffmpeg"):
        raise RuntimeError(
            "FFmpeg was not found on PATH. Install it and reopen the terminal."
        )

    options = {
        "format": format_selector,
        "merge_output_format": "mp4",
        "outtmpl": str(output_folder / "%(title)s.%(ext)s"),
        "noplaylist": True,
        "progress_hooks": [show_progress],
    }
    with YoutubeDL(options) as downloader:
        downloader.download([url])


def main() -> None:
    """Ask for a URL, media type, and quality, then download once."""
    url = input("Enter the YouTube video link: ").strip()
    if not is_youtube_url(url):
        print("Please enter a valid YouTube URL.")
        return

    try:
        with YoutubeDL({"noplaylist": True, "quiet": True}) as downloader:
            info = downloader.extract_info(url, download=False)
        formats = info.get("formats", [])

        print("\nWhat do you want to download?")
        print("  1. Video")
        print("  2. Audio")
        media_choice = input("Choose media type (1-2): ").strip()
        if media_choice == "1":
            selector = choose_option(video_quality_options(formats), "video")
        elif media_choice == "2":
            selector = choose_option(audio_quality_options(formats), "audio")
        else:
            print("Please choose 1 for video or 2 for audio.")
            return

        folder_text = input(
            "\nSave folder (press Enter for 'downloads'): "
        ).strip()
        output_folder = Path(folder_text or "downloads")
        download_video(url, output_folder, selector)
        print(f"Saved to: {output_folder.resolve()}")
    except (DownloadError, RuntimeError, ValueError) as error:
        print(f"\nDownload failed: {error}")
    except KeyboardInterrupt:
        print("\nDownload cancelled.")


if __name__ == "__main__":
    main()
