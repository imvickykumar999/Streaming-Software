># `Streaming Software` : [`Demo Stream`](https://youtu.be/BzArIRqk7Ks)
>
>     Solution of : "Start sending us your video from your streaming software to go live" on YouTube.
>
><img width="1534" height="1023" alt="image" src="https://github.com/user-attachments/assets/003f65e1-6aec-4ebd-95c5-5b0d6a6ecc09" />
><img width="1535" height="983" alt="image" src="https://github.com/user-attachments/assets/c888dda4-adb2-4a56-b325-a928fcfe34db" />

## Features

- **GUI Application**: Easy-to-use tkinter interface for streaming to YouTube Live
- **Live Stream Preview**: View your YouTube live stream directly in the application
- **YouTube Studio URL Support**: Enter your YouTube Studio URL to load and preview the stream
- **Automatic Restart**: Automatically restarts stream on disconnection
- **Configuration Management**: Save and load stream settings
- **Real-time Logging**: View stream logs in real-time within the application
- **Video File Support**: Stream any video file format supported by FFmpeg

## Requirements

1. **Python 3.6+** (tkinter is usually included)
2. **FFmpeg** - Must be installed and available in your system PATH
   - Download from: https://ffmpeg.org/download.html
   - Windows: Add FFmpeg to your system PATH after installation
3. **tkinterweb** (Optional) - For embedded video display within the GUI
   - Install with: `pip install tkinterweb`
   - If not installed, videos will open in your default browser instead

## Usage

### GUI Application (Recommended)

1. Run the GUI application:
   ```bash
   python youtube_streamer_gui.py
   ```

2. Configure your stream:
   - Enter your YouTube Studio URL (e.g., `https://studio.youtube.com/video/e18cavUkogI/livestreaming`) and click "Load Video" to preview
   - Click "Browse" to select your video file to stream
   - Enter your YouTube Stream Key (get it from YouTube Studio > Go Live > Stream Settings)
   - Optionally click "Save Config" to save your settings

3. Start streaming:
   - Click "Start Stream" to begin streaming
   - Monitor the logs in the application window
   - Click "Stop Stream" when you want to end the stream

### Bash Script (Alternative)

If you prefer using the bash script:

1. Create a `config.env` file with:
   ```bash
   YT_FILE="your_video.mp4"
   YOUTUBE_STREAM_KEY="your_stream_key_here"
   ```

2. Run the script:
   ```bash
   bash stream_youtube.sh
   ```

## Getting Your YouTube Stream Key

1. Go to YouTube Studio (https://studio.youtube.com)
2. Click "Go Live" or "Create" > "Go Live"
3. Go to "Stream Settings"
4. Copy your "Stream Key"
5. Paste it into the application

## Notes

- The application will automatically restart the stream if it disconnects
- Logs are saved to `logs/stream_yt_log.txt`
- Configuration is saved to `stream_config.json`
- The stream uses 1920x1080 resolution at 30fps with 4500k video bitrate
- **YouTube Studio URL Format**: The application accepts URLs like:
  - `https://studio.youtube.com/video/VIDEO_ID/livestreaming`
  - `https://www.youtube.com/watch?v=VIDEO_ID`
  - `https://youtu.be/VIDEO_ID`
- If `tkinterweb` is installed, the video will be displayed in an iframe within the GUI. Otherwise, it will open in your default browser.
