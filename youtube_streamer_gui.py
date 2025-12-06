#!/usr/bin/env python3
"""
YouTube Live Streamer GUI
A tkinter-based GUI application for streaming video to YouTube Live
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
        self.root.title("YouTube Live Streamer")
        self.root.geometry("900x750")
        self.root.resizable(True, True)
        
        # Apply dark theme
        self.setup_dark_theme()
        
        # Configuration file
        self.config_file = "stream_config.json"
        
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
    
    def setup_dark_theme(self):
        """Setup modern dark theme with light buttons"""
        # Dark theme colors
        self.bg_color = "#1e1e1e"  # Dark background
        self.fg_color = "#ffffff"   # White text
        self.entry_bg = "#2d2d2d"  # Dark entry background
        self.entry_fg = "#ffffff"   # White entry text
        self.button_bg = "#4a9eff"  # Light blue button
        self.button_fg = "#ffffff"  # White button text
        self.button_hover = "#5fb0ff"  # Lighter blue on hover
        self.accent_color = "#00d4ff"  # Cyan accent
        self.success_color = "#4caf50"  # Green for success
        self.error_color = "#f44336"    # Red for errors
        
        # Configure root window
        self.root.configure(bg=self.bg_color)
        
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('TFrame', background=self.bg_color)
        style.configure('TLabel', background=self.bg_color, foreground=self.fg_color)
        style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.entry_fg, 
                       borderwidth=1, relief='solid')
        style.configure('TButton', background=self.button_bg, foreground=self.button_fg,
                       borderwidth=0, focuscolor='none', padding=10)
        style.map('TButton',
                 background=[('active', self.button_hover), ('pressed', self.button_bg)])
        style.configure('TCheckbutton', background=self.bg_color, foreground=self.fg_color)
        style.configure('TCheckbutton', focuscolor='none')
        style.map('TCheckbutton',
                 background=[('selected', self.bg_color)],
                 foreground=[('selected', self.fg_color)])
    
    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(1, weight=1)
        
        # Title with modern styling
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 30), sticky=(tk.W, tk.E))
        
        title_label = tk.Label(
            title_frame,
            text="YouTube Live Streamer",
            font=("Segoe UI", 24, "bold"),
            bg=self.bg_color,
            fg=self.accent_color
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            title_frame,
            text="Stream your videos to YouTube Live",
            font=("Segoe UI", 10),
            bg=self.bg_color,
            fg="#888888"
        )
        subtitle_label.pack(pady=(5, 0))
        
        # Video file selection section
        section_frame = ttk.Frame(main_frame)
        section_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=15)
        section_frame.columnconfigure(1, weight=1)
        
        ttk.Label(section_frame, text="Video File:", font=("Segoe UI", 11)).grid(
            row=0, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        
        self.video_file_var = tk.StringVar()
        video_frame = ttk.Frame(section_frame)
        video_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=8)
        video_frame.columnconfigure(0, weight=1)
        
        self.video_file_entry = ttk.Entry(video_frame, textvariable=self.video_file_var, font=("Segoe UI", 10))
        self.video_file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(video_frame, text="Browse", command=self.browse_video_file, width=12)
        browse_btn.grid(row=0, column=1)
        
        # YouTube Stream Key section
        ttk.Label(section_frame, text="Stream Key:", font=("Segoe UI", 11)).grid(
            row=1, column=0, sticky=tk.W, pady=8, padx=(0, 15))
        
        self.stream_key_var = tk.StringVar()
        key_frame = ttk.Frame(section_frame)
        key_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=8)
        key_frame.columnconfigure(0, weight=1)
        
        stream_key_entry = ttk.Entry(key_frame, textvariable=self.stream_key_var, 
                                     show="*", font=("Segoe UI", 10))
        stream_key_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        self.show_key_var = tk.BooleanVar()
        show_key_check = ttk.Checkbutton(key_frame, text="Show", variable=self.show_key_var,
                                        command=lambda: stream_key_entry.config(
                                            show="" if self.show_key_var.get() else "*"))
        show_key_check.grid(row=0, column=1)
        
        # Control buttons with modern styling
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=3, pady=30)
        
        self.start_button = ttk.Button(
            button_frame, 
            text="▶ Start Stream", 
            command=self.start_stream, 
            width=18
        )
        self.start_button.pack(side=tk.LEFT, padx=8)
        
        self.stop_button = ttk.Button(
            button_frame, 
            text="⏹ Stop Stream", 
            command=self.stop_stream, 
            width=18,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=8)
        
        config_frame = ttk.Frame(button_frame)
        config_frame.pack(side=tk.LEFT, padx=15)
        
        ttk.Button(config_frame, text="💾 Save", command=self.save_config, width=12).pack(side=tk.LEFT, padx=4)
        ttk.Button(config_frame, text="📂 Load", command=self.load_config, width=12).pack(side=tk.LEFT, padx=4)
        
        # Status indicator
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.status_var = tk.StringVar()
        self.status_indicator = tk.Label(
            status_frame,
            text="●",
            font=("Segoe UI", 16),
            bg=self.bg_color,
            fg=self.success_color
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))
        
        status_label = tk.Label(
            status_frame,
            textvariable=self.status_var,
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        status_label.pack(side=tk.LEFT)
        
        # Set initial status
        self.update_status("Ready")
        
        # Log display section
        log_section = ttk.Frame(main_frame)
        log_section.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_section.columnconfigure(0, weight=1)
        log_section.rowconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        log_header = ttk.Frame(log_section)
        log_header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(log_header, text="Stream Logs", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT)
        
        clear_btn = ttk.Button(log_header, text="Clear", command=self.clear_logs, width=10)
        clear_btn.pack(side=tk.RIGHT)
        
        # Log text area with dark theme
        log_frame = ttk.Frame(log_section)
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg=self.entry_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.button_bg,
            selectforeground=self.button_fg,
            font=("Consolas", 9),
            relief=tk.FLAT,
            borderwidth=1,
            highlightthickness=1,
            highlightbackground="#444444",
            highlightcolor=self.accent_color
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def browse_video_file(self):
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv"), ("All files", "*.*")]
        )
        if filename:
            self.video_file_var.set(filename)
    
    def update_status(self, message, color=None):
        """Update status text and indicator color"""
        self.status_var.set(message)
        if color is None:
            # Auto-determine color based on message
            if "Streaming" in message or "Starting" in message:
                color = self.accent_color
            elif "Stopped" in message or "Ready" in message:
                color = self.success_color
            elif "Error" in message or "Stopping" in message:
                color = self.error_color
            elif "Reconnecting" in message or "Verifying" in message:
                color = "#ffa500"  # Orange
            else:
                color = self.fg_color
        self.status_indicator.config(fg=color)
    
    def log_message(self, message):
        """Add a timestamped message to the log display"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Also write to log file
        try:
            with open("logs/stream_yt_log.txt", "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def start_output_reader(self):
        """Start a thread to read output from the queue"""
        def read_queue():
            while True:
                try:
                    message = self.output_queue.get(timeout=0.1)
                    if message:
                        self.log_message(message)
                except queue.Empty:
                    continue
                except Exception:
                    break
        
        reader_thread = threading.Thread(target=read_queue, daemon=True)
        reader_thread.start()
    
    def kill_all_ffmpeg_processes(self):
        """Kill all ffmpeg processes (integrated from kill_ffmpeg.py)"""
        try:
            if platform.system() == "Windows":
                # Find all ffmpeg processes
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if "ffmpeg.exe" in result.stdout:
                    self.log_message("Found ffmpeg processes. Killing them...")
                    subprocess.run(
                        ["taskkill", "/F", "/IM", "ffmpeg.exe"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5,
                        check=False
                    )
                    self.log_message("All ffmpeg processes killed.")
                else:
                    self.log_message("No ffmpeg processes found.")
            else:
                # Unix-like systems
                result = subprocess.run(
                    ["pgrep", "-f", "ffmpeg"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    self.log_message(f"Found {len(pids)} ffmpeg process(es). Killing them...")
                    for pid in pids:
                        if pid:
                            try:
                                subprocess.run(
                                    ["kill", "-9", pid],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    timeout=2,
                                    check=False
                                )
                            except:
                                pass
                    self.log_message("All ffmpeg processes killed.")
                else:
                    self.log_message("No ffmpeg processes found.")
        except Exception as e:
            self.log_message(f"Error killing ffmpeg processes: {e}")
    
    def kill_process_tree(self, process):
        """Kill process and all its children (Windows-compatible)"""
        if process is None:
            return
        
        try:
            if platform.system() == "Windows":
                # On Windows, use taskkill to kill the process tree
                try:
                    # First try graceful termination
                    process.terminate()
                    try:
                        process.wait(timeout=2)
                        return
                    except subprocess.TimeoutExpired:
                        pass
                    
                    # Force kill if graceful termination failed
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=3,
                        check=False
                    )
                except Exception:
                    # If taskkill fails, try direct kill
                    try:
                        process.kill()
                        process.wait(timeout=1)
                    except:
                        pass
            else:
                # On Unix-like systems
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    try:
                        process.wait(timeout=1)
                    except:
                        pass
        except Exception as e:
            # Silently handle errors - process might already be dead
            pass
    
    def validate_inputs(self):
        """Validate that all required inputs are provided"""
        video_file = self.video_file_var.get().strip()
        stream_key = self.stream_key_var.get().strip()
        
        if not video_file:
            messagebox.showerror("Error", "Please select a video file")
            return False
        
        if not os.path.exists(video_file):
            messagebox.showerror("Error", f"Video file not found: {video_file}")
            return False
        
        if not stream_key or stream_key == "YOUR_YOUTUBE_STREAM_KEY":
            messagebox.showerror("Error", "Please enter your YouTube Stream Key")
            return False
        
        return True
    
    def start_stream(self):
        """Start the YouTube streaming process"""
        if not self.validate_inputs():
            return
        
        if self.streaming:
            messagebox.showwarning("Warning", "Stream is already running")
            return
        
        self.streaming = True
        self.restart_count = 0
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.update_status("Starting stream...")
        
        # Start streaming in a separate thread
        self.stream_thread = threading.Thread(target=self.stream_loop, daemon=True)
        self.stream_thread.start()
    
    def stop_stream(self):
        """Stop the YouTube streaming process"""
        if not self.streaming:
            return
        
        self.streaming = False
        self.update_status("Stopping stream...")
        self.log_message("Received stop signal, stopping stream...")
        
        # Disable stop button to prevent multiple clicks
        self.stop_button.config(state=tk.DISABLED)
        
        # Force kill the ffmpeg process immediately
        if self.ffmpeg_process:
            try:
                self.log_message("Terminating ffmpeg process...")
                self.kill_process_tree(self.ffmpeg_process)
                self.ffmpeg_process = None
                self.log_message("FFmpeg process terminated.")
            except Exception as e:
                self.log_message(f"Error stopping ffmpeg: {e}")
        
        # Wait a moment for thread to recognize the stop
        time.sleep(0.5)
        
        # Kill all remaining ffmpeg processes (from kill_ffmpeg.py)
        self.log_message("Checking for any remaining ffmpeg processes...")
        self.kill_all_ffmpeg_processes()
        
        # Wait a bit more to ensure everything is stopped
        time.sleep(0.5)
        
        # Verify streaming is fully stopped
        max_wait = 10  # Maximum 10 seconds
        wait_count = 0
        self.update_status("Verifying stream stopped...")
        while wait_count < max_wait:
            # Check if any ffmpeg processes are still running
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(
                        ["tasklist", "/FI", "IMAGENAME eq ffmpeg.exe", "/FO", "CSV"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if "ffmpeg.exe" not in result.stdout:
                        break
                else:
                    result = subprocess.run(
                        ["pgrep", "-f", "ffmpeg"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if result.returncode != 0:
                        break
            except:
                # If check fails, assume processes are stopped
                break
            
            wait_count += 1
            if wait_count % 2 == 0:  # Update status every second
                self.update_status(f"Verifying stream stopped... ({wait_count/2}s)")
            time.sleep(0.5)
        
        if wait_count >= max_wait:
            self.log_message("Warning: Some processes may still be running. Forcing kill...")
            self.kill_all_ffmpeg_processes()
        
        self.start_button.config(state=tk.NORMAL)
        self.update_status("Stopped")
        self.log_message("Stream stopped by user.")
    
    def stream_loop(self):
        """Main streaming loop with automatic restart on errors"""
        video_file = self.video_file_var.get().strip()
        stream_key = self.stream_key_var.get().strip()
        
        while self.streaming:
            self.restart_count += 1
            
            if self.restart_count == 1:
                self.log_message(f"Starting YouTube stream (attempt {self.restart_count})...")
                self.root.after(0, lambda: self.update_status("Streaming..."))
            else:
                self.log_message(f"Stream disconnected. Restarting stream (attempt {self.restart_count})...")
                self.root.after(0, lambda: self.update_status(f"Reconnecting... (attempt {self.restart_count})"))
                # Wait 5 seconds before restarting
                for _ in range(5):
                    if not self.streaming:
                        break
                    time.sleep(1)
            
            if not self.streaming:
                break
            
            # Build ffmpeg command
            rtmp_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
            
            ffmpeg_cmd = [
                "ffmpeg",
                "-re",  # Read input at native frame rate
                "-stream_loop", "-1",  # Loop video indefinitely
                "-i", video_file,
                "-c:v", "libx264",
                "-preset", "superfast",
                "-b:v", "4500k",
                "-maxrate", "4500k",
                "-bufsize", "9000k",
                "-vf", "scale=1920:1080",
                "-r", "30",
                "-pix_fmt", "yuv420p",
                "-g", "60",
                "-c:a", "aac",
                "-b:a", "128k",
                "-ar", "44100",
                "-f", "flv",
                rtmp_url
            ]
            
            try:
                self.log_message(f"Running ffmpeg command...")
                
                # Create process with proper flags for Windows
                popen_kwargs = {
                    "stdout": subprocess.PIPE,
                    "stderr": subprocess.STDOUT,
                    "universal_newlines": True,
                    "bufsize": 1
                }
                
                if platform.system() == "Windows":
                    popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
                
                self.ffmpeg_process = subprocess.Popen(ffmpeg_cmd, **popen_kwargs)
                
                # Read output in a separate thread to avoid blocking
                def read_output():
                    try:
                        for line in iter(self.ffmpeg_process.stdout.readline, ''):
                            if not self.streaming or self.ffmpeg_process is None:
                                break
                            if line.strip():
                                try:
                                    self.output_queue.put(line.strip(), timeout=0.1)
                                except queue.Full:
                                    pass
                    except Exception:
                        pass
                
                output_thread = threading.Thread(target=read_output, daemon=True)
                output_thread.start()
                
                # Wait for process to complete, but check streaming flag periodically
                while self.ffmpeg_process.poll() is None:
                    if not self.streaming:
                        # Force kill if we're stopping
                        self.kill_process_tree(self.ffmpeg_process)
                        break
                    time.sleep(0.1)
                
                exit_code = self.ffmpeg_process.poll()
                
                if not self.streaming:
                    self.log_message("Stream stopped by user.")
                    break
                
                if exit_code is not None:
                    self.log_message(f"FFmpeg exited with code {exit_code}. Will restart...")
                
            except FileNotFoundError:
                self.root.after(0, lambda: messagebox.showerror(
                    "Error", 
                    "FFmpeg not found. Please install FFmpeg and ensure it's in your PATH."
                ))
                self.root.after(0, self.stop_stream)
                break
            except Exception as e:
                self.log_message(f"Error running ffmpeg: {e}")
                if self.streaming:
                    time.sleep(5)
        
        # Cleanup
        self.root.after(0, lambda: self.update_status("Stopped"))
        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
    
    def save_config(self):
        """Save configuration to JSON file"""
        config = {
            "video_file": self.video_file_var.get(),
            "stream_key": self.stream_key_var.get()
        }
        
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=4)
            self.log_message("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully")
        except Exception as e:
            self.log_message(f"Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
    
    def load_config(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                
                if "video_file" in config:
                    self.video_file_var.set(config["video_file"])
                if "stream_key" in config:
                    self.stream_key_var.set(config["stream_key"])
                
                self.log_message("Configuration loaded successfully")
            except Exception as e:
                self.log_message(f"Error loading configuration: {e}")
    
    def on_closing(self):
        """Handle window closing event - prevent closing while streaming"""
        if self.streaming:
            messagebox.showwarning(
                "Cannot Close", 
                "Stream is currently running. Please click 'Stop Stream' to stop the stream before closing the application."
            )
            # Don't close the window - just return
            return
        else:
            self.root.destroy()


def main():
    root = tk.Tk()
    app = YouTubeStreamerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()

