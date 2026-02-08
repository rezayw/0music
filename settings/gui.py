import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import threading
import webbrowser
from .utils import clear_placeholder, restore_placeholder
from .config import OUTPUT_DIR
from .database import init_db, get_all_songs
from .downloader import download_audio, extract_video_info

# Try to import VLC
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    print("Warning: python-vlc not installed. Audio preview disabled.")


class MusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("0Music - Free Downloader YouTube Audio")
        self.root.geometry("338x700")
        self.root.configure(bg="#000000")
        self.root.resizable(False, False)

        # VLC player instance
        self.vlc_instance = None
        self.vlc_player = None
        self.is_playing = False
        self.current_stream_url = None
        
        if VLC_AVAILABLE:
            self.vlc_instance = vlc.Instance('--no-xlib', '--quiet')
            self.vlc_player = self.vlc_instance.media_player_new()

        # Load default logo
        self.default_logo_image = None
        try:
            original_logo = Image.open("assets/logo.png")
            resized_logo = original_logo.resize((338, 180), Image.LANCZOS)
            self.default_logo_image = ImageTk.PhotoImage(resized_logo)
        except FileNotFoundError:
            print("Warning: assets/logo.png not found.")
        except Exception as e:
            print(f"Error loading default logo: {e}")

        self.font = "Segoe UI"
        self.colors = {
            "bg": "#121212",
            "entry_bg": "#1DB954",
            "entry_fg": "#FFFFFF",
            "placeholder_fg": "#FFFFFF",
            "accent": "#1DB954",
            "progress_trough": "#2E2E3E",
            "progress_bar": "#1ED760",
            "text": "#FFFFFF",
            "muted": "#AAAAAA",
            "error": "#FF4C4C"
        }

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar",
                        troughcolor=self.colors["progress_trough"],
                        background=self.colors["progress_bar"],
                        thickness=12,
                        borderwidth=0)

        init_db()
        self.thumbnail_image = None
        self.current_thumbnail_image = None
        
        # Create play/pause icons
        self.play_icon_image = self.create_play_icon(60)
        self.pause_icon_image = self.create_pause_icon(60)

        # Store placeholders for validation
        self.url_placeholder = "https://youtu.be/example"
        self.title_placeholder = "e.g. My Song"
        self.author_placeholder = "e.g. Artist"

        self.build_ui()
        
        # Bind cleanup on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_play_icon(self, size):
        """Create a play triangle icon."""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        padding = 5
        draw.ellipse([padding, padding, size-padding, size-padding], fill=(255, 255, 255, 200))
        margin = size // 4
        points = [
            (margin + 5, margin),
            (margin + 5, size - margin),
            (size - margin, size // 2)
        ]
        draw.polygon(points, fill=(29, 185, 84, 255))
        return ImageTk.PhotoImage(img)

    def create_pause_icon(self, size):
        """Create a pause icon with two bars."""
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        padding = 5
        draw.ellipse([padding, padding, size-padding, size-padding], fill=(255, 255, 255, 200))
        bar_width = size // 6
        margin = size // 4
        draw.rectangle([margin, margin, margin + bar_width, size - margin], fill=(29, 185, 84, 255))
        draw.rectangle([size - margin - bar_width, margin, size - margin, size - margin], fill=(29, 185, 84, 255))
        return ImageTk.PhotoImage(img)

    def build_ui(self):
        self.build_thumbnail_section()
        self.url_entry = self.build_entry("YouTube Video URL:", self.url_placeholder, self.start_load_thumbnail_thread)
        self.custom_title_entry = self.build_entry("Title:", self.title_placeholder)
        self.custom_author_entry = self.build_entry("Author:", self.author_placeholder)
        self.build_output_label()
        self.build_download_button()
        self.build_song_list()

    def build_thumbnail_section(self):
        frame = tk.Frame(self.root, width=338, height=180, bg=self.colors["bg"])
        frame.pack(pady=10)
        frame.pack_propagate(False)

        self.thumbnail_label = tk.Label(frame, bg=self.colors["bg"])
        self.thumbnail_label.pack(expand=True, fill="both")

        if self.default_logo_image:
            self.thumbnail_label.config(image=self.default_logo_image)
            self.current_thumbnail_image = self.default_logo_image

        self.play_button = tk.Button(
            frame, image=self.play_icon_image, command=self.toggle_playback,
            bg=self.colors["bg"], border=0, highlightthickness=0, relief="flat", cursor="hand2",
            activebackground=self.colors["bg"]
        )
        self.play_button.place(relx=0.5, rely=0.5, anchor="center")
        self.play_button.lower()

        # Thumbnail loading progress bar
        self.thumb_progress = ttk.Progressbar(
            self.root, 
            mode="indeterminate",
            style="TProgressbar",
            length=308
        )

    def build_entry(self, label_text, placeholder, focusout_func=None):
        frame = tk.Frame(self.root, bg=self.colors["bg"])
        frame.pack(pady=5, fill="x", padx=15)

        label = tk.Label(frame, text=label_text, fg=self.colors["placeholder_fg"], bg=self.colors["bg"],
                         font=(self.font, 9, "bold"))
        label.pack(anchor="w")

        entry = tk.Entry(frame, fg=self.colors["placeholder_fg"], bg=self.colors["entry_bg"],
                         insertbackground=self.colors["entry_fg"], font=(self.font, 11), relief="flat")
        entry.insert(0, placeholder)
        entry.bind("<FocusIn>", lambda e: clear_placeholder(entry, placeholder, self.colors["entry_fg"]))
        entry.bind("<FocusOut>", lambda e: restore_placeholder(entry, placeholder, self.colors["placeholder_fg"]))
        
        if focusout_func:
            entry.bind("<FocusOut>", focusout_func, add="+")
        entry.pack(fill="x", ipady=4)

        return entry

    def build_output_label(self):
        label = tk.Label(
            self.root, text=f"Output: {OUTPUT_DIR}",
            fg=self.colors["muted"], bg=self.colors["bg"],
            font=(self.font, 9), justify="left"
        )
        label.pack(anchor="w", padx=15, pady=(5, 15))

    def build_download_button(self):
        self.download_button = tk.Button(
            self.root, text="Download", command=self.start_download_thread,
            bg=self.colors["accent"], fg="black", font=(self.font, 12, "bold"),
            relief="flat", padx=10, pady=8, cursor="hand2"
        )
        self.download_button.pack(padx=15, pady=5, fill="x")
        self.download_button.bind("<Enter>", lambda e: self.download_button.config(bg="#1AA34A"))
        self.download_button.bind("<Leave>", lambda e: self.download_button.config(bg=self.colors["accent"]))

        self.download_progress = ttk.Progressbar(
            self.root, 
            mode="indeterminate",
            style="TProgressbar",
            length=308
        )

    def build_song_list(self):
        wrapper = tk.Frame(self.root, bg=self.colors["bg"])
        wrapper.pack(fill="both", expand=True, padx=15, pady=(10, 20))

        tk.Label(wrapper, text="Downloaded Songs", font=(self.font, 11, "bold"),
                 fg="white", bg=self.colors["bg"]).pack(anchor="w", pady=(0, 8))

        listbox_frame = tk.Frame(wrapper, bg=self.colors["bg"])
        listbox_frame.pack(fill="both", expand=True)

        columns = ("ID", "Title", "Author")
        self.song_list_tree = ttk.Treeview(
            listbox_frame,
            columns=columns,
            show="headings",
            height=7,
            selectmode="browse"
        )

        self.song_list_tree.heading("ID", text="ID", anchor=tk.W)
        self.song_list_tree.heading("Title", text="Title", anchor=tk.W)
        self.song_list_tree.heading("Author", text="Author", anchor=tk.W)

        self.song_list_tree.column("ID", width=40, stretch=tk.NO, anchor=tk.CENTER)
        self.song_list_tree.column("Title", width=160, stretch=tk.YES, anchor=tk.W)
        self.song_list_tree.column("Author", width=100, stretch=tk.YES, anchor=tk.W)

        style = ttk.Style()
        style.configure("Treeview",
                        background=self.colors["entry_bg"],
                        foreground=self.colors["text"],
                        fieldbackground=self.colors["entry_bg"],
                        font=(self.font, 10),
                        rowheight=25)
        style.map("Treeview",
                  background=[("selected", self.colors["accent"])],
                  foreground=[("selected", "black")])
        style.configure("Treeview.Heading",
                        font=(self.font, 10, "bold"),
                        background=self.colors["accent"],
                        foreground="black",
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[("active", "#1AA34A")])

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.song_list_tree.yview)
        self.song_list_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.song_list_tree.pack(side="left", fill="both", expand=True)

        self.refresh_song_list()

    def refresh_song_list(self):
        for item in self.song_list_tree.get_children():
            self.song_list_tree.delete(item)

        for song_id, title, author, *_ in get_all_songs():
            self.song_list_tree.insert("", tk.END, values=(song_id, title or "Unknown", author or "Unknown"))

    def get_entry_value(self, entry, placeholder):
        value = entry.get().strip()
        return "" if value == placeholder else value

    def set_entry_value(self, entry, value):
        entry.delete(0, tk.END)
        entry.insert(0, value)
        entry.config(fg=self.colors["entry_fg"])

    def toggle_playback(self):
        if not VLC_AVAILABLE:
            url = self.get_entry_value(self.url_entry, self.url_placeholder)
            if url and ("youtube.com/watch?v=" in url or "youtu.be/" in url):
                webbrowser.open(url)
            else:
                messagebox.showerror("Invalid URL", "Please enter a valid YouTube link.")
            return

        if not self.current_stream_url:
            messagebox.showinfo("Info", "Load a video first by entering a URL.")
            return

        if self.is_playing:
            self.stop_playback()
        else:
            self.start_playback()

    def start_playback(self):
        if not VLC_AVAILABLE or not self.current_stream_url:
            return
        
        try:
            media = self.vlc_instance.media_new(self.current_stream_url)
            self.vlc_player.set_media(media)
            self.vlc_player.play()
            self.is_playing = True
            self.play_button.config(image=self.pause_icon_image)
        except Exception as e:
            print(f"Playback error: {e}")
            err_msg = str(e)
            messagebox.showerror("Playback Error", f"Could not play audio: {err_msg}")

    def stop_playback(self):
        if not VLC_AVAILABLE:
            return
        
        try:
            self.vlc_player.stop()
            self.is_playing = False
            self.play_button.config(image=self.play_icon_image)
        except Exception as e:
            print(f"Stop error: {e}")

    def start_load_thumbnail_thread(self, event=None):
        url = self.get_entry_value(self.url_entry, self.url_placeholder)
        if not url:
            self.clear_thumbnail()
            return

        self.stop_playback()
        self.current_stream_url = None

        self.thumbnail_label.config(image="", text="Loading...", fg=self.colors["muted"])
        self.play_button.lower()

        self.thumb_progress.pack(pady=(0, 5), padx=15, fill="x")
        self.thumb_progress.start(15)
        threading.Thread(target=self.load_thumbnail, daemon=True).start()

    def load_thumbnail(self):
        url = self.get_entry_value(self.url_entry, self.url_placeholder)
        if not url:
            self.root.after(0, self.clear_thumbnail)
            return

        try:
            info = extract_video_info(url)
            img = info.get('thumbnail')
            title = info.get('title', '')
            author = info.get('author', '')
            stream_url = info.get('stream_url')
            
            self.current_stream_url = stream_url
            
            if img:
                self.current_thumbnail_image = ImageTk.PhotoImage(img.resize((338, 180), Image.LANCZOS))
                self.root.after(0, self.update_thumbnail_ui)
            else:
                self.root.after(0, lambda: self.thumbnail_label.config(image="", text="No thumbnail available", fg=self.colors["muted"]))
                self.root.after(0, self.play_button.lower)
            
            if title:
                self.root.after(0, lambda t=title: self.set_entry_value(self.custom_title_entry, t))
            if author:
                self.root.after(0, lambda a=author: self.set_entry_value(self.custom_author_entry, a))
                
        except Exception as e:
            err_msg = str(e)[:50]
            self.root.after(0, lambda msg=err_msg: self.thumbnail_label.config(image="", text=f"Error: {msg}", fg=self.colors["error"]))
            self.root.after(0, self.play_button.lower)
        finally:
            self.root.after(0, self.thumb_progress.stop)
            self.root.after(0, self.thumb_progress.pack_forget)

    def update_thumbnail_ui(self):
        self.thumbnail_label.config(image=self.current_thumbnail_image, text="")
        self.play_button.config(image=self.play_icon_image)
        self.play_button.lift()

    def clear_thumbnail(self):
        self.stop_playback()
        self.current_stream_url = None
        
        if self.default_logo_image:
            self.thumbnail_label.config(image=self.default_logo_image, text="")
            self.current_thumbnail_image = self.default_logo_image
        else:
            self.thumbnail_label.config(image="", text="")
            self.current_thumbnail_image = None
        self.play_button.lower()
        self.thumb_progress.stop()
        self.thumb_progress.pack_forget()

    def start_download_thread(self):
        url = self.get_entry_value(self.url_entry, self.url_placeholder)
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube URL.")
            return

        self.stop_playback()

        self.download_button.config(state=tk.DISABLED, text="Downloading...")
        self.download_progress.pack(pady=(0, 5), padx=15, fill="x")
        self.download_progress.start(15)
        threading.Thread(target=self.download_audio_process, daemon=True).start()

    def download_audio_process(self):
        try:
            url = self.get_entry_value(self.url_entry, self.url_placeholder)
            title = self.get_entry_value(self.custom_title_entry, self.title_placeholder)
            author = self.get_entry_value(self.custom_author_entry, self.author_placeholder)

            if not url:
                self.root.after(0, lambda: messagebox.showwarning("Warning", "Missing URL"))
                return

            song_title = download_audio(url, title or None, author or None)
            self.root.after(0, self.refresh_song_list)
            self.root.after(0, lambda st=song_title: messagebox.showinfo("Downloaded", f"'{st}' has been saved."))

        except Exception as e:
            print(f"Download error: {e}")
            err_msg = str(e)
            self.root.after(0, lambda msg=err_msg: messagebox.showerror("Download Error", f"Failed to download: {msg}"))
        finally:
            self.root.after(0, self.download_progress.stop)
            self.root.after(0, self.download_progress.pack_forget)
            self.root.after(0, lambda: self.download_button.config(state=tk.NORMAL, text="Download"))

    def on_closing(self):
        self.stop_playback()
        if self.vlc_player:
            self.vlc_player.release()
        if self.vlc_instance:
            self.vlc_instance.release()
        self.root.destroy()
