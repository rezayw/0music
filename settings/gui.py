import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import webbrowser
from .utils import clear_placeholder, restore_placeholder
from .config import OUTPUT_DIR
from .database import init_db, get_all_songs
from .downloader import download_audio, extract_thumbnail

class MusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("0Music - Free Downloader YouTube Audio")
        self.root.geometry("338x730")
        self.root.configure(bg="#000000")

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
        style.theme_use('clam')
        style.configure("TProgressbar",
                        troughcolor=self.colors["progress_trough"],
                        background=self.colors["progress_bar"],
                        thickness=8)

        init_db()
        self.thumbnail_image = None
        self.play_icon_image = self.load_icon("assets/youtube.png", (90, 65))

        self.build_ui()

    def load_icon(self, path, size):
        return ImageTk.PhotoImage(Image.open(path).resize(size))

    def build_ui(self):
        self.build_thumbnail_section()
        self.url_entry = self.build_entry("YouTube Video URL:", "https://youtu.be/example", self.start_load_thumbnail_thread)
        self.custom_title_entry = self.build_entry("Title :", "e.g. My Song")
        self.custom_author_entry = self.build_entry("Author :", "e.g. Artist")
        self.build_output_label()
        self.build_download_button()
        self.build_song_list()

    def build_thumbnail_section(self):
        frame = tk.Frame(self.root, width=320, height=180, bg=self.colors["bg"])
        frame.pack(pady=10)
        frame.pack_propagate(False)

        self.thumbnail_label = tk.Label(frame, bg=self.colors["bg"])
        self.thumbnail_label.pack(expand=True, fill='both')

        self.play_button = tk.Button(
            frame, image=self.play_icon_image, command=self.play_video,
            bg=self.colors["bg"], border=0, highlightthickness=0, relief="flat", cursor="hand2")
        self.play_button.place(relx=0.5, rely=0.5, anchor="center")
        self.play_button.lower()

        self.thumb_progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.thumb_progress.pack(pady=5)
        self.thumb_progress.pack_forget()

    def build_entry(self, label_text, placeholder, focusout_func=None):
        frame = tk.Frame(self.root, bg=self.colors["bg"])
        frame.pack(pady=5, fill="x", padx=15)

        label = tk.Label(frame, text=label_text, fg=self.colors["placeholder_fg"], bg=self.colors["bg"],
                         font=(self.font, 9, "bold"))
        label.pack(anchor='w')

        entry = tk.Entry(frame, fg=self.colors["placeholder_fg"], bg=self.colors["entry_bg"],
                         insertbackground=self.colors["entry_fg"], font=(self.font, 11), relief='flat')
        entry.insert(0, placeholder)
        entry.bind("<FocusIn>", lambda e: clear_placeholder(entry, placeholder, self.colors["entry_fg"]))
        entry.bind("<FocusOut>", lambda e: restore_placeholder(entry, placeholder, self.colors["placeholder_fg"]))
        if focusout_func:
            entry.bind("<FocusOut>", focusout_func)
        entry.pack(fill="x", ipady=4)

        return entry

    def build_output_label(self):
        label = tk.Label(
            self.root, text=f"Output Folder:\n{OUTPUT_DIR}",
            fg=self.colors["muted"], bg=self.colors["bg"],
            font=(self.font, 9), justify="left"
        )
        label.pack(anchor='w', padx=15, pady=(5, 15))

    def build_download_button(self):
        self.download_button = tk.Button(
            self.root, text="Download", command=self.start_download_thread,
            bg=self.colors["accent"], fg="black", font=(self.font, 12, "bold"),
            relief="flat", padx=10, pady=8, cursor="hand2")
        self.download_button.pack(padx=15, pady=5, fill="x")
        self.download_button.bind("<Enter>", lambda e: self.download_button.config(bg="#1AA34A"))
        self.download_button.bind("<Leave>", lambda e: self.download_button.config(bg=self.colors["accent"]))

        self.download_progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.download_progress.pack(pady=5, padx=15)
        self.download_progress.pack_forget()

    def build_song_list(self):
        wrapper = tk.Frame(self.root, bg=self.colors["bg"])
        wrapper.pack(fill="both", expand=False, padx=15, pady=(10, 20))

        tk.Label(wrapper, text="🎵  Downloaded Songs", font=(self.font, 11, "bold"),
                fg="white", bg=self.colors["bg"]).pack(anchor='w', pady=(0, 8))

        listbox_frame = tk.Frame(wrapper, bg=self.colors["bg"])
        listbox_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side="right", fill="y")

        self.song_listbox = tk.Listbox(
            listbox_frame,
            height=7,
            bg=self.colors["entry_bg"],
            fg="white",
            font=(self.font, 10),
            relief="flat",
            highlightthickness=1,
            highlightcolor=self.colors["accent"],
            selectbackground=self.colors["accent"],
            activestyle='none',
            yscrollcommand=scrollbar.set
        )
        self.song_listbox.pack(side="left", fill="both", expand=True)

        scrollbar.config(command=self.song_listbox.yview)

        self.refresh_song_list()

    def refresh_song_list(self):
        self.song_listbox.delete(0, tk.END)
        self.song_listbox.insert(tk.END, "ID  | Title           | Author")
        self.song_listbox.insert(tk.END, "----------------------------------")
        for id, title, author, *_ in get_all_songs():
            line = f"{str(id):<3} | {title[:15]:<15} | {author[:12]:<12}"
            self.song_listbox.insert(tk.END, line)

    def play_video(self):
        url = self.url_entry.get().strip()
        if "youtube.com/watch?v=" in url or "youtu.be/" in url:
            webbrowser.open(url)
        else:
            messagebox.showerror("Invalid URL", "Please enter a valid YouTube link.")

    def start_load_thumbnail_thread(self, event=None):
        self.thumb_progress.pack()
        threading.Thread(target=self.load_thumbnail, daemon=True).start()

    def load_thumbnail(self):
        url = self.url_entry.get().strip()
        if not url:
            self.clear_thumbnail()
            return
        try:
            self.root.after(0, self.thumb_progress.start)
            img = extract_thumbnail(url)
            if img:
                self.thumbnail_image = ImageTk.PhotoImage(img.resize((338, 180)))
                self.root.after(0, self.update_thumbnail_ui)
            else:
                self.root.after(0, lambda: self.thumbnail_label.config(text="No thumbnail", fg=self.colors["muted"]))
                self.root.after(0, self.play_button.lower)
        except Exception as e:
            self.root.after(0, lambda: self.thumbnail_label.config(text=f"Error:\n{e}", fg=self.colors["error"]))
        finally:
            self.root.after(0, self.thumb_progress.stop)
            self.root.after(0, self.thumb_progress.pack_forget)

    def update_thumbnail_ui(self):
        self.thumbnail_label.config(image=self.thumbnail_image)
        self.play_button.lift()

    def clear_thumbnail(self):
        self.thumbnail_label.config(image="", text="")
        self.play_button.lower()
        self.thumb_progress.pack_forget()

    def start_download_thread(self):
        self.download_progress.pack()
        threading.Thread(target=self.download_audio_process, daemon=True).start()

    def download_audio_process(self):
        url = self.url_entry.get().strip()
        title = self.custom_title_entry.get().strip()
        author = self.custom_author_entry.get().strip()

        if not url:
            self.show_message("Missing URL", warning=True)
            return

        try:
            self.download_progress.start()
            song_title = download_audio(url, title or None, author or None)
            self.root.after(0, self.refresh_song_list)
            self.root.after(0, lambda: messagebox.showinfo("Downloaded", f"{song_title} has been saved."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.root.after(0, self.download_progress.stop)
            self.root.after(0, self.download_progress.pack_forget)

    def show_message(self, text, warning=False):
        if warning:
            self.root.after(0, lambda: messagebox.showwarning("Warning", text))
        else:
            self.root.after(0, lambda: messagebox.showinfo("Info", text))