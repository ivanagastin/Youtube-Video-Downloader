import os
import io
import urllib.request
import threading
import sys
import webbrowser
from PIL import Image
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Import the downloader logic
from downloader import YouTubeDownloader, is_ffmpeg_available

# Set window theme and colors
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Theme colors
COLOR_ACCENT = "#6366F1"  # Modern Indigo
COLOR_ACCENT_HOVER = "#4F46E5"
COLOR_SUCCESS = "#10B981"  # Emerald Green
COLOR_WARNING = "#F59E0B"  # Amber
COLOR_DANGER = "#EF4444"   # Rose
COLOR_BG_CARD = "#2D3035"

class YTDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Downloader engine
        self.downloader = YouTubeDownloader()
        self.current_video_info = None
        self.thumbnail_pil = None

        # Window Settings
        self.title("Antigravity YouTube Downloader")
        self.geometry("820x650")
        self.minsize(820, 650)
        
        # Configure Grid Layout (1 row, 2 columns - Sidebar & Main Content)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create GUI Components
        self.create_sidebar()
        self.create_main_content()

        # Set default download path to user's Downloads folder
        default_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        if not os.path.exists(default_path):
            default_path = os.getcwd()
        self.download_path_var.set(default_path)

        # Check FFmpeg on startup
        self.check_ffmpeg_status()

    def create_sidebar(self):
        """Creates the left sidebar for settings and utility links."""
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        # Title/Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Antigravity\nDownloader", 
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=COLOR_ACCENT
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Save Directory Title
        self.save_lbl = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Save Location:", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.save_lbl.grid(row=1, column=0, padx=20, pady=(10, 5), sticky="w")

        # Save Directory Path Input
        self.download_path_var = ctk.StringVar()
        self.path_entry = ctk.CTkEntry(
            self.sidebar_frame, 
            textvariable=self.download_path_var,
            width=180,
            state="readonly"
        )
        self.path_entry.grid(row=2, column=0, padx=20, pady=5)

        # Browse Button
        self.browse_btn = ctk.CTkButton(
            self.sidebar_frame, 
            text="Browse Folder", 
            command=self.browse_folder,
            fg_color="transparent",
            border_width=1,
            border_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER
        )
        self.browse_btn.grid(row=3, column=0, padx=20, pady=(5, 20))

        # Divider
        self.sidebar_sep = ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="gray30")
        self.sidebar_sep.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        # FFmpeg Status Card
        self.ffmpeg_card = ctk.CTkFrame(self.sidebar_frame, fg_color="#232529", corner_radius=8)
        self.ffmpeg_card.grid(row=5, column=0, padx=15, pady=15, sticky="ew")
        
        self.ffmpeg_lbl = ctk.CTkLabel(
            self.ffmpeg_card, 
            text="FFmpeg Status", 
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold")
        )
        self.ffmpeg_lbl.pack(padx=10, pady=(8, 2), anchor="w")

        self.ffmpeg_status_val = ctk.CTkLabel(
            self.ffmpeg_card, 
            text="Checking...", 
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="gray"
        )
        self.ffmpeg_status_val.pack(padx=10, pady=(0, 8), anchor="w")

        self.ffmpeg_help_btn = ctk.CTkButton(
            self.ffmpeg_card, 
            text="How to install FFmpeg?", 
            font=ctk.CTkFont(family="Segoe UI", size=10, underline=True),
            text_color=COLOR_ACCENT,
            fg_color="#232529",
            hover_color="#2D3035",
            width=120,
            height=20,
            command=self.show_ffmpeg_help
        )
        self.ffmpeg_help_btn.pack(padx=10, pady=(0, 8), anchor="w")

        # Appearance Settings (Theme switcher)
        self.appearance_lbl = ctk.CTkLabel(self.sidebar_frame, text="Theme Mode:", anchor="w")
        self.appearance_lbl.grid(row=7, column=0, padx=20, pady=(10, 0), sticky="w")
        
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(
            self.sidebar_frame, 
            values=["Dark", "Light", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(5, 20))

    def create_main_content(self):
        """Creates the main panel containing the URL inputs, metadata preview, and progress outputs."""
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Header Title
        self.header_title = ctk.CTkLabel(
            self.main_frame, 
            text="Download YouTube Media", 
            font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"),
            anchor="w"
        )
        self.header_title.grid(row=0, column=0, sticky="w", pady=(10, 5))

        self.header_desc = ctk.CTkLabel(
            self.main_frame, 
            text="Enter a YouTube Video, Shorts, or Audio link to download in multiple resolutions and formats.", 
            text_color="gray", 
            font=ctk.CTkFont(family="Segoe UI", size=13),
            anchor="w",
            wraplength=550
        )
        self.header_desc.grid(row=1, column=0, sticky="w", pady=(0, 20))

        # URL Input Frame
        self.url_frame = ctk.CTkFrame(self.main_frame, fg_color=self.main_frame.cget("fg_color"))
        self.url_frame.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        self.url_frame.grid_columnconfigure(0, weight=1)

        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(
            self.url_frame, 
            placeholder_text="Paste YouTube URL or Shorts link here...", 
            textvariable=self.url_var,
            height=45,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            border_color="gray40"
        )
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self.paste_btn = ctk.CTkButton(
            self.url_frame, 
            text="Paste", 
            width=70, 
            height=45,
            command=self.paste_url,
            fg_color="gray30",
            hover_color="gray40"
        )
        self.paste_btn.grid(row=0, column=1, padx=(0, 10))

        self.fetch_btn = ctk.CTkButton(
            self.url_frame, 
            text="Fetch Details", 
            width=120, 
            height=45,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self.start_fetch_details
        )
        self.fetch_btn.grid(row=0, column=2)

        # Status Banner (for fetching updates)
        self.status_banner = ctk.CTkLabel(
            self.main_frame, 
            text="", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=COLOR_ACCENT,
            anchor="w"
        )
        self.status_banner.grid(row=3, column=0, sticky="w", pady=(0, 10))

        # ----------------------------------------------------
        # Video Metadata Card (Initially hidden)
        # ----------------------------------------------------
        self.meta_card = ctk.CTkFrame(self.main_frame, fg_color=COLOR_BG_CARD, corner_radius=12)
        self.meta_card.grid_columnconfigure(1, weight=1)

        # Thumbnail Label
        self.thumb_label = ctk.CTkLabel(self.meta_card, text="[No Thumbnail]")
        self.thumb_label.grid(row=0, column=0, rowspan=4, padx=15, pady=15)

        # Video Title
        self.video_title_lbl = ctk.CTkLabel(
            self.meta_card, 
            text="Video Title Here", 
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            anchor="w", 
            justify="left",
            wraplength=350
        )
        self.video_title_lbl.grid(row=0, column=1, padx=(5, 15), pady=(15, 2), sticky="w")

        # Channel
        self.video_channel_lbl = ctk.CTkLabel(
            self.meta_card, 
            text="Channel: --", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="gray75",
            anchor="w"
        )
        self.video_channel_lbl.grid(row=1, column=1, padx=(5, 15), pady=2, sticky="w")

        # Duration & Views
        self.video_stats_lbl = ctk.CTkLabel(
            self.meta_card, 
            text="Duration: -- | Views: --", 
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="gray75",
            anchor="w"
        )
        self.video_stats_lbl.grid(row=2, column=1, padx=(5, 15), pady=2, sticky="w")

        # ----------------------------------------------------
        # Format Selector Tabview (Initially hidden)
        # ----------------------------------------------------
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.add("Video + Audio")
        self.tab_view.add("Video Only")
        self.tab_view.add("Audio Only")

        # Video + Audio Tab Elements
        self.tab_combobox_combined = ctk.CTkComboBox(self.tab_view.tab("Video + Audio"), width=400, state="readonly")
        self.tab_combobox_combined.pack(padx=20, pady=15)
        self.combined_help_lbl = ctk.CTkLabel(
            self.tab_view.tab("Video + Audio"), 
            text="Note: Select resolutions under 720p or Combined (MP4) to download without FFmpeg.\nResolutions labeled '[Needs FFmpeg]' will download but might lack audio or fail if FFmpeg is missing.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="gray60"
        )
        self.combined_help_lbl.pack(padx=20, pady=(0, 10))

        # Video Only Tab Elements
        self.tab_combobox_video = ctk.CTkComboBox(self.tab_view.tab("Video Only"), width=400, state="readonly")
        self.tab_combobox_video.pack(padx=20, pady=15)
        self.video_help_lbl = ctk.CTkLabel(
            self.tab_view.tab("Video Only"), 
            text="These files contain Video stream only (no audio tracks). Perfect for editing.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="gray60"
        )
        self.video_help_lbl.pack(padx=20, pady=(0, 10))

        # Audio Only Tab Elements
        self.tab_combobox_audio = ctk.CTkComboBox(self.tab_view.tab("Audio Only"), width=400, state="readonly")
        self.tab_combobox_audio.pack(padx=20, pady=15)
        self.audio_help_lbl = ctk.CTkLabel(
            self.tab_view.tab("Audio Only"), 
            text="Downloads music tracks. Saved in native formats (m4a, webm). Doesn't require FFmpeg.",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color="gray60"
        )
        self.audio_help_lbl.pack(padx=20, pady=(0, 10))

        # Download Button (Initially hidden)
        self.download_btn = ctk.CTkButton(
            self.main_frame, 
            text="Download Selected", 
            height=45,
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            fg_color=COLOR_SUCCESS,
            hover_color="#0D9488",
            command=self.start_download
        )

        # ----------------------------------------------------
        # Progress Card (Initially hidden)
        # ----------------------------------------------------
        self.progress_card = ctk.CTkFrame(self.main_frame, fg_color="#1E293B", corner_radius=10)
        
        self.progress_title = ctk.CTkLabel(
            self.progress_card, 
            text="Downloading Media...", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.progress_title.grid(row=0, column=0, columnspan=2, padx=15, pady=(10, 5), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(self.progress_card, width=500, progress_color=COLOR_ACCENT)
        self.progress_bar.grid(row=1, column=0, columnspan=2, padx=15, pady=5, sticky="ew")
        self.progress_bar.set(0)

        self.progress_speed_lbl = ctk.CTkLabel(
            self.progress_card, 
            text="Speed: 0 B/s", 
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.progress_speed_lbl.grid(row=2, column=0, padx=15, pady=(2, 10), sticky="w")

        self.progress_eta_lbl = ctk.CTkLabel(
            self.progress_card, 
            text="ETA: N/A", 
            font=ctk.CTkFont(family="Segoe UI", size=11),
            anchor="e"
        )
        self.progress_eta_lbl.grid(row=2, column=1, padx=15, pady=(2, 10), sticky="e")
        self.progress_card.grid_columnconfigure(0, weight=1)
        self.progress_card.grid_columnconfigure(1, weight=1)

        self.cancel_btn = ctk.CTkButton(
            self.progress_card, 
            text="Cancel", 
            fg_color=COLOR_DANGER,
            hover_color="#DC2626",
            width=80,
            command=self.cancel_download
        )
        self.cancel_btn.grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 10))

        # Success Frame
        self.success_frame = ctk.CTkFrame(self.main_frame, fg_color="#064E3B", corner_radius=10)
        self.success_lbl = ctk.CTkLabel(
            self.success_frame, 
            text="✓ Download Complete!", 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#A7F3D0"
        )
        self.success_lbl.pack(padx=15, pady=(10, 5))
        
        self.action_buttons_frame = ctk.CTkFrame(self.success_frame, fg_color="#064E3B")
        self.action_buttons_frame.pack(padx=15, pady=(5, 10))
        
        self.open_file_btn = ctk.CTkButton(
            self.action_buttons_frame, 
            text="Play File", 
            width=100, 
            fg_color=COLOR_SUCCESS,
            hover_color="#0D9488",
            command=self.play_file
        )
        self.open_file_btn.pack(side="left", padx=5)

        self.open_folder_btn = ctk.CTkButton(
            self.action_buttons_frame, 
            text="Open Folder", 
            width=100,
            fg_color="gray30",
            hover_color="gray40",
            command=self.open_download_folder
        )
        self.open_folder_btn.pack(side="left", padx=5)
        
        self.last_saved_file = None

    # ----------------------------------------------------
    # Business Logic Interactivity
    # ----------------------------------------------------
    
    def check_ffmpeg_status(self):
        """Updates the sidebar FFmpeg status display."""
        if is_ffmpeg_available():
            self.ffmpeg_status_val.configure(text="Detected (Full HD Unlocked)", text_color=COLOR_SUCCESS)
        else:
            self.ffmpeg_status_val.configure(text="Missing (Limited to Combined 720p)", text_color=COLOR_WARNING)

    def show_ffmpeg_help(self):
        """Displays help pop-up for FFmpeg installation."""
        ffmpeg_help_window = ctk.CTkToplevel(self)
        ffmpeg_help_window.title("FFmpeg Installation Guide")
        ffmpeg_help_window.geometry("500x400")
        ffmpeg_help_window.transient(self)  # set to be on top of main window
        ffmpeg_help_window.grab_set()

        lbl = ctk.CTkLabel(
            ffmpeg_help_window, 
            text="Installing FFmpeg for HD Merging", 
            font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            text_color=COLOR_ACCENT
        )
        lbl.pack(padx=20, pady=(20, 10), anchor="w")

        help_text = (
            "YouTube keeps high-definition video (1080p, 4K) and audio separate. "
            "To combine them, this app uses a utility named FFmpeg.\n\n"
            "How to install FFmpeg on Windows:\n"
            "1. Open PowerShell or Command Prompt as Administrator.\n"
            "2. Run the command: \n"
            "    winget install GnuWin32.FFmpeg\n"
            "   (Or download from ffmpeg.org and add it to your PATH environment variable).\n"
            "3. Restart this application.\n\n"
            "Without FFmpeg, you can download pre-merged videos up to 720p directly, "
            "as well as separate video-only or audio-only formats."
        )

        txt_box = ctk.CTkTextbox(ffmpeg_help_window, wrap="word", width=460, height=250)
        txt_box.pack(padx=20, pady=10)
        txt_box.insert("0.0", help_text)
        txt_box.configure(state="disabled")

        close_btn = ctk.CTkButton(ffmpeg_help_window, text="Dismiss", command=ffmpeg_help_window.destroy)
        close_btn.pack(padx=20, pady=10)

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def paste_url(self):
        """Reads clipboard contents and inserts into URL entry."""
        try:
            clipboard = self.clipboard_get()
            self.url_var.set(clipboard)
        except Exception:
            pass  # Empty clipboard or invalid contents

    def browse_folder(self):
        """Opens folder dialog and updates path."""
        folder = filedialog.askdirectory(initialdir=self.download_path_var.get())
        if folder:
            self.download_path_var.set(os.path.normpath(folder))

    def paste_url(self):
        try:
            self.url_var.set(self.clipboard_get())
        except Exception:
            pass

    def start_fetch_details(self):
        """Validates input and launches the background thread to fetch details."""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter or paste a valid YouTube URL.")
            return

        # Hide any previous results/progress/success panels
        self.meta_card.grid_forget()
        self.tab_view.grid_forget()
        self.download_btn.grid_forget()
        self.progress_card.grid_forget()
        self.success_frame.grid_forget()

        # Disable fetch interface
        self.url_entry.configure(state="disabled")
        self.paste_btn.configure(state="disabled")
        self.fetch_btn.configure(state="disabled")
        self.status_banner.configure(text="Fetching video metadata... Please wait.", text_color=COLOR_ACCENT)

        # Threaded Fetch
        threading.Thread(target=self._fetch_details_worker, args=(url,), daemon=True).start()

    def _fetch_details_worker(self, url):
        """Worker thread executing yt-dlp to extract metadata."""
        try:
            info = self.downloader.fetch_video_info(url)
            
            # Load thumbnail image using urllib to avoid requests dependency
            thumbnail_image = None
            if info.get('thumbnail'):
                try:
                    req = urllib.request.Request(
                        info['thumbnail'], 
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    with urllib.request.urlopen(req, timeout=5) as response:
                        img_data = response.read()
                        thumbnail_image = Image.open(io.BytesIO(img_data))
                except Exception as e:
                    print(f"Error fetching thumbnail image: {e}")

            # Send back to main GUI thread
            self.after(0, lambda: self.finish_fetch_details(info, thumbnail_image))
            
        except Exception as e:
            self.after(0, lambda: self.handle_fetch_error(str(e)))

    def handle_fetch_error(self, err_msg):
        """Restores fetch UI and displays errors."""
        self.url_entry.configure(state="normal")
        self.paste_btn.configure(state="normal")
        self.fetch_btn.configure(state="normal")
        self.status_banner.configure(text=f"Failed to fetch details.", text_color=COLOR_DANGER)
        messagebox.showerror("Error Fetching Video", err_msg)

    def finish_fetch_details(self, info, thumbnail_image):
        """Displays metadata on screen and populates option lists."""
        self.current_video_info = info
        
        # Re-enable inputs
        self.url_entry.configure(state="normal")
        self.paste_btn.configure(state="normal")
        self.fetch_btn.configure(state="normal")
        self.status_banner.configure(text="Metadata loaded successfully!", text_color=COLOR_SUCCESS)

        # Set title, channel, duration, and stats
        self.video_title_lbl.configure(text=info['title'])
        self.video_channel_lbl.configure(text=f"Channel: {info['author']}")
        self.video_stats_lbl.configure(text=f"Duration: {info['duration']} | Views: {info['views']}")

        # Set Thumbnail
        if thumbnail_image:
            # Resize image to fit keeping aspect ratio (target 240x135)
            self.thumbnail_pil = thumbnail_image
            thumbnail_image = thumbnail_image.resize((240, 135), Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=thumbnail_image, dark_image=thumbnail_image, size=(240, 135))
            self.thumb_label.configure(image=ctk_img, text="")
        else:
            self.thumb_label.configure(image=None, text="[No Thumbnail]")

        # Populate dropdown menus
        # 1. Combined (Video + Audio)
        combined_options = []
        self.combined_id_map = {}
        
        # Add high quality merge option at the top if ffmpeg is available
        ffmpeg_ok = is_ffmpeg_available()
        
        # We also want to let them download best video/audio merged if they want.
        # Let's map high-res formats to a special key 'best_merge:<format_id>'
        
        # Let's separate formats. Pre-merged first:
        for fmt in info['formats_combined']:
            display = f"{fmt['display_name']} (Pre-Merged)"
            combined_options.append(display)
            self.combined_id_map[display] = ('combined', fmt['id'])
            
        # Video-only formats can be merged with audio if ffmpeg is present.
        # Let's add them as options to Combined tab, clearly marked.
        for fmt in info['formats_video_only']:
            lbl = "[Needs FFmpeg]" if not ffmpeg_ok else "[Auto Merge]"
            display = f"{fmt['resolution']} - {fmt['size_str']} {lbl}"
            combined_options.append(display)
            self.combined_id_map[display] = ('best_merge', fmt['id'])

        if combined_options:
            self.tab_combobox_combined.configure(values=combined_options)
            self.tab_combobox_combined.set(combined_options[0])
        else:
            self.tab_combobox_combined.configure(values=["No combined formats available"])
            self.tab_combobox_combined.set("No combined formats available")

        # 2. Video Only
        video_options = []
        self.video_id_map = {}
        for fmt in info['formats_video_only']:
            display = fmt['display_name']
            video_options.append(display)
            self.video_id_map[display] = fmt['id']
            
        if video_options:
            self.tab_combobox_video.configure(values=video_options)
            self.tab_combobox_video.set(video_options[0])
        else:
            self.tab_combobox_video.configure(values=["No video-only formats available"])
            self.tab_combobox_video.set("No video-only formats available")

        # 3. Audio Only
        audio_options = []
        self.audio_id_map = {}
        for fmt in info['formats_audio_only']:
            display = fmt['display_name']
            audio_options.append(display)
            self.audio_id_map[display] = fmt['id']
            
        if audio_options:
            self.tab_combobox_audio.configure(values=audio_options)
            self.tab_combobox_audio.set(audio_options[0])
        else:
            self.tab_combobox_audio.configure(values=["No audio formats available"])
            self.tab_combobox_audio.set("No audio formats available")

        # Render everything
        self.meta_card.grid(row=4, column=0, sticky="ew", pady=10)
        self.tab_view.grid(row=5, column=0, sticky="ew", pady=10)
        self.download_btn.grid(row=6, column=0, sticky="ew", pady=(10, 20))

    def start_download(self):
        """Gathers options and triggers the download process."""
        active_tab = self.tab_view.get()
        url = self.current_video_info['url']
        out_dir = self.download_path_var.get()
        
        # Create output directory if it doesn't exist
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        download_type = None
        format_id = None

        if active_tab == "Video + Audio":
            selected = self.tab_combobox_combined.get()
            if selected not in self.combined_id_map:
                messagebox.showerror("Error", "Please select a valid quality option.")
                return
            download_type, format_id = self.combined_id_map[selected]
            
            # Check FFmpeg warning
            if download_type == 'best_merge' and not is_ffmpeg_available():
                show_anyway = messagebox.askyesno(
                    "FFmpeg Missing", 
                    "You selected a high-definition format that requires FFmpeg to merge video and audio.\n\n"
                    "Since FFmpeg is not installed, downloading will fail or lack audio.\n\n"
                    "Would you like to try downloading it anyway? (Or select a 'Pre-Merged' format to download safely without FFmpeg.)"
                )
                if not show_anyway:
                    return

        elif active_tab == "Video Only":
            selected = self.tab_combobox_video.get()
            if selected not in self.video_id_map:
                messagebox.showerror("Error", "Please select a valid quality option.")
                return
            download_type = 'video_only'
            format_id = self.video_id_map[selected]
            
        elif active_tab == "Audio Only":
            selected = self.tab_combobox_audio.get()
            if selected not in self.audio_id_map:
                messagebox.showerror("Error", "Please select a valid quality option.")
                return
            download_type = 'audio_only'
            format_id = self.audio_id_map[selected]

        # Reset and show progress bar
        self.progress_bar.set(0)
        self.progress_speed_lbl.configure(text="Speed: 0 B/s")
        self.progress_eta_lbl.configure(text="ETA: N/A")
        self.progress_title.configure(text="Downloading: Starting...")
        
        self.success_frame.grid_forget()
        self.progress_card.grid(row=7, column=0, sticky="ew", pady=10)

        # Disable selectors and download buttons
        self.download_btn.configure(state="disabled")
        self.fetch_btn.configure(state="disabled")
        self.url_entry.configure(state="disabled")
        self.paste_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")

        # Scroll to bottom to ensure progress card is visible
        self.main_frame._parent_canvas.yview_moveto(1.0)

        # Call download engine
        self.downloader.download(
            url=url,
            format_id=format_id,
            download_type=download_type,
            output_path=out_dir,
            progress_callback=self.on_download_progress,
            done_callback=self.on_download_success,
            error_callback=self.on_download_error
        )

    def on_download_progress(self, data):
        """Callback to handle progress updates from downloader."""
        self.after(0, lambda: self._update_progress_ui(data))

    def _update_progress_ui(self, data):
        self.progress_bar.set(data['percent'])
        self.progress_title.configure(text=data['message'])
        self.progress_speed_lbl.configure(text=f"Speed: {data['speed']}")
        self.progress_eta_lbl.configure(text=f"ETA: {data['eta']}")

    def cancel_download(self):
        """Triggers downloader cancellation."""
        self.downloader.cancel_download()
        self.progress_title.configure(text="Cancelling download...")

    def on_download_success(self, filepath):
        """Callback on completion."""
        self.after(0, lambda: self._handle_success_ui(filepath))

    def _handle_success_ui(self, filepath):
        self.last_saved_file = filepath
        
        # Hide progress card and show success banner
        self.progress_card.grid_forget()
        
        self.success_frame.grid(row=8, column=0, sticky="ew", pady=10)
        self.success_lbl.configure(text=f"✓ Download Complete!\nSaved to: {os.path.basename(filepath)}")

        # Re-enable inputs
        self.download_btn.configure(state="normal")
        self.fetch_btn.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.paste_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")

        # Scroll to bottom
        self.main_frame._parent_canvas.yview_moveto(1.0)
        
        # Play completion sound or alert
        messagebox.showinfo("Success", f"Download finished successfully!\nFile: {os.path.basename(filepath)}")

    def on_download_error(self, err_msg):
        """Callback on failure."""
        self.after(0, lambda: self._handle_error_ui(err_msg))

    def _handle_error_ui(self, err_msg):
        # Hide progress card
        self.progress_card.grid_forget()
        
        # Re-enable inputs
        self.download_btn.configure(state="normal")
        self.fetch_btn.configure(state="normal")
        self.url_entry.configure(state="normal")
        self.paste_btn.configure(state="normal")
        self.browse_btn.configure(state="normal")

        messagebox.showerror("Download Failed", err_msg)

    def play_file(self):
        """Opens the downloaded file in default media player."""
        if self.last_saved_file and os.path.exists(self.last_saved_file):
            try:
                os.startfile(self.last_saved_file)
            except Exception as e:
                messagebox.showerror("Error Opening File", f"Could not launch file: {str(e)}")
        else:
            messagebox.showerror("Error", "File does not exist or has been moved.")

    def open_download_folder(self):
        """Opens file explorer focused on downloaded file's folder."""
        if self.last_saved_file:
            folder = os.path.dirname(self.last_saved_file)
            if os.path.exists(folder):
                try:
                    os.startfile(folder)
                except Exception as e:
                    messagebox.showerror("Error Opening Folder", f"Could not open directory: {str(e)}")
        else:
            # Fallback to output directory path
            folder = self.download_path_var.get()
            if os.path.exists(folder):
                os.startfile(folder)
