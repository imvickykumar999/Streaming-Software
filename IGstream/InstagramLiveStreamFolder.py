#!/usr/bin/env python3
"""
Instagram Live Streamer GUI (Folder Edition)
A tkinter-based GUI application for streaming a folder of videos to Instagram Live 
in a vertical format (9:16) and a continuous circular loop.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import json
import time
import queue
import platform
from datetime import datetime

class InstagramStreamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Instagram Live Streamer - Folder Loop")
        self.root.geometry("900x850")
        self.root.resizable(True, True)
        
        # Configuration file
        self.config_file = "ig_stream_config.json"
        
        # Theme Colors (Instagram Pink/Violet/Purple)
        self.setup_instagram_theme()
        
        # Streaming state
        self.streaming = False
        self.ffmpeg_process = None
        self.stream_thread = None
        self.output_queue = queue.Queue()
        
        # Supported video extensions
        self.video_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.flv', '.ts')
        
        # Create UI
        self.create_widgets()
        
        # Load saved configuration
        self.load_config()
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Start output reader thread
        self.start_output_reader()
    
    def setup_instagram_theme(self):
        """Setup Instagram-inspired pink/violet/dark theme"""
        self.bg_color = "#121212"
        self.fg_color = "#ffffff"
        self.entry_bg = "#262626"
        self.accent_pink = "#E1306C"
        self.accent_purple = "#833AB4"
        self.button_bg = "#C13584"
        self.button_hover = "#E1306C"
        self.success_color = "#4caf50"
        self.error_color = "#f44336"
        self.border_color = "#333333"
        
        self.root.configure(bg=self.bg_color)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg_color, borderwidth=0)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        
        # Header
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 30), sticky=(tk.W, tk.E))
        
        tk.Label(title_frame, text="Instagram Live", font=("Segoe UI", 32, "bold"), bg=self.bg_color, fg=self.accent_pink).pack()
        tk.Label(title_frame, text="Loop all videos in folder (Auto-Vertical Format)", font=("Segoe UI", 11), bg=self.bg_color, fg="#999999").pack(pady=(5, 0))
        
        # Inputs
        section_frame = ttk.Frame(main_frame)
        section_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        section_frame.columnconfigure(1, weight=1)
        
        # 1. Video Folder
        ttk.Label(section_frame, text="Video Folder:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.folder_path_var = tk.StringVar()
        v_frame = ttk.Frame(section_frame)
        v_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        v_frame.columnconfigure(0, weight=1)
        
        self.folder_entry = self.create_styled_entry(v_frame, self.folder_path_var)
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        self.create_rounded_button(v_frame, "Browse Folder", self.browse_folder, width=15).grid(row=0, column=1)
        
        # 2. RTMP URL (Instagram usually provides this or you use a 3rd party tool)
        ttk.Label(section_frame, text="RTMP URL:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.rtmp_url_var = tk.StringVar(value="")
        self.rtmp_entry = self.create_styled_entry(section_frame, self.rtmp_url_var)
        self.rtmp_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # 3. Stream Key
        ttk.Label(section_frame, text="Stream Key:", font=("Segoe UI", 10, "bold")).grid(row=2, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.stream_key_var = tk.StringVar()
        k_frame = ttk.Frame(section_frame)
        k_frame.grid(row=2, column=1, sticky=(tk.W, tk.E))
        k_frame.columnconfigure(0, weight=1)
        
        self.key_entry = self.create_styled_entry(k_frame, self.stream_key_var, show="*")
        self.key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        
        self.show_key_var = tk.BooleanVar()
        ttk.Checkbutton(k_frame, text="Show", variable=self.show_key_var, 
                       command=lambda: self.key_entry.config(show="" if self.show_key_var.get() else "*")).grid(row=0, column=1)

        # Controls
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=2, column=0, columnspan=3, pady=25)
        
        self.start_btn = self.create_rounded_button(self.button_frame, "▶ Start Loop Stream", self.start_stream, width=22, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = self.create_rounded_button(self.button_frame, "⏹ Stop Stream", self.stop_stream, width=18, height=2, disabled=True)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        cfg_frame = ttk.Frame(main_frame)
        cfg_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        self.create_rounded_button(cfg_frame, "Save Settings", self.save_config, width=16).pack(side=tk.LEFT, padx=5)

        # Status Bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.status_indicator = tk.Label(status_frame, text="●", font=("Segoe UI", 14), bg=self.bg_color, fg=self.success_color)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready to stream")
        tk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10, "bold"), bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        # Currently Playing Indicator
        self.current_video_var = tk.StringVar(value="No folder selected")
        tk.Label(main_frame, textvariable=self.current_video_var, font=("Consolas", 9), bg=self.bg_color, fg="#888888", wraplength=800).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(5, 10))

        # Log Window
        log_label_frame = ttk.Frame(main_frame)
        log_label_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))
        ttk.Label(log_label_frame, text="Streaming Console Output", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.create_rounded_button(log_label_frame, "Clear Logs", self.clear_logs, width=10).pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=10, bg=self.entry_bg, fg=self.fg_color, font=("Consolas", 9), relief=tk.FLAT, state=tk.DISABLED)
        self.log_text.grid(row=7, column=0, columnspan=3, sticky=(tk.N, tk.S, tk.E, tk.W))
        main_frame.rowconfigure(7, weight=1)

    def create_styled_entry(self, parent, variable, show=None):
        return tk.Entry(parent, textvariable=variable, show=show, font=("Segoe UI", 10), bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color, relief=tk.FLAT, borderwidth=0, highlightthickness=1, highlightbackground=self.border_color, highlightcolor=self.accent_pink)

    def create_rounded_button(self, parent, text, command, width=15, height=1, disabled=False):
        btn_frame = tk.Frame(parent, bg=self.bg_color)
        width_px, height_px = width * 8, (40 if height == 2 else 32)
        radius = 8
        canvas = tk.Canvas(btn_frame, width=width_px, height=height_px, bg=self.bg_color, highlightthickness=0)
        canvas.pack()
        
        def draw(fill, txt_col):
            canvas.delete("all")
            canvas.create_rectangle(radius, 0, width_px-radius, height_px, fill=fill, outline="")
            canvas.create_rectangle(0, radius, width_px, height_px-radius, fill=fill, outline="")
            canvas.create_oval(0, 0, radius*2, radius*2, fill=fill, outline="")
            canvas.create_oval(width_px-radius*2, 0, width_px, radius*2, fill=fill, outline="")
            canvas.create_oval(0, height_px-radius*2, radius*2, height_px, fill=fill, outline="")
            canvas.create_oval(width_px-radius*2, height_px-radius*2, width_px, height_px, fill=fill, outline="")
            canvas.create_text(width_px//2, height_px//2, text=text, fill=txt_col, font=("Segoe UI", 9, "bold"))

        btn_frame.draw, btn_frame.disabled, btn_frame.command, btn_frame.canvas = draw, disabled, command, canvas
        draw("#555555" if disabled else self.button_bg, "#999999" if disabled else self.fg_color)

        if not disabled:
            canvas.bind("<Enter>", lambda e: draw(self.button_hover, self.fg_color))
            canvas.bind("<Leave>", lambda e: draw(self.button_bg, self.fg_color))
            canvas.bind("<Button-1>", lambda e: command() if command else None)
            canvas.config(cursor="hand2")
        return btn_frame

    def _set_btn_state(self, btn, disabled):
        btn.disabled = disabled
        bg, fg = ("#555555", "#999999") if disabled else (self.button_bg, self.fg_color)
        btn.draw(bg, fg)
        btn.canvas.config(cursor="" if disabled else "hand2")
        if disabled:
            btn.canvas.unbind("<Enter>")
            btn.canvas.unbind("<Leave>")
            btn.canvas.unbind("<Button-1>")
        else:
            btn.canvas.bind("<Enter>", lambda e: btn.draw(self.button_hover, self.fg_color))
            btn.canvas.bind("<Leave>", lambda e: btn.draw(self.button_bg, self.fg_color))
            btn.canvas.bind("<Button-1>", lambda e: btn.command())

    def browse_folder(self):
        dir_path = filedialog.askdirectory(title="Select Video Folder")
        if dir_path:
            self.folder_path_var.set(dir_path)
            self.current_video_var.set(f"Selected: {dir_path}")

    def log_message(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{ts}] {msg}\n"
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_output_reader(self):
        def reader():
            while True:
                try:
                    msg = self.output_queue.get(timeout=0.1)
                    if msg: self.log_message(msg)
                except queue.Empty: continue
                except: break
        threading.Thread(target=reader, daemon=True).start()

    def start_stream(self):
        folder = self.folder_path_var.get().strip()
        key = self.stream_key_var.get().strip()
        if not folder or not os.path.isdir(folder):
            return messagebox.showerror("Error", "Please select a valid folder")
        if not key:
            return messagebox.showerror("Error", "Enter Stream Key")
        
        self.streaming = True
        self._set_btn_state(self.start_btn, True)
        self._set_btn_state(self.stop_btn, False)
        self.status_var.set("Starting Folder Loop...")
        self.status_indicator.config(fg=self.accent_pink)
        
        self.stream_thread = threading.Thread(target=self.stream_loop, daemon=True)
        self.stream_thread.start()

    def stop_stream(self):
        self.streaming = False
        self.status_var.set("Stopping...")
        if self.ffmpeg_process:
            try:
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.ffmpeg_process.pid)], capture_output=True)
                else:
                    self.ffmpeg_process.terminate()
            except: pass
        
        self._set_btn_state(self.start_btn, False)
        self._set_btn_state(self.stop_btn, True)
        self.status_var.set("Stream Stopped")
        self.status_indicator.config(fg=self.success_color)

    def stream_loop(self):
        folder = self.folder_path_var.get().strip()
        url = self.rtmp_url_var.get().strip()
        key = self.stream_key_var.get().strip()
        full_url = f"{url}{key}"
        
        while self.streaming:
            # Re-scan folder for videos
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(self.video_extensions)]
            files.sort()
            
            if not files:
                self.log_message("No video files found! Waiting...")
                time.sleep(5)
                continue
            
            for video_path in files:
                if not self.streaming: break
                
                filename = os.path.basename(video_path)
                self.root.after(0, lambda f=filename: self.current_video_var.set(f"NOW LIVE: {f}"))
                self.log_message(f"Starting Video: {filename}")
                
                # FFmpeg Instagram Vertical Command
                # crop=in_h*9/16:in_h crops the center to vertical, then we scale to 720:1280
                cmd = [
                    "ffmpeg", "-re", "-i", video_path,
                    "-vf", "crop=in_h*9/16:in_h,scale=720:1280", 
                    "-c:v", "libx264", "-preset", "superfast", "-b:v", "3000k", "-maxrate", "3000k", "-bufsize", "6000k",
                    "-pix_fmt", "yuv420p", "-g", "60",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                    "-f", "flv", full_url
                ]
                
                try:
                    self.ffmpeg_process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                        universal_newlines=True, bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                    )
                    
                    for line in iter(self.ffmpeg_process.stdout.readline, ''):
                        if not self.streaming: break
                        if "fps=" in line and time.time() % 4 < 0.1: # Throttled logs
                            self.output_queue.put(line.strip())
                        elif "Error" in line:
                            self.output_queue.put(line.strip())
                            
                    self.ffmpeg_process.wait()
                except Exception as e:
                    self.log_message(f"FFmpeg Error: {e}")
                
                if self.streaming:
                    self.log_message(f"Finished {filename}. Transitioning...")
                    time.sleep(1)

        self.root.after(0, lambda: self.current_video_var.set("Stream cycle ended"))

    def save_config(self):
        data = {"folder": self.folder_path_var.get(), "url": self.rtmp_url_var.get(), "key": self.stream_key_var.get()}
        try:
            with open(self.config_file, "w") as f: json.dump(data, f)
            messagebox.showinfo("Success", "Settings saved")
        except Exception as e: messagebox.showerror("Error", str(e))

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.folder_path_var.set(data.get("folder", ""))
                    self.rtmp_url_var.set(data.get("url", ""))
                    self.stream_key_var.set(data.get("key", ""))
            except: pass

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_closing(self):
        if self.streaming:
            if messagebox.askokcancel("Quit", "Stop stream and quit?"):
                self.stop_stream()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramStreamerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
