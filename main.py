import threading
import time
import subprocess
import os
import signal
from dotenv import load_dotenv
from fallDetection.run_fall_detection import run_fall_detection
from fallDetection.response_listener import ResponseListener

load_dotenv()

stop_detection_event = threading.Event()
stop_streaming_event = threading.Event()

ffmpeg_process = None

def detection_worker():
    try:
        print("📹 Iniciando detección de caídas...")
        run_fall_detection()
    except Exception as e:
        print(f"⚠️ Error en la detección de caídas: {e}")

def streaming_worker():
    listener = ResponseListener(stop_streaming_event)
    print("🎧 Escuchando respuestas para streaming...")
    
    while not stop_detection_event.is_set():
        try:
            if listener.response_received and not stop_streaming_event.is_set():
                print("🎥 Solicitud de inicio de streaming recibida.")
                start_streaming()
                listener.response_received = False
        except Exception as e:
            print(f"⚠️ Error en el hilo de streaming: {e}")
        time.sleep(1)
    
    print("⏹️ Hilo de streaming detenido.")

def start_streaming():
    global ffmpeg_process
    stop_streaming_event.clear()

    stop_streaming()

    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-f", "gdigrab",
        "-offset_x", "0",
        "-offset_y", "0",
        "-video_size", "640x480",
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

    print(f"Iniciando streaming con comando: {' '.join(ffmpeg_command)}")

    try:
        ffmpeg_process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )

        while not stop_streaming_event.is_set():
            if ffmpeg_process.poll() is not None:
                print("⚠️ FFmpeg terminó inesperadamente.")
                break
            time.sleep(1)
    except Exception as e:
        print(f"⚠️ Error durante el streaming: {e}")
    finally:
        stop_streaming()

def stop_streaming():
    global ffmpeg_process

    if ffmpeg_process:
        print("⏹️ Intentando detener FFmpeg...")
        try:
            if ffmpeg_process.poll() is None:
                ffmpeg_process.send_signal(signal.CTRL_BREAK_EVENT)
                time.sleep(2)
                if ffmpeg_process.poll() is None:
                    print("⚠️ FFmpeg sigue activo. Forzando terminación...")
                    ffmpeg_process.terminate()
                    time.sleep(2)
                    if ffmpeg_process.poll() is None:
                        ffmpeg_process.kill()
            ffmpeg_process.wait()
        except Exception as e:
            print(f"⚠️ Error al detener FFmpeg: {e}")
        finally:
            ffmpeg_process = None
            print("✅ FFmpeg detenido.")
    else:
        print("🔍 No hay un proceso FFmpeg activo.")

def main():
    print("🏁 Iniciando sistema de detección de caídas...")
    
    threads = []

    detection_thread = threading.Thread(target=detection_worker, daemon=True)
    threads.append(detection_thread)

    streaming_thread = threading.Thread(target=streaming_worker, daemon=True)
    threads.append(streaming_thread)

    for thread in threads:
        thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⛔ Finalizando sistema...")
        stop_detection_event.set()
        stop_streaming_event.set()
    finally:
        for thread in threads:
            thread.join()
        print("✅ Sistema finalizado.")

if __name__ == "__main__":
    main()
