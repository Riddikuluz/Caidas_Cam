import cv2
import subprocess
import time
import os
from dotenv import load_dotenv

load_dotenv()
STREAM_TIMEOUT = os.getenv("STREAM_TIMEOUT")

def start_streaming(timeout=300):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo acceder a la cámara.")
        return

    ffmpeg_command = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', '640x480',
        '-r', '30',
        '-i', '-',
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-preset', 'veryfast',
        '-f', 'flv',
        '-tune', 'zerolatency',
        '-b:v', '800k',
        '-maxrate', '800k',
        '-bufsize', '1200k',
        f'{os.getenv("INGEST_URL")}{os.getenv("STREAM_KEY")}'
    ]

    process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE)
    start_time = time.time()

    try:
        while time.time() - start_time < timeout:
            ret, frame = cap.read()
            if not ret:
                break
            frame_resized = cv2.resize(frame, (640, 480))
            process.stdin.write(frame_resized.tobytes())
    finally:
        cap.release()
        process.stdin.close()
        process.wait()
