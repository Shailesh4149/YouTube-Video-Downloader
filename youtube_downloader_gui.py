"""Graphical YouTube downloader with selectable media type and quality."""

import queue
import shutil
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
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


class DownloaderApp:
    """Tkinter application for downloading selected YouTube formats."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Streamline | YouTube Downloader")
        self.root.resizable(True, True)
        self.root.minsize(720, 680)
        self.root.state("zoomed")
        self.messages: queue.Queue[tuple[str, object]] = queue.Queue()
        self.video_formats: dict[str, str] = {}
        self.audio_formats: dict[str, str] = {}

        self.url = tk.StringVar()
        self.output_folder = tk.StringVar(
            value=str(Path.cwd() / "downloads")
        )
        self.media_type = tk.StringVar(value="Video")
        self.quality = tk.StringVar()
        self.status = tk.StringVar(value="Paste a YouTube link, then load qualities.")
        self.progress = tk.DoubleVar()

        self._configure_theme()
        self._build_ui()
        self.root.after(100, self._process_messages)

    def _configure_theme(self) -> None:
        self.root.configure(bg="#0b1220")
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("App.TFrame", background="#0b1220")
        style.configure("Card.TFrame", background="#111c2f",
                        relief="solid", borderwidth=1)
        style.configure(
            "Title.TLabel",
            background="#0b1220",
            foreground="#f8fafc",
            font=("Segoe UI Semibold", 23),
        )
        style.configure(
            "Subtitle.TLabel",
            background="#0b1220",
            foreground="#94a3b8",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Card.TLabel",
            background="#111c2f",
            foreground="#e2e8f0",
            font=("Segoe UI Semibold", 10),
        )
        style.configure(
            "Hint.TLabel",
            background="#111c2f",
            foreground="#64748b",
            font=("Segoe UI", 9),
        )
        style.configure("Section.TLabel", background="#111c2f",
                        foreground="#60a5fa",
                        font=("Segoe UI Semibold", 9))
        style.configure("Status.TLabel", background="#17263d",
                        foreground="#bfdbfe", font=("Segoe UI", 9),
                        padding=(10, 8))
        style.configure(
            "Accent.TButton",
            background="#3b82f6",
            foreground="#ffffff",
            font=("Segoe UI Semibold", 10),
            padding=(14, 10),
        )
        style.map(
            "Accent.TButton",
            background=[("active", "#60a5fa"), ("disabled", "#334155")],
        )
        style.configure("TButton", background="#1e293b",
                        foreground="#dbeafe", font=("Segoe UI", 9),
                        padding=(10, 7))
        style.map("TButton",
                  background=[("active", "#334155"), ("disabled", "#172033")],
                  foreground=[("disabled", "#64748b")])
        style.configure("TEntry", fieldbackground="#0f172a",
                        foreground="#f8fafc", insertcolor="#f8fafc",
                        bordercolor="#334155", lightcolor="#334155",
                        darkcolor="#334155", padding=8)
        style.configure("TCombobox", fieldbackground="#0f172a",
                        foreground="#f8fafc", padding=7)
        style.map("TCombobox",
                  fieldbackground=[("readonly", "#0f172a")],
                  foreground=[("readonly", "#f8fafc")])
        style.configure(
            "Horizontal.TProgressbar",
            background="#38bdf8",
            troughcolor="#1e293b",
            bordercolor="#1e293b",
            lightcolor="#38bdf8",
            darkcolor="#38bdf8",
        )

    def _build_ui(self) -> None:
        frame = ttk.Frame(self.root, padding=(28, 24), style="App.TFrame")
        frame.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        ttk.Label(frame, text="YouTube Downloader", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            frame,
            text="Fast, focused downloads with complete quality control.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(3, 18))

        card = ttk.Frame(frame, padding=20, style="Card.TFrame")
        card.grid(row=2, column=0, sticky="ew")
        card.columnconfigure(0, weight=1)

        ttk.Label(card, text="SOURCE", style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        url_entry = ttk.Entry(card, textvariable=self.url, width=68)
        url_entry.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(5, 8))
        ttk.Button(card, text="Paste", command=self._paste_url).grid(
            row=2, column=0, sticky="w"
        )
        ttk.Button(card, text="Clear", command=self._clear_url).grid(
            row=2, column=1, sticky="w", padx=(8, 0)
        )

        ttk.Label(card, text="FORMAT & QUALITY", style="Section.TLabel").grid(
            row=3, column=0, sticky="w", pady=(18, 0)
        )
        self.type_box = ttk.Combobox(
            card,
            textvariable=self.media_type,
            values=("Video", "Audio"),
            state="readonly",
            width=18,
        )
        self.type_box.grid(row=4, column=0, sticky="w", pady=(5, 14))
        self.type_box.bind("<<ComboboxSelected>>", self._change_media_type)

        self.load_button = ttk.Button(
            card, text="Load qualities", command=self._load_qualities
        )
        self.load_button.grid(row=4, column=2, sticky="e", pady=(5, 14))

        ttk.Label(card, text="Quality", style="Card.TLabel").grid(
            row=5, column=0, sticky="w"
        )
        self.quality_box = ttk.Combobox(
            card, textvariable=self.quality, state="readonly", width=58
        )
        self.quality_box.grid(
            row=6, column=0, columnspan=3, sticky="ew", pady=(5, 14)
        )

        ttk.Label(card, text="DESTINATION", style="Section.TLabel").grid(
            row=7, column=0, sticky="w"
        )
        ttk.Entry(card, textvariable=self.output_folder, width=55).grid(
            row=8, column=0, columnspan=2, sticky="ew", pady=(5, 14)
        )
        ttk.Button(
            card, text="Browse...", command=self._choose_folder
        ).grid(row=8, column=2, padx=(8, 0), pady=(5, 14))

        self.download_button = ttk.Button(
            card, text="Download selected quality",
            command=self._start_download,
            style="Accent.TButton",
        )
        self.download_button.grid(
            row=9, column=0, columnspan=3, sticky="ew", pady=(2, 8)
        )

        ttk.Progressbar(
            card, variable=self.progress, maximum=100, length=500,
            style="Horizontal.TProgressbar",
        ).grid(row=10, column=0, columnspan=3, sticky="ew", pady=(8, 6))
        ttk.Label(card, textvariable=self.status, wraplength=500,
                  style="Status.TLabel").grid(
            row=11, column=0, columnspan=3, sticky="w"
        )
        ttk.Label(
            card,
            text="High-resolution video uses FFmpeg to merge separate streams.",
            style="Hint.TLabel",
        ).grid(row=12, column=0, columnspan=3, sticky="w", pady=(12, 0))

        self.new_button = ttk.Button(
            frame, text="New download", command=self._new_download
        )
        self.new_button.grid(row=3, column=0, sticky="w", pady=(14, 0))

        footer = ttk.Frame(frame, style="App.TFrame")
        footer.grid(row=4, column=0, sticky="ew", pady=(18, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(
            footer,
            text="STREAMLINE  •  v1.0",
            style="Subtitle.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            footer,
            text="Powered by yt-dlp  •  FFmpeg",
            style="Subtitle.TLabel",
        ).grid(row=0, column=1, sticky="e")
        ttk.Label(
            footer,
            text="Download only content you have permission to use.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        self.root.bind("<Control-l>", lambda _event: self._load_qualities())
        self.root.bind("<Control-n>", lambda _event: self._new_download())
        self.root.bind("<Return>", lambda _event: self._start_download())
        url_entry.focus_set()

    def _paste_url(self) -> None:
        try:
            self.url.set(self.root.clipboard_get().strip())
            self.status.set("Link pasted. Load qualities to continue.")
        except tk.TclError:
            messagebox.showwarning("Clipboard empty", "No text was found in the clipboard.")

    def _clear_url(self) -> None:
        self.url.set("")
        self.quality.set("")
        self.video_formats.clear()
        self.audio_formats.clear()
        self.quality_box["values"] = ()
        self.status.set("Paste a YouTube link, then load qualities.")

    def _new_download(self) -> None:
        self._clear_url()
        self.progress.set(0)
        self.status.set("Ready for the next video.")

    def _choose_folder(self) -> None:
        folder = filedialog.askdirectory(
            title="Choose download folder",
            initialdir=self.output_folder.get(),
        )
        if folder:
            self.output_folder.set(folder)

    def _change_media_type(self, _event: object = None) -> None:
        formats = self.video_formats if self.media_type.get() == "Video" else self.audio_formats
        self.quality_box["values"] = tuple(formats)
        self.quality.set("")

    def _load_qualities(self) -> None:
        url = self.url.get().strip()
        if not is_youtube_url(url):
            messagebox.showerror("Invalid link", "Enter a valid YouTube URL.")
            return

        self._set_busy(True)
        self.status.set("Reading available qualities...")
        threading.Thread(
            target=self._extract_formats, args=(url,), daemon=True
        ).start()

    def _extract_formats(self, url: str) -> None:
        try:
            options = {"noplaylist": True, "quiet": True, "no_warnings": True}
            with YoutubeDL(options) as downloader:
                info = downloader.extract_info(url, download=False)
            video_formats = self._video_quality_options(info.get("formats", []))
            audio_formats = self._audio_quality_options(info.get("formats", []))
            self.messages.put(("formats", (video_formats, audio_formats)))
        except (DownloadError, KeyError, TypeError, ValueError) as error:
            self.messages.put(("error", f"Could not load qualities: {error}"))

    @staticmethod
    def _video_quality_options(formats: list[dict]) -> dict[str, str]:
        choices: dict[str, tuple[int, str]] = {}
        for item in formats:
            height = item.get("height")
            format_id = item.get("format_id")
            if not height or not format_id or item.get("vcodec") == "none":
                continue
            label = f"{height}p"
            if item.get("fps"):
                fps = float(item["fps"])
                label += f" ({int(fps) if fps.is_integer() else fps} fps)"
            current = choices.get(label)
            score = int(item.get("tbr") or 0)
            if current is None or score > current[0]:
                choices[label] = (score, str(format_id))

        return {
            label: f"{format_id}+bestaudio/best"
            for label, (_score, format_id) in sorted(
                choices.items(), key=lambda entry: int(entry[0].split("p")[0]),
                reverse=True,
            )
        }

    @staticmethod
    def _audio_quality_options(formats: list[dict]) -> dict[str, str]:
        choices: dict[str, tuple[int, str]] = {}
        for item in formats:
            abr = item.get("abr")
            format_id = item.get("format_id")
            if not abr or not format_id or item.get("acodec") == "none":
                continue
            extension = item.get("ext", "audio")
            label = f"{round(float(abr))} kbps ({extension})"
            current = choices.get(label)
            score = int(item.get("asr") or 0)
            if current is None or score > current[0]:
                choices[label] = (score, str(format_id))

        return {
            label: format_id
            for label, (_score, format_id) in sorted(
                choices.items(),
                key=lambda entry: float(entry[0].split()[0]),
                reverse=True,
            )
        }

    def _start_download(self) -> None:
        url = self.url.get().strip()
        folder = self.output_folder.get().strip()
        selected = self.quality.get()
        formats = self.video_formats if self.media_type.get() == "Video" else self.audio_formats
        format_selector = formats.get(selected)

        if not format_selector:
            messagebox.showerror(
                "Choose quality", "Load qualities and select one first."
            )
            return
        if not folder:
            messagebox.showerror("Missing folder", "Choose a save folder.")
            return

        self._set_busy(True)
        self.progress.set(0)
        self.status.set("Starting one download job...")
        threading.Thread(
            target=self._download,
            args=(url, Path(folder), format_selector),
            daemon=True,
        ).start()

    def _download(
        self, url: str, output_folder: Path, format_selector: str
    ) -> None:
        try:
            output_folder.mkdir(parents=True, exist_ok=True)
            if "+" in format_selector and not shutil.which("ffmpeg"):
                raise RuntimeError(
                    "FFmpeg was not found on PATH. Open a new terminal "
                    "after installing FFmpeg and try again."
                )

            options = {
                "format": format_selector,
                "merge_output_format": "mp4",
                "outtmpl": str(output_folder / "%(title)s.%(ext)s"),
                "noplaylist": True,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self._progress_hook],
            }
            with YoutubeDL(options) as downloader:
                downloader.download([url])
            self.messages.put(("complete", str(output_folder.resolve())))
        except (DownloadError, RuntimeError) as error:
            self.messages.put(("error", str(error)))

    def _progress_hook(self, data: dict) -> None:
        if data["status"] == "downloading":
            downloaded = data.get("downloaded_bytes", 0)
            total = data.get("total_bytes") or data.get("total_bytes_estimate")
            if total:
                self.messages.put(("progress", downloaded / total * 100))
        elif data["status"] == "finished":
            self.messages.put(("status", "Finishing selected file..."))

    def _set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.download_button.configure(state=state)
        self.load_button.configure(state=state)
        self.new_button.configure(state=state)
        self.type_box.configure(state="disabled" if busy else "readonly")

    def _process_messages(self) -> None:
        try:
            while True:
                message_type, value = self.messages.get_nowait()
                if message_type == "formats":
                    self.video_formats, self.audio_formats = value
                    self._change_media_type()
                    self._set_busy(False)
                    self.status.set("Select a quality and start the download.")
                elif message_type == "progress":
                    percent = float(value)
                    self.progress.set(percent)
                    self.status.set(f"Downloading: {percent:.1f}%")
                elif message_type == "status":
                    self.status.set(str(value))
                elif message_type == "complete":
                    self.progress.set(100)
                    self.status.set(f"Saved to: {value}")
                    self._set_busy(False)
                    messagebox.showinfo("Complete", f"File saved to:\n{value}")
                elif message_type == "error":
                    self.status.set("Operation failed.")
                    self._set_busy(False)
                    messagebox.showerror("Download failed", str(value))
        except queue.Empty:
            pass
        self.root.after(100, self._process_messages)


def main() -> None:
    root = tk.Tk()
    DownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
