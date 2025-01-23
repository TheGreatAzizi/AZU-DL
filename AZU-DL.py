import yt_dlp
import os
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import socket
import webbrowser

default_download_folder = os.path.join(os.path.expanduser('~'), 'Downloads')

def check_internet_connection():
    try:
        socket.create_connection(("www.youtube.com", 80), timeout=5)
        return True
    except (socket.timeout, socket.gaierror, ConnectionRefusedError):
        return False

def check_disk_space(path):
    total, used, free = shutil.disk_usage(path)
    return free // (1024 * 1024)

def download_video_gui(url, audio_only, download_folder, subtitles, progress_var, progress_bar, status_label, log_text, filename_label, total_size_label):
    if not check_internet_connection():
        messagebox.showerror("No Internet Connection", "You are not connected to the internet or, if you are in Iran, please turn on your VPN.")
        return

    def progress_hook(d):
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes > 0:
                percentage = (downloaded_bytes / total_bytes) * 100
                progress_var.set(percentage)
                progress_bar.update_idletasks()
                download_speed = d.get('speed', 0) / 1024
                time_remaining = (total_bytes - downloaded_bytes) / d.get('speed', 1)
                speed_label.config(text=f"Speed: {download_speed:.2f} KB/s")
                time_left_label.config(text=f"Time Remaining: {int(time_remaining)}s")
            log_text.insert(tk.END, f"Downloading: {d.get('filename', 'Unknown')}\n")
            log_text.yview(tk.END)
        elif d['status'] == 'finished':
            messagebox.showinfo("Success", f"Download complete! File saved in {download_folder}")
            log_text.insert(tk.END, f"Download completed: {d.get('filename', 'Unknown')}\n")
            log_text.yview(tk.END)

    try:
        filename = url.split("/")[-1].split("?")[0]
        filename_label.config(text=f"Filename: {filename}")
        total_size_label.config(text="Total Size: Not Available Yet")
        ydl_opts = {
            'format': 'bestaudio' if audio_only else 'best',
            'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'extract_flat': True,
        }
        if subtitles:
            ydl_opts.update({
                'subtitleslangs': ['en'],
                'writesubtitles': True,
                'writeautomaticsub': True,
            })
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            filename = info_dict.get('title', 'Unknown') + '.' + info_dict.get('ext', 'mp4')
            total_size = info_dict.get('filesize', None)
            if total_size:
                total_size_label.config(text=f"Total Size: {total_size / (1024 * 1024):.2f} MB")
            filename_label.config(text=f"Filename: {filename}")
            ydl.download([url])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download video: {str(e)}")

def start_download():
    def download_thread():
        urls = url_entry.get("1.0", "end").strip().split("\n")
        audio_only = audio_var.get()
        subtitles = subtitles_var.get()
        download_folder = folder_path.get()
        if not check_internet_connection():
            messagebox.showerror("No Internet Connection", "You are not connected to the internet or, if you are in Iran, please turn on your VPN.")
            return
        if not urls or not download_folder:
            messagebox.showwarning("Input Error", "Please provide video URL(s) and select a download folder.")
            return
        for url in urls:
            if url.strip():
                progress_var.set(0)
                try:
                    download_video_gui(url.strip(), audio_only, download_folder, subtitles, progress_var, progress_bar, status_label, log_text, filename_label, total_size_label)
                except Exception as e:
                    messagebox.showerror("Error", f"An error occurred: {str(e)}")
    download_threading = threading.Thread(target=download_thread)
    download_threading.start()

def select_folder():
    folder = filedialog.askdirectory(initialdir=default_download_folder)
    if folder:
        folder_path.set(folder)

def add_context_menu(widget):
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Cut", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_command(label="Copy", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Paste", command=lambda: widget.event_generate("<<Paste>>"))
    def show_context_menu(event):
        menu.tk_popup(event.x_root, event.y_root)
    widget.bind("<Button-3>", show_context_menu)
    widget.bind("<Control-v>", lambda e: widget.event_generate("<<Paste>>"))
    widget.bind("<Control-c>", lambda e: widget.event_generate("<<Copy>>"))
    widget.bind("<Control-x>", lambda e: widget.event_generate("<<Cut>>"))

app = tk.Tk()
app.title("AZU-DL | YouTube Downloader")
app.resizable(False, False)
app.grid_columnconfigure(0, weight=1)
tk.Label(app, text="Enter YouTube Video URL(s) (one per line):").grid(row=0, column=0, pady=5, sticky="w")
url_entry = tk.Text(app, height=5, width=50)
url_entry.grid(row=1, column=0, pady=5, padx=5)
add_context_menu(url_entry)
tk.Label(app, text="Select Download Folder:").grid(row=2, column=0, pady=5, sticky="w")
folder_path = tk.StringVar(value=default_download_folder)
folder_entry = tk.Entry(app, textvariable=folder_path, width=40)
folder_entry.grid(row=3, column=0, padx=5, pady=5, sticky="w")
tk.Button(app, text="Browse", command=select_folder).grid(row=3, column=1, padx=5, pady=5)
audio_var = tk.BooleanVar()
subtitles_var = tk.BooleanVar()

def toggle_subtitle_checkbox():
    if audio_var.get():
        subtitle_checkbox.config(state=tk.DISABLED)
    else:
        subtitle_checkbox.config(state=tk.NORMAL)

def toggle_audio_checkbox():
    if subtitles_var.get():
        audio_checkbox.config(state=tk.DISABLED)
    else:
        audio_checkbox.config(state=tk.NORMAL)

audio_checkbox = tk.Checkbutton(app, text="Audio Only", variable=audio_var, command=toggle_subtitle_checkbox)
audio_checkbox.grid(row=4, column=0, pady=5, sticky="w")
subtitle_checkbox = tk.Checkbutton(app, text="Download Subtitles", variable=subtitles_var, command=toggle_audio_checkbox)
subtitle_checkbox.grid(row=5, column=0, pady=5, sticky="w")
tk.Label(app, text="Download Progress:").grid(row=6, column=0, pady=5, sticky="w")
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(app, variable=progress_var, maximum=100)
progress_bar.grid(row=7, column=0, padx=10, pady=5, sticky="ew")
status_label = tk.Label(app, text="Waiting for download...", anchor="w")
status_label.grid(row=8, column=0, pady=5, sticky="w")
speed_label = tk.Label(app, text="Speed: 0 KB/s")
speed_label.grid(row=9, column=0, pady=5, sticky="w")
time_left_label = tk.Label(app, text="Time Remaining: 0s")
time_left_label.grid(row=10, column=0, pady=5, sticky="w")
total_size_label = tk.Label(app, text="Total Size: Not Available Yet")
total_size_label.grid(row=11, column=0, pady=5, sticky="w")
tk.Label(app, text="Log:").grid(row=12, column=0, pady=5, sticky="w")
log_text = tk.Text(app, height=5, width=50)
log_text.grid(row=13, column=0, pady=5, padx=5)
filename_label = tk.Label(app, text="Filename: Not started")
filename_label.grid(row=14, column=0, pady=5, sticky="w")
tk.Button(app, text="Start Download", command=start_download, bg="green", fg="white").grid(row=15, column=0, pady=10)

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to stop downloads and exit?"):
        app.destroy()
        
def open_update_link():
    webbrowser.open("https://github.com/TheGreatAzizi/AZU-DL")

tk.Button(app, text="Update", command=open_update_link, bg="blue", fg="white").grid(row=15, column=1, pady=10, padx=5)

app.protocol("WM_DELETE_WINDOW", on_closing)
app.mainloop()
