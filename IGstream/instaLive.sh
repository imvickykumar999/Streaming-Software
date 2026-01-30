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

if [ -z "$INSTAGRAM_RTMP_URL" ]; then
    echo "Error: INSTAGRAM_RTMP_URL not set in config.env"
    exit 1
fi

if [ -z "$INSTAGRAM_STREAM_KEY" ] || [ "$INSTAGRAM_STREAM_KEY" = "YOUR_INSTAGRAM_STREAM_KEY" ]; then
    echo "Error: INSTAGRAM_STREAM_KEY not set in config.env"
    exit 1
fi

# Check if video file exists
if [ ! -f "$VIDEO_FILE" ]; then
    echo "Error: Video file '$VIDEO_FILE' not found in current directory"
    echo "Download a video using: python3 download_youtube.py \"URL\""
    exit 1
fi

# CREATE LOGS DIRECTORY IF IT DOES NOT EXIST
mkdir -p logs

# use this parameter to crop and scale video for Instagram vertical format
# -vf "crop=in_h*9/16:in_h,scale=720:1280" \

ffmpeg -re -stream_loop -1 -i "$VIDEO_FILE" \
-c:v libx264 -preset superfast -b:v 2000k -maxrate 2000k -bufsize 4000k \
-pix_fmt yuv420p -g 60 -c:a aac -b:a 128k -ar 44100 \
-f flv -rtmp_live live "${INSTAGRAM_RTMP_URL}${INSTAGRAM_STREAM_KEY}" > logs/stream_ig_log.txt 2>&1
