#!/usr/bin/env python3
"""
YouTube Live Streamer GUI (Folder Edition)
A tkinter-based GUI application for streaming a folder of videos to YouTube Live in a loop.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
from datetime import datetime
import json
import time
import queue
import platform

class YouTubeStreamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Live Streamer - Folder Loop")
        self.root.geometry("900x800")
        self.root.resizable(True, True)
        
        # Apply dark theme
        self.setup_dark_theme()
        
        # Configuration file
        self.config_file = "stream_config.json"
        
        # Streaming state
        self.streaming = False
        self.ffmpeg_process = None
        self.stream_thread = None
        self.output_queue = queue.Queue()
        
        # Supported video extensions
        self.video_extensions = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.ts', '.wmv')
        
        # Create UI
        self.create_widgets()
        
        # Load saved configuration
        self.load_config()
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Start output reader thread
        self.start_output_reader()
    
    def setup_dark_theme(self):
        """Setup YouTube red theme with rounded corners"""
        self.bg_color = "#0f0f0f"
        self.fg_color = "#ffffff"
        self.entry_bg = "#181818"
        self.entry_fg = "#ffffff"
        self.button_bg = "#FF0000"
        self.button_fg = "#ffffff"
        self.button_hover = "#CC0000"
        self.button_pressed = "#AA0000"
        self.accent_color = "#FF0000"
        self.success_color = "#4caf50"
        self.error_color = "#f44336"
        self.border_color = "#303030"
        
        self.root.configure(bg=self.bg_color)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background=self.bg_color, borderwidth=0)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.entry_fg, borderwidth=0, relief='flat', padding=10)
        style.map('TEntry', fieldbackground=[('focus', self.entry_bg)], bordercolor=[('focus', self.accent_color)])
        style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 30), sticky=(tk.W, tk.E))
        
        tk.Label(title_frame, text="YouTube Live Streamer", font=("Segoe UI", 28, "bold"), bg=self.bg_color, fg=self.accent_color).pack()
        tk.Label(title_frame, text="Loop all videos from a folder continuously", font=("Segoe UI", 11), bg=self.bg_color, fg="#aaaaaa").pack(pady=(8, 0))
        
        # Folder selection section
        section_frame = ttk.Frame(main_frame)
        section_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        section_frame.columnconfigure(1, weight=1)
        
        ttk.Label(section_frame, text="Video Folder:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        
        self.folder_path_var = tk.StringVar()
        folder_frame = ttk.Frame(section_frame)
        folder_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=8)
        folder_frame.columnconfigure(0, weight=1)
        
        entry_frame1 = tk.Frame(folder_frame, bg=self.bg_color)
        entry_frame1.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        entry_frame1.columnconfigure(0, weight=1)
        
        self.folder_path_entry = tk.Entry(entry_frame1, textvariable=self.folder_path_var, font=("Segoe UI", 10), bg=self.entry_bg, fg=self.entry_fg, insertbackground=self.entry_fg, relief=tk.FLAT, borderwidth=0, highlightthickness=2, highlightbackground=self.border_color, highlightcolor=self.accent_color)
        self.folder_path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=12, pady=10)
        
        self.create_rounded_button(folder_frame, "Browse Folder", self.browse_folder, width=15).grid(row=0, column=1)
        
        # Stream Key section
        ttk.Label(section_frame, text="Stream Key:", font=("Segoe UI", 11)).grid(row=1, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        
        self.stream_key_var = tk.StringVar()
        key_frame = ttk.Frame(section_frame)
        key_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=8)
        key_frame.columnconfigure(0, weight=1)
        
        entry_frame2 = tk.Frame(key_frame, bg=self.bg_color)
        entry_frame2.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        entry_frame2.columnconfigure(0, weight=1)
        
        stream_key_entry = tk.Entry(entry_frame2, textvariable=self.stream_key_var, show="*", font=("Segoe UI", 10), bg=self.entry_bg, fg=self.entry_fg, insertbackground=self.entry_fg, relief=tk.FLAT, borderwidth=0, highlightthickness=2, highlightbackground=self.border_color, highlightcolor=self.accent_color)
        stream_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=12, pady=10)
        
        self.show_key_var = tk.BooleanVar()
        ttk.Checkbutton(key_frame, text="Show", variable=self.show_key_var, command=lambda: stream_key_entry.config(show="" if self.show_key_var.get() else "*")).grid(row=0, column=1)
        
        # Control buttons
        self.button_frame = ttk.Frame(main_frame)
        self.button_frame.grid(row=2, column=0, columnspan=3, pady=30)
        
        self.start_button_frame = self.create_rounded_button(self.button_frame, "▶ Start Loop Stream", self.start_stream, width=22, height=2)
        self.start_button_frame.pack(side=tk.LEFT, padx=10)
        
        self.stop_button_frame = self.create_rounded_button(self.button_frame, "⏹ Stop Stream", self.stop_stream, width=20, height=2, disabled=True)
        self.stop_button_frame.pack(side=tk.LEFT, padx=10)
        
        config_frame = ttk.Frame(self.button_frame)
        config_frame.pack(side=tk.LEFT, padx=20)
        self.create_rounded_button(config_frame, "💾 Save Settings", self.save_config, width=16).pack(side=tk.LEFT, padx=6)
        
        # Status
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready")
        self.status_indicator = tk.Label(status_frame, text="●", font=("Segoe UI", 16), bg=self.bg_color, fg=self.success_color)
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(status_frame, textvariable=self.status_var, font=("Segoe UI", 11, "bold"), bg=self.bg_color, fg=self.fg_color).pack(side=tk.LEFT)
        
        # Current file indicator
        self.current_file_var = tk.StringVar(value="No folder selected")
        tk.Label(main_frame, textvariable=self.current_file_var, font=("Consolas", 9), bg=self.bg_color, fg="#888888", wraplength=800).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # Logs
        log_section = ttk.Frame(main_frame)
        log_section.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_section.columnconfigure(0, weight=1)
        log_section.rowconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        log_header = ttk.Frame(log_section)
        log_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        ttk.Label(log_header, text="Stream Logs", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        self.create_rounded_button(log_header, "Clear", self.clear_logs, width=10).pack(side=tk.RIGHT)
        
        self.log_text = scrolledtext.ScrolledText(log_section, height=12, wrap=tk.WORD, state=tk.DISABLED, bg=self.entry_bg, fg=self.fg_color, insertbackground=self.fg_color, font=("Consolas", 9), relief=tk.FLAT, highlightthickness=2, highlightbackground=self.border_color)
        self.log_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    def create_rounded_button(self, parent, text, command, width=15, height=1, disabled=False):
        btn_frame = tk.Frame(parent, bg=self.bg_color)
        width_px = width * 8
        height_px = 42 if height == 2 else 38
        radius = 10
        canvas = tk.Canvas(btn_frame, width=width_px, height=height_px, bg=self.bg_color, highlightthickness=0, relief=tk.FLAT)
        canvas.pack()
        
        btn_color = "#666666" if disabled else self.button_bg
        text_color = "#999999" if disabled else self.button_fg
        
        def draw_rounded_rect(c, x1, y1, x2, y2, r, fill):
            c.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline=fill, width=0)
            c.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline=fill, width=0)
            c.create_oval(x1, y1, x1+r*2, y1+r*2, fill=fill, outline=fill, width=0)
            c.create_oval(x2-r*2, y1, x2, y1+r*2, fill=fill, outline=fill, width=0)
            c.create_oval(x1, y2-r*2, x1+r*2, y2, fill=fill, outline=fill, width=0)
            c.create_oval(x2-r*2, y2-r*2, x2, y2, fill=fill, outline=fill, width=0)

        def redraw(color, txt_color):
            canvas.delete("all")
            draw_rounded_rect(canvas, 0, 0, width_px, height_px, radius, color)
            canvas.create_text(width_px//2, height_px//2, text=text, fill=txt_color, font=("Segoe UI", 10, "bold"))
        
        redraw(btn_color, text_color)
        btn_frame.canvas, btn_frame.command, btn_frame.redraw = canvas, command, redraw
        btn_frame.disabled = disabled

        if not disabled:
            canvas.bind("<Enter>", lambda e: redraw(self.button_hover, self.button_fg))
            canvas.bind("<Leave>", lambda e: redraw(self.button_bg, self.button_fg))
            canvas.bind("<Button-1>", lambda e: command() if command else None)
            canvas.config(cursor="hand2")
        return btn_frame

    def update_btn_state(self, btn, disabled):
        btn.disabled = disabled
        color = "#666666" if disabled else self.button_bg
        txt = "#999999" if disabled else self.button_fg
        btn.redraw(color, txt)
        btn.canvas.config(cursor="" if disabled else "hand2")
        if disabled:
            btn.canvas.unbind("<Enter>")
            btn.canvas.unbind("<Leave>")
            btn.canvas.unbind("<Button-1>")
        else:
            btn.canvas.bind("<Enter>", lambda e: btn.redraw(self.button_hover, self.button_fg))
            btn.canvas.bind("<Leave>", lambda e: btn.redraw(self.button_bg, self.button_fg))
            btn.canvas.bind("<Button-1>", lambda e: btn.command())

    def browse_folder(self):
        directory = filedialog.askdirectory(title="Select Video Folder")
        if directory:
            self.folder_path_var.set(directory)
            self.current_file_var.set(f"Target: {directory}")

    def log_message(self, message):
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        try:
            with open("logs/stream_yt.log", "a", encoding="utf-8") as f:
                f.write(log_entry)
        except: pass

    def start_output_reader(self):
        def read_queue():
            while True:
                try:
                    msg = self.output_queue.get(timeout=0.1)
                    if msg: self.log_message(msg)
                except queue.Empty: continue
                except: break
        threading.Thread(target=read_queue, daemon=True).start()

    def kill_all_ffmpeg(self):
        try:
            if platform.system() == "Windows":
                subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pkill", "-9", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except: pass

    def start_stream(self):
        folder = self.folder_path_var.get().strip()
        key = self.stream_key_var.get().strip()
        
        if not folder or not os.path.isdir(folder):
            return messagebox.showerror("Error", "Please select a valid folder")
        if not key:
            return messagebox.showerror("Error", "Please enter your Stream Key")
        
        self.streaming = True
        self.update_btn_state(self.start_button_frame, True)
        self.update_btn_state(self.stop_button_frame, False)
        self.status_var.set("Starting sequence...")
        self.status_indicator.config(fg=self.accent_color)
        
        self.stream_thread = threading.Thread(target=self.stream_loop, daemon=True)
        self.stream_thread.start()

    def stop_stream(self):
        self.streaming = False
        self.status_var.set("Stopping...")
        self.log_message("Stopping stream and killing processes...")
        if self.ffmpeg_process:
            try: self.ffmpeg_process.terminate()
            except: pass
        self.kill_all_ffmpeg()
        self.update_btn_state(self.stop_button_frame, True)
        self.update_btn_state(self.start_button_frame, False)
        self.status_var.set("Stopped")
        self.status_indicator.config(fg=self.success_color)

    def stream_loop(self):
        folder = self.folder_path_var.get().strip()
        key = self.stream_key_var.get().strip()
        rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{key}"
        
        while self.streaming:
            # Re-scan folder every cycle to pick up new files
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(self.video_extensions)]
            files.sort()
            
            if not files:
                self.log_message("No video files found in folder! Waiting 10 seconds...")
                time.sleep(10)
                continue
                
            self.log_message(f"Found {len(files)} videos. Starting circular queue.")
            
            for video_path in files:
                if not self.streaming: break
                
                filename = os.path.basename(video_path)
                self.root.after(0, lambda f=filename: self.current_file_var.set(f"NOW STREAMING: {f}"))
                self.root.after(0, lambda: self.status_var.set("Streaming Live"))
                self.log_message(f"Streaming: {filename}")
                
                # FFmpeg command (No -stream_loop here, we want to move to next file)
                cmd = [
                    "ffmpeg", "-re", "-i", video_path,
                    "-c:v", "libx264", "-preset", "veryfast", "-b:v", "4000k", "-maxrate", "4000k", "-bufsize", "8000k",
                    "-vf", "scale=1280:720,format=yuv420p", "-g", "60",
                    "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                    "-f", "flv", rtmp_url
                ]
                
                try:
                    self.ffmpeg_process = subprocess.Popen(
                        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                        universal_newlines=True, bufsize=1,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                    )
                    
                    # Read FFmpeg output
                    for line in iter(self.ffmpeg_process.stdout.readline, ''):
                        if not self.streaming: break
                        if "fps=" in line: # Only log actual progress lines occasionally
                            if time.time() % 5 < 0.1: self.output_queue.put(line.strip())
                        elif "Error" in line:
                            self.output_queue.put(line.strip())
                            
                    self.ffmpeg_process.wait()
                    
                except Exception as e:
                    self.log_message(f"Error streaming {filename}: {e}")
                    time.sleep(2)
                
                if self.streaming:
                    self.log_message(f"Finished {filename}. Moving to next...")
                    time.sleep(1) # Small gap between files

        self.root.after(0, lambda: self.current_file_var.set("Stream stopped"))

    def save_config(self):
        config = {"folder_path": self.folder_path_var.get(), "stream_key": self.stream_key_var.get()}
        try:
            with open(self.config_file, "w") as f: json.dump(config, f, indent=4)
            messagebox.showinfo("Success", "Settings saved")
        except Exception as e: messagebox.showerror("Error", str(e))

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.folder_path_var.set(config.get("folder_path", ""))
                    self.stream_key_var.set(config.get("stream_key", ""))
            except: pass

    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_closing(self):
        if self.streaming:
            if messagebox.askokcancel("Quit", "Are you sure?"):
                self.stop_stream()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeStreamerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
