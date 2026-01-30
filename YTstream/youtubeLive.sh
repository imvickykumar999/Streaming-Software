#!/bin/bash

# Load configuration from config.env
if [ -f "config.env" ]; then
    source config.env
else
    echo "Error: config.env file not found. Please create it with your stream keys."
    exit 1
fi

# Check if required variables are set
if [ -z "$VIDEO_FILE" ]; then
    echo "Error: VIDEO_FILE not set in config.env"
    exit 1
fi

if [ -z "$YOUTUBE_STREAM_KEY" ] || [ "$YOUTUBE_STREAM_KEY" = "YOUR_YOUTUBE_STREAM_KEY" ]; then
    echo "Error: YOUTUBE_STREAM_KEY not set in config.env"
    exit 1
fi

# Check if video file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "Error: Video file '$VIDEO_FILE' not found in current directory"
    echo "Download a video using: python3 download_youtube.py \"URL\""
    exit 1
fi

ffmpeg -re -stream_loop -1 -i "$VIDEO_FILE" \
-c:v libx264 -preset superfast -b:v 6800k -maxrate 6800k -bufsize 13600k \
-pix_fmt yuv420p -g 60 -c:a aac -b:a 128k -ar 44100 \
-f flv "rtmp://a.rtmp.youtube.com/live2/$YOUTUBE_STREAM_KEY" > logs/stream_yt.log 2>&1
