#!/usr/bin/env python3
"""
Instagram Live Streamer GUI
A tkinter-based GUI application for streaming video to Instagram Live
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
        self.root.title("Instagram Live Streamer")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Configuration file
        self.config_file = "ig_stream_config.json"
        
        # Theme Colors (Instagram Pink/Violet/Purple)
        self.setup_instagram_theme()
        
        # Streaming state
        self.streaming = False
        self.ffmpeg_process = None
        self.restart_count = 0
        self.stream_thread = None
        self.output_queue = queue.Queue()
        
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
        self.bg_color = "#121212"       # Dark background
        self.fg_color = "#ffffff"       # White text
        self.entry_bg = "#262626"       # Lighter dark for entries
        self.entry_fg = "#ffffff"
        
        # Instagram Gradient Colors
        self.accent_pink = "#E1306C"    # Pink
        self.accent_purple = "#833AB4"  # Purple
        self.accent_orange = "#F77737"  # Orange
        
        self.button_bg = "#C13584"      # Main Button Pink
        self.button_hover = "#E1306C"   # Brighter Pink
        self.button_pressed = "#833AB4" # Deep Purple
        
        self.success_color = "#4caf50"  # Green
        self.error_color = "#f44336"    # Red
        self.border_color = "#333333"
        
        self.root.configure(bg=self.bg_color)
        
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=self.bg_color, borderwidth=0)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        
        # Configure scrollbar style
        style.configure("Vertical.TScrollbar", gripcount=0, background=self.entry_bg, darkcolor=self.bg_color, lightcolor=self.bg_color, bordercolor=self.bg_color, troughcolor=self.bg_color)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        
        # Header / Logo Area
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 30), sticky=(tk.W, tk.E))
        
        title_label = tk.Label(
            title_frame,
            text="Instagram Live",
            font=("Segoe UI", 32, "bold"),
            bg=self.bg_color,
            fg=self.accent_pink
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Stream to your followers in vertical format",
            font=("Segoe UI", 11),
            bg=self.bg_color,
            fg="#999999"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Inputs Section
        section_frame = ttk.Frame(main_frame)
        section_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        section_frame.columnconfigure(1, weight=1)
        
        # 1. Video File
        ttk.Label(section_frame, text="Video Source:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        self.video_file_var = tk.StringVar()
        v_frame = ttk.Frame(section_frame)
        v_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        v_frame.columnconfigure(0, weight=1)
        
        self.video_entry = self.create_styled_entry(v_frame, self.video_file_var)
        self.video_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10), pady=5)
        self.create_rounded_button(v_frame, "Browse", self.browse_video, width=10).grid(row=0, column=1)
        
        # 2. RTMP URL
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
        
        self.start_btn = self.create_rounded_button(self.button_frame, "▶ Go Live", self.start_stream, width=18, height=2)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        # FIXED: Initial state should be disabled (True)
        self.stop_btn = self.create_rounded_button(self.button_frame, "⏹ Stop Stream", self.stop_stream, width=18, height=2, disabled=True)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Config management
        cfg_frame = ttk.Frame(main_frame)
        cfg_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        self.create_rounded_button(cfg_frame, "Save Settings", self.save_config, width=14).pack(side=tk.LEFT, padx=5)
        self.create_rounded_button(cfg_frame, "Load Settings", self.load_config, width=14).pack(side=tk.LEFT, padx=5)

        # Status Bar
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        self.status_indicator = tk.Label(status_frame, text="●", font=("Segoe UI", 14), bg=self.bg_color, fg=self.success_color)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready to stream")
        tk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 10, "bold"), bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        # Log Window
        log_label_frame = ttk.Frame(main_frame)
        log_label_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))
        ttk.Label(log_label_frame, text="Streaming Console Output", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.create_rounded_button(log_label_frame, "Clear Logs", self.clear_logs, width=10).pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(
            main_frame, height=12, bg=self.entry_bg, fg=self.fg_color, 
            font=("Consolas", 9), relief=tk.FLAT, borderwidth=0, highlightthickness=1, 
            highlightbackground=self.border_color, state=tk.DISABLED
        )
        self.log_text.grid(row=6, column=0, columnspan=3, sticky=(tk.N, tk.S, tk.E, tk.W))
        main_frame.rowconfigure(6, weight=1)

    def create_styled_entry(self, parent, variable, show=None):
        return tk.Entry(
            parent, textvariable=variable, show=show, font=("Segoe UI", 10),
            bg=self.entry_bg, fg=self.entry_fg, insertbackground=self.fg_color,
            relief=tk.FLAT, borderwidth=0, highlightthickness=1,
            highlightbackground=self.border_color, highlightcolor=self.accent_pink
        )

    def create_rounded_button(self, parent, text, command, width=15, height=1, disabled=False):
        btn_frame = tk.Frame(parent, bg=self.bg_color)
        width_px = width * 8
        height_px = 40 if height == 2 else 32
        radius = 8
        
        canvas = tk.Canvas(btn_frame, width=width_px, height=height_px, bg=self.bg_color, highlightthickness=0)
        canvas.pack()
        
        def draw(fill, txt_col):
            canvas.delete("all")
            canvas.create_oval(0, 0, radius*2, radius*2, fill=fill, outline="")
            canvas.create_oval(width_px-radius*2, 0, width_px, radius*2, fill=fill, outline="")
            canvas.create_oval(0, height_px-radius*2, radius*2, height_px, fill=fill, outline="")
            canvas.create_oval(width_px-radius*2, height_px-radius*2, width_px, height_px, fill=fill, outline="")
            canvas.create_rectangle(radius, 0, width_px-radius, height_px, fill=fill, outline="")
            canvas.create_rectangle(0, radius, width_px, height_px-radius, fill=fill, outline="")
            canvas.create_text(width_px//2, height_px//2, text=text, fill=txt_col, font=("Segoe UI", 9, "bold"))

        btn_frame.draw = draw
        btn_frame.disabled = disabled
        btn_frame.command = command
        btn_frame.canvas = canvas

        # Initial Draw
        initial_bg = "#555555" if disabled else self.button_bg
        initial_fg = "#999999" if disabled else self.fg_color
        draw(initial_bg, initial_fg)

        def on_enter(e):
            if not btn_frame.disabled: draw(self.button_hover, self.fg_color)
        def on_leave(e):
            if not btn_frame.disabled: draw(self.button_bg, self.fg_color)
        def on_click(e):
            if not btn_frame.disabled and btn_frame.command: btn_frame.command()

        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_click)
        if not disabled: canvas.config(cursor="hand2")
            
        return btn_frame

    def _set_btn_state(self, btn, disabled):
        """Update button state and redraw correctly"""
        btn.disabled = disabled
        bg = "#555555" if disabled else self.button_bg
        fg = "#999999" if disabled else self.fg_color
        btn.draw(bg, fg)
        btn.canvas.config(cursor="" if disabled else "hand2")

    def browse_video(self):
        file = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.mov *.avi *.mkv"), ("All", "*.*")])
        if file: self.video_file_var.set(file)

    def update_status(self, msg, color=None):
        self.status_var.set(msg)
        if not color:
            if "LIVE" in msg: color = self.accent_pink
            elif "Error" in msg: color = self.error_color
            else: color = self.success_color
        self.status_indicator.config(fg=color)

    def log_message(self, msg):
        ts = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{ts}] {msg}\n"
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, full_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        try:
            with open("logs/insta_stream.log", "a") as f: f.write(full_msg)
        except: pass

    def start_output_reader(self):
        def reader():
            while True:
                try:
                    msg = self.output_queue.get(timeout=0.1)
                    if msg: self.log_message(msg)
                except queue.Empty: continue
        threading.Thread(target=reader, daemon=True).start()

    def start_stream(self):
        if not self.video_file_var.get() or not self.stream_key_var.get():
            messagebox.showerror("Missing Data", "Please select a video and enter your Stream Key.")
            return
        
        self.streaming = True
        # Toggle buttons
        self._set_btn_state(self.start_btn, True)
        self._set_btn_state(self.stop_btn, False)
        
        self.update_status("Starting Instagram Live...")
        self.stream_thread = threading.Thread(target=self.run_ffmpeg, daemon=True)
        self.stream_thread.start()

    def stop_stream(self):
        self.streaming = False
        self.update_status("Stopping...")
        if self.ffmpeg_process:
            try:
                if platform.system() == "Windows":
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.ffmpeg_process.pid)], capture_output=True)
                else:
                    self.ffmpeg_process.terminate()
            except: pass
        
        self.ffmpeg_process = None
        # Toggle buttons back
        self._set_btn_state(self.start_btn, False)
        self._set_btn_state(self.stop_btn, True)
        self.update_status("Stream Stopped")

    def run_ffmpeg(self):
        video = self.video_file_var.get()
        url = self.rtmp_url_var.get()
        key = self.stream_key_var.get()
        
        # Instagram vertical format command
        cmd = [
            "ffmpeg", "-re", "-stream_loop", "-1", "-i", video,
            "-vf", "crop=in_h*9/16:in_h,scale=720:1280", 
            "-c:v", "libx264", "-preset", "superfast", "-b:v", "2500k",
            "-maxrate", "2500k", "-bufsize", "5000k", "-pix_fmt", "yuv420p",
            "-g", "60", "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
            "-f", "flv", f"{url}{key}"
        ]

        self.log_message("Launching FFmpeg...")
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                universal_newlines=True, bufsize=1
            )
            
            self.root.after(0, lambda: self.update_status("LIVE on Instagram", self.accent_pink))

            for line in iter(self.ffmpeg_process.stdout.readline, ''):
                if not self.streaming: break
                if line.strip(): self.output_queue.put(line.strip())
            
            self.ffmpeg_process.wait()
        except Exception as e:
            self.log_message(f"Execution Error: {str(e)}")
        
        if self.streaming:
            self.root.after(0, self.stop_stream)

    def save_config(self):
        data = {"video": self.video_file_var.get(), "url": self.rtmp_url_var.get(), "key": self.stream_key_var.get()}
        with open(self.config_file, "w") as f: json.dump(data, f)
        self.log_message("Settings saved.")

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.video_file_var.set(data.get("video", ""))
                    self.rtmp_url_var.set(data.get("url", ""))
                    self.stream_key_var.set(data.get("key", ""))
                self.log_message("Settings loaded.")
            except: pass

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_closing(self):
        if self.streaming:
            if messagebox.askokcancel("Quit", "Stream is active. Force quit?"):
                self.stop_stream()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = InstagramStreamerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()