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
import re
import webbrowser
import urllib.parse

class YouTubeStreamerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Live Streamer")
        self.root.geometry("1200x900")
        self.root.resizable(True, True)
        
        # Try to import tkinterweb for HTML rendering
        self.tkinterweb_available = False
        try:
            import tkinterweb
            self.tkinterweb_available = True
            self.tkinterweb = tkinterweb
        except ImportError:
            self.tkinterweb_available = False
        
        # Configuration file
        self.config_file = "stream_config.json"
        
        # Streaming state
        self.streaming = False
        self.ffmpeg_process = None
        self.restart_count = 0
        self.stream_thread = None
        self.output_queue = queue.Queue()
        self.video_frame_widget = None
        
        # Create UI
        self.create_widgets()
        
        # Load saved configuration
        self.load_config()
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Start output reader thread
        self.start_output_reader()
    
    def create_widgets(self):
        # Create paned window for split view
        paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left pane - Controls and settings
        left_frame = ttk.Frame(paned, padding="10")
        paned.add(left_frame, weight=1)
        
        # Right pane - Video display
        right_frame = ttk.Frame(paned, padding="10")
        paned.add(right_frame, weight=1)
        
        # Configure grid weights for left frame
        left_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(left_frame, text="YouTube Live Streamer", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # YouTube Studio URL input
        ttk.Label(left_frame, text="YouTube Studio URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.youtube_url_var = tk.StringVar()
        url_frame = ttk.Frame(left_frame)
        url_frame.grid(row=1, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        url_frame.columnconfigure(0, weight=1)
        
        self.youtube_url_entry = ttk.Entry(url_frame, textvariable=self.youtube_url_var, width=40)
        self.youtube_url_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(url_frame, text="Load Video", command=self.load_youtube_video).grid(row=0, column=1)
        
        # Video file selection
        ttk.Label(left_frame, text="Video File:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.video_file_var = tk.StringVar()
        video_frame = ttk.Frame(left_frame)
        video_frame.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        video_frame.columnconfigure(0, weight=1)
        
        self.video_file_entry = ttk.Entry(video_frame, textvariable=self.video_file_var, width=40)
        self.video_file_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(video_frame, text="Browse", command=self.browse_video_file).grid(row=0, column=1)
        
        # YouTube Stream Key
        ttk.Label(left_frame, text="YouTube Stream Key:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.stream_key_var = tk.StringVar()
        stream_key_entry = ttk.Entry(left_frame, textvariable=self.stream_key_var, 
                                     show="*", width=40)
        stream_key_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Show/Hide stream key button
        self.show_key_var = tk.BooleanVar()
        show_key_check = ttk.Checkbutton(left_frame, text="Show Key", 
                                         variable=self.show_key_var,
                                         command=lambda: stream_key_entry.config(
                                             show="" if self.show_key_var.get() else "*"))
        show_key_check.grid(row=3, column=2, sticky=tk.E, padx=(5, 0))
        
        # Control buttons frame
        button_frame = ttk.Frame(left_frame)
        button_frame.grid(row=4, column=0, columnspan=3, pady=20)
        
        self.start_button = ttk.Button(button_frame, text="Start Stream", 
                                       command=self.start_stream, width=15)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop Stream", 
                                      command=self.stop_stream, width=15, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Save Config", 
                  command=self.save_config, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Load Config", 
                  command=self.load_config, width=15).pack(side=tk.LEFT, padx=5)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(left_frame, textvariable=self.status_var, 
                                font=("Arial", 10, "bold"))
        status_label.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(0, 5))
        
        # Log display
        ttk.Label(left_frame, text="Stream Logs:").grid(row=6, column=0, sticky=tk.W, pady=(10, 5))
        
        log_frame = ttk.Frame(left_frame)
        log_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(7, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=50, 
                                                   wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear logs button
        ttk.Button(left_frame, text="Clear Logs", 
                  command=self.clear_logs).grid(row=8, column=0, columnspan=3, pady=5)
        
        # Right pane - Video display
        ttk.Label(right_frame, text="Live Stream Preview", 
                 font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Video display frame
        self.video_display_frame = ttk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=2)
        self.video_display_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        # Placeholder for video
        self.video_placeholder = ttk.Label(
            self.video_display_frame, 
            text="Enter YouTube Studio URL and click 'Load Video'\nto display the live stream here",
            font=("Arial", 10),
            justify=tk.CENTER
        )
        self.video_placeholder.pack(expand=True, fill=tk.BOTH)
    
    def extract_video_id(self, url):
        """Extract video ID from YouTube Studio URL"""
        # Pattern for YouTube Studio URL: https://studio.youtube.com/video/VIDEO_ID/livestreaming
        patterns = [
            r'studio\.youtube\.com/video/([a-zA-Z0-9_-]+)',
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def load_youtube_video(self):
        """Load and display YouTube video from Studio URL"""
        url = self.youtube_url_var.get().strip()
        
        if not url:
            messagebox.showwarning("Warning", "Please enter a YouTube Studio URL")
            return
        
        video_id = self.extract_video_id(url)
        
        if not video_id:
            messagebox.showerror("Error", "Could not extract video ID from URL.\n"
                                 "Please enter a valid YouTube Studio URL.\n"
                                 "Example: https://studio.youtube.com/video/e18cavUkogI/livestreaming")
            return
        
        self.log_message(f"Loading video with ID: {video_id}")
        
        # Create embed URL for live stream
        embed_url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
        
        # Remove placeholder
        if self.video_placeholder:
            self.video_placeholder.destroy()
            self.video_placeholder = None
        
        # Remove existing video widget if any
        if self.video_frame_widget:
            self.video_frame_widget.destroy()
            self.video_frame_widget = None
        
        # Try to use tkinterweb if available
        if self.tkinterweb_available:
            try:
                self.video_frame_widget = self.tkinterweb.HtmlFrame(
                    self.video_display_frame,
                    messages_enabled=False
                )
                self.video_frame_widget.pack(fill=tk.BOTH, expand=True)
                
                # Create HTML with iframe
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            margin: 0;
                            padding: 0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            height: 100vh;
                            background: #000;
                        }}
                        iframe {{
                            width: 100%;
                            height: 100%;
                            border: none;
                        }}
                    </style>
                </head>
                <body>
                    <iframe src="{embed_url}" 
                            frameborder="0" 
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                            allowfullscreen>
                    </iframe>
                </body>
                </html>
                """
                self.video_frame_widget.load_html(html_content)
                self.log_message(f"Video loaded successfully (ID: {video_id})")
            except Exception as e:
                self.log_message(f"Error loading video with tkinterweb: {e}")
                self._create_fallback_video_display(video_id, embed_url)
        else:
            self._create_fallback_video_display(video_id, embed_url)
    
    def _create_fallback_video_display(self, video_id, embed_url):
        """Create fallback video display when tkinterweb is not available"""
        # Create a frame with link and instructions
        fallback_frame = ttk.Frame(self.video_display_frame)
        fallback_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        info_label = ttk.Label(
            fallback_frame,
            text=f"Video ID: {video_id}\n\n"
                 "To view the live stream, click the button below\nto open it in your default browser.\n\n"
                 "For embedded video support, install tkinterweb:\n"
                 "pip install tkinterweb",
            font=("Arial", 10),
            justify=tk.CENTER
        )
        info_label.pack(pady=20)
        
        open_button = ttk.Button(
            fallback_frame,
            text="Open Video in Browser",
            command=lambda: webbrowser.open(embed_url)
        )
        open_button.pack(pady=10)
        
        # Also open automatically
        webbrowser.open(embed_url)
        self.log_message(f"Opened video in browser (ID: {video_id})")
    
    def browse_video_file(self):
        filename = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.flv"), ("All files", "*.*")]
        )
        if filename:
            self.video_file_var.set(filename)
    
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
        self.status_var.set("Starting stream...")
        
        # Start streaming in a separate thread
        self.stream_thread = threading.Thread(target=self.stream_loop, daemon=True)
        self.stream_thread.start()
    
    def stop_stream(self):
        """Stop the YouTube streaming process"""
        if not self.streaming:
            return
        
        self.streaming = False
        self.status_var.set("Stopping stream...")
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
        self.status_var.set("Verifying stream stopped...")
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
                self.status_var.set(f"Verifying stream stopped... ({wait_count/2}s)")
            time.sleep(0.5)
        
        if wait_count >= max_wait:
            self.log_message("Warning: Some processes may still be running. Forcing kill...")
            self.kill_all_ffmpeg_processes()
        
        self.start_button.config(state=tk.NORMAL)
        self.status_var.set("Stopped")
        self.log_message("Stream stopped by user.")
    
    def stream_loop(self):
        """Main streaming loop with automatic restart on errors"""
        video_file = self.video_file_var.get().strip()
        stream_key = self.stream_key_var.get().strip()
        
        while self.streaming:
            self.restart_count += 1
            
            if self.restart_count == 1:
                self.log_message(f"Starting YouTube stream (attempt {self.restart_count})...")
                self.root.after(0, lambda: self.status_var.set("Streaming..."))
            else:
                self.log_message(f"Stream disconnected. Restarting stream (attempt {self.restart_count})...")
                self.root.after(0, lambda: self.status_var.set(f"Reconnecting... (attempt {self.restart_count})"))
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
        self.root.after(0, lambda: self.status_var.set("Stopped"))
        self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: self.stop_button.config(state=tk.DISABLED))
    
    def save_config(self):
        """Save configuration to JSON file"""
        config = {
            "video_file": self.video_file_var.get(),
            "stream_key": self.stream_key_var.get(),
            "youtube_url": self.youtube_url_var.get()
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
                if "youtube_url" in config:
                    self.youtube_url_var.set(config["youtube_url"])
                    # Auto-load video if URL is present
                    if config["youtube_url"]:
                        self.root.after(500, self.load_youtube_video)
                
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

