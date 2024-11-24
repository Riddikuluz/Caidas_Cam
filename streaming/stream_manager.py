import subprocess
import os
import time
import signal
from dotenv import load_dotenv

load_dotenv()

ffmpeg_process = None

def start_streaming(stop_event):
    """Inicia el streaming del escritorio usando FFmpeg."""
    global ffmpeg_process
    
    if ffmpeg_process and ffmpeg_process.poll() is None:
        print("⚠️ Streaming ya está en curso.")
        return
    
    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-f", "gdigrab",
        "-offset_x", "1920",  # Coordenada X de inicio
        "-offset_y", "0",     # Coordenada Y de inicio
        "-video_size", "1920x1080",
        "-i", "desktop",
        "-framerate", "30",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-b:v", "800k",
        "-maxrate", "800k",
        "-bufsize", "1200k",
        "-f", "flv",
        f'{os.getenv("INGEST_URL")}{os.getenv("STREAM_KEY")}'
    ]
    
    ffmpeg_process = subprocess.Popen(
        ffmpeg_command,
        stdin=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )

    try:
        print("🎥 Streaming del escritorio iniciado. Esperando mensaje de detención...")
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔ Streaming detenido manualmente.")
    finally:
        stop_streaming()

def stop_streaming():
    global ffmpeg_process
    if ffmpeg_process:
        print("🛑 Intentando detener el proceso de FFmpeg...")
        try:
            if ffmpeg_process.poll() is None:
                ffmpeg_process.send_signal(signal.CTRL_BREAK_EVENT)
                print("🕒 Esperando que el proceso de FFmpeg termine...")
                time.sleep(3)
                if ffmpeg_process.poll() is None:
                    print("⚠️ FFmpeg sigue activo. Intentando forzar la detención...")
                    ffmpeg_process.terminate()
                    time.sleep(1)
                    if ffmpeg_process.poll() is None:
                        print("🔴 Terminando proceso con fuerza...")
                        ffmpeg_process.kill()
            else:
                print("✅ FFmpeg ya ha terminado.")
        except Exception as e:
            print(f"⚠️ Error al intentar detener FFmpeg: {e}")
        finally:
            ffmpeg_process = None
            print("✅ Streaming finalizado.")
    else:
        print("⚠️ No hay un proceso de streaming en ejecución.")
