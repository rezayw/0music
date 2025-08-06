import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import threading
import webbrowser
from .utils import clear_placeholder, restore_placeholder
from .config import OUTPUT_DIR
from .database import init_db, get_all_songs
from .downloader import download_audio, extract_thumbnail
from .apply_metadata import apply_metadata


class MusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("0Music - Free Downloader YouTube Audio")
        self.root.geometry("338x755")
        self.root.configure(bg="#000000")
        
        try:
            original_logo = Image.open("assets/logo.png")
            # Ubah ukuran menjadi 338x180 agar sesuai dengan ukuran thumbnail video
            resized_logo = original_logo.resize((338, 180), Image.LANCZOS)
            self.default_logo_image = ImageTk.PhotoImage(resized_logo)
        except FileNotFoundError:
            print("Error: assets/logo.png not found. Please ensure the path is correct.")
        except Exception as e:
            print(f"Error loading or resizing default logo image: {e}")

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
        self.url_entry = self.build_entry("𝐘𝐎𝐔𝐭𝐮𝐛𝐞 Video URL:", "https://youtu.be/example", self.start_load_thumbnail_thread)
        self.custom_title_entry = self.build_entry("♪ Title :", "e.g. My Song")
        self.custom_author_entry = self.build_entry("⭐ Author :", "e.g. Artist")
        self.build_output_label()
        self.build_download_button()
        self.build_song_list()

    def build_thumbnail_section(self):
        frame = tk.Frame(self.root, width=320, height=180, bg=self.colors["bg"])
        frame.pack(pady=10)
        frame.pack_propagate(False)

        self.thumbnail_label = tk.Label(frame, bg=self.colors["bg"])
        self.thumbnail_label.pack(expand=True, fill='both')

        if self.default_logo_image:
            self.thumbnail_label.config(image=self.default_logo_image)
            self.current_thumbnail_image = self.default_logo_image 

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

        # --- Start of Treeview changes ---
        listbox_frame = tk.Frame(wrapper, bg=self.colors["bg"])
        listbox_frame.pack(fill="both", expand=True)

        # Define columns for the Treeview
        columns = ('ID', 'Title', 'Author')
        self.song_list_tree = ttk.Treeview(
            listbox_frame,
            columns=columns,
            show='headings', # This makes the column headers visible
            height=7, # Set initial height
            selectmode='browse' # Allow single selection
        )

        # Configure column headings and their properties
        self.song_list_tree.heading('ID', text='ID', anchor=tk.W)
        self.song_list_tree.heading('Title', text='Title', anchor=tk.W)
        self.song_list_tree.heading('Author', text='Author', anchor=tk.W)

        # Configure column widths (adjust as needed for your content)
        self.song_list_tree.column('ID', width=50, stretch=tk.NO, anchor=tk.CENTER) # Fixed width, centered
        self.song_list_tree.column('Title', width=180, stretch=tk.YES, anchor=tk.W)
        self.song_list_tree.column('Author', width=120, stretch=tk.YES, anchor=tk.W)

        # Apply modern styling to the Treeview
        style = ttk.Style()
        # Use 'clam' theme as you already have it, then customize
        style.configure("Treeview",
                        background=self.colors["entry_bg"],
                        foreground=self.colors["text"],
                        fieldbackground=self.colors["entry_bg"],
                        font=(self.font, 10),
                        rowheight=25) # Adjust row height for better spacing
        style.map('Treeview',
                  background=[('selected', self.colors["accent"])],
                  foreground=[('selected', 'black')]) # Text color when selected

        style.configure("Treeview.Heading",
                        font=(self.font, 10, 'bold'),
                        background=self.colors["accent"], # Header background
                        foreground="black", # Header text color
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[('active', '#1AA34A')]) # Hover effect for header

        # Add a scrollbar
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.song_list_tree.yview)
        self.song_list_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.song_list_tree.pack(side="left", fill="both", expand=True)
        # --- End of Treeview changes ---

        self.refresh_song_list()

    def refresh_song_list(self):
        # Clear existing items from the Treeview
        for item in self.song_list_tree.get_children():
            self.song_list_tree.delete(item)

        # Populate the Treeview
        for id, title, author, *_ in get_all_songs():
            # Insert values directly into the Treeview; it handles column alignment
            self.song_list_tree.insert('', tk.END, values=(id, title, author))

    def play_video(self):
        url = self.url_entry.get().strip()
        if "youtube.com/watch?v=" in url or "youtu.be/" in url:
            webbrowser.open(url)
        else:
            messagebox.showerror("Invalid URL", "Please enter a valid YouTube link.")

    # settings/gui.py

   # Di start_load_thumbnail_thread:
    def start_load_thumbnail_thread(self, event=None):
        url = self.url_entry.get().strip()
        if not url or url == "https://youtu.be/example":
            self.clear_thumbnail()
            return

        # Tampilkan teks loading sebelum memulai progress bar
        self.thumbnail_label.config(image="", text="Loading thumbnail...", fg=self.colors["muted"])
        self.play_button.lower() # Sembunyikan tombol play sementara

        self.thumb_progress.pack()
        self.thumb_progress.start()
        threading.Thread(target=self.load_thumbnail, daemon=True).start()

    # Di load_thumbnail, jika ada error atau tidak ada thumbnail:
    # Ganti bagian ini:
    # self.root.after(0, lambda: self.thumbnail_label.config(image="", text="No thumbnail", fg=self.colors["muted"]))
    # Menjadi:
    # self.root.after(0, lambda: self.thumbnail_label.config(image="", text="Failed to load thumbnail.", fg=self.colors["error"]))

    def load_thumbnail(self):
        url = self.url_entry.get().strip()
        # --- Tambahkan Kode Ini ---
        if not url or url == "https://youtu.be/example": # Periksa lagi URL di thread
            self.root.after(0, self.clear_thumbnail)
            return
        # --- Akhir Penambahan Kode ---

        try:
            # ... kode yang sudah ada ...
            img = extract_thumbnail(url)
            if img:
                # --- Modifikasi Ukuran Gambar Thumbnail ---
                self.current_thumbnail_image = ImageTk.PhotoImage(img.resize((338, 180), Image.LANCZOS))
                # --- Akhir Modifikasi Ukuran Gambar Thumbnail ---
                self.root.after(0, self.update_thumbnail_ui)
            else:
                self.root.after(0, lambda: self.thumbnail_label.config(image="", text="No thumbnail", fg=self.colors["muted"])) # Kosongkan image
                self.root.after(0, self.play_button.lower)
        except Exception as e:
            self.root.after(0, lambda: self.thumbnail_label.config(image="", text=f"Error:\n{e}", fg=self.colors["error"])) # Kosongkan image
            self.root.after(0, self.play_button.lower)
        finally:
            self.root.after(0, self.thumb_progress.stop)
            self.root.after(0, self.thumb_progress.pack_forget)

    def update_thumbnail_ui(self):
        self.thumbnail_label.config(image=self.current_thumbnail_image, text="") # Pastikan teks dikosongkan
        self.play_button.lift()

    # settings/gui.py

    def clear_thumbnail(self):
        # --- Modifikasi Kode Ini ---
        if self.default_logo_image:
            self.thumbnail_label.config(image=self.default_logo_image, text="") # Tampilkan logo default
            self.current_thumbnail_image = self.default_logo_image
        else:
            self.thumbnail_label.config(image="", text="") # Jika logo default tidak ada, kosongkan
            self.current_thumbnail_image = None
        self.play_button.lower()
        self.thumb_progress.pack_forget()
        # --- Akhir Modifikasi Kode ---
        
        # Di start_download_thread:
      # Di start_download_thread:
    def start_download_thread(self):
        self.download_button.config(state=tk.DISABLED, text="Downloading...") # Nonaktifkan tombol dan ubah teks
        self.download_progress.pack()
        threading.Thread(target=self.download_audio_process, daemon=True).start()

    # Di download_audio_process, di bagian finally:
    def download_audio_process(self):
        # Di start_download_thread:
        # self.download_button.config(state=tk.DISABLED, text="Downloading...") # Nonaktifkan tombol dan ubah teks
        # self.download_progress.pack()
        # threading.Thread(target=self.download_audio_process, daemon=True).start()

        # Di download_audio_process, di bagian finally:
        try:
            url = self.url_entry.get().strip()
            print(f"URL retrieved: '{url}'")
            title = self.custom_title_entry.get().strip()
            author = self.custom_author_entry.get().strip()
            print(f"Title: '{title}', Author: '{author}'")

            if not url:
                self.root.after(0, lambda: self.show_message("Missing URL", warning=True))
                return

            # --- BARIS PENTING YANG HARUS DIPINDAHKAN KE SINI ---
            song_title = download_audio(url, title or None, author or None)
            self.root.after(0, self.refresh_song_list)
            self.root.after(0, lambda: messagebox.showinfo("Downloaded", f"{song_title} has been saved."))
            # --- AKHIR BARIS PENTING ---

        except Exception as e:
            print(f"Error within download_audio_process: {e}") # Pesan error yang lebih jelas
            self.root.after(0, lambda: messagebox.showerror("Download Error", f"An unexpected error occurred: {e}"))
        finally:
            self.root.after(0, self.download_progress.stop)
            self.root.after(0, self.download_progress.pack_forget)
            self.root.after(0, lambda: self.download_button.config(state=tk.NORMAL, text="Download"))

    def show_message(self, text, warning=False):
        if warning:
            self.root.after(0, lambda: messagebox.showwarning("Warning", text))
        else:
            self.root.after(0, lambda: messagebox.showinfo("Info", text))
    def show_message(self, text, warning=False):
        if warning:
            self.root.after(0, lambda: messagebox.showwarning("Warning", text))
        else:
            self.root.after(0, lambda: messagebox.showinfo("Info", text))