#!/bin/bash

# Directorio donde se guardan los archivos HLS
OUTPUT_DIR="/home/laura25/Desktop/FLASK/static/hls"
mkdir -p "$OUTPUT_DIR"
rm -f "$OUTPUT_DIR"/*

echo "⏺️ Iniciando transmisión de cámara Pi5 con libcamera + ffmpeg..."

# Comando libcamera-vid piped a ffmpeg para generar el stream HLS
libcamera-vid \
--width 1280 \
--height 720 \
--framerate 25 \
--codec yuv420 \
-t 0 \
-o - | ffmpeg -f rawvideo -pixel_format yuv420p -video_size 1280x720 \
-framerate 25 -i - \
-c:v libx264 -preset ultrafast -f hls \
-hls_time 2 -hls_list_size 10 -hls_flags delete_segments \
"$OUTPUT_DIR/stream.m3u8"
