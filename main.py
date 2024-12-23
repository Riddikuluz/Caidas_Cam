import threading
import time
import subprocess
import os
from dotenv import load_dotenv
from response_listener import ResponseListener

load_dotenv()

stop_detection_event = threading.Event()
stop_streaming_event = threading.Event()

ffmpeg_process = None
is_streaming = False

def detection_worker():
    try:
        print("Iniciando deteccion de caidas...")
        subprocess.run(["python", "./fall_detector.py"])
    except Exception as e:
        print(f"Error en la deteccion de caidas: {e}")

def streaming_worker():
    global is_streaming
    listener = ResponseListener(stop_streaming_event)
    print("Escuchando respuestas para streaming...")

    while not stop_detection_event.is_set():
        try:
            if listener.response_received and not stop_streaming_event.is_set() and not is_streaming:
                print("Solicitud de inicio de streaming recibida.")
                start_streaming(listener.stream_type)
                listener.response_received = False
        except Exception as e:
            print(f"Error en el hilo de streaming: {e}")
        time.sleep(1)

    print("Hilo de streaming detenido.")

def stop_streaming():
    global ffmpeg_process
    global is_streaming

    if ffmpeg_process:
        try:
            ffmpeg_process.terminate()  
            time.sleep(1)
            if ffmpeg_process.poll() is None:
                ffmpeg_process.kill()  
            ffmpeg_process.wait()
            print("FFmpeg detenido correctamente.")
        except Exception as e:
            print(f"Error al detener FFmpeg: {e}")
        finally:
            ffmpeg_process = None
            is_streaming = False
    else:
        print("No hay un proceso FFmpeg activo.")


def start_streaming(stream_type):
    global ffmpeg_process
    stop_streaming_event.clear()
    stop_streaming()

    global is_streaming

    if stream_type == "monitor":
        ingest_url = os.getenv("INGEST_URL_Monitor")
        stream_key = os.getenv("STREAM_KEY_Monitor")
    elif stream_type == "alerta":
        ingest_url = os.getenv("INGEST_URL_Alerta")
        stream_key = os.getenv("STREAM_KEY_Alerta")
    elif stream_type == "ambiental":
        ingest_url = os.getenv("INGEST_URL_Ambiental")
        stream_key = os.getenv("STREAM_KEY_Ambiental")
    else:
        print("Tipo de streaming no valido.")
        return

    ffmpeg_command = [
        "ffmpeg",
        "-y",
        "-f", "x11grab",
        "-video_size", "1280x720",
        "-i", ":0.0",
        "-framerate", "24",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-pix_fmt", "yuv420p",
        "-b:v", "800k",
        "-maxrate", "800k",
        "-bufsize", "1200k",
        "-f", "flv",
        f"{ingest_url}{stream_key}"
    ]

    print(f"Iniciando streaming ({stream_type}) con comando: {' '.join(ffmpeg_command)}")
    is_streaming = True

    try:
        ffmpeg_process = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        while not stop_streaming_event.is_set():
            if ffmpeg_process.poll() is not None:
                print("FFmpeg termino inesperadamente.")
                break
            time.sleep(1)

        if stop_streaming_event.is_set() and ffmpeg_process.poll() is None:
            print("Deteniendo streaming con comando 'q'.")
            ffmpeg_process.stdin.write(b'q\n')
            ffmpeg_process.stdin.flush()
    except Exception as e:
        print(f"Error durante el streaming: {e}")
    finally:
        stop_streaming()

def main():
    print("Iniciando sistema de deteccion de caidas...")

    detection_thread = threading.Thread(target=detection_worker, daemon=True)
    streaming_thread = threading.Thread(target=streaming_worker, daemon=True)

    detection_thread.start()
    streaming_thread.start()

    try:
        while not stop_detection_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nFinalizando sistema...")
        stop_detection_event.set()
        stop_streaming_event.set()
    finally:
        detection_thread.join()
        streaming_thread.join()
        print("Sistema finalizado.")

if __name__ == "__main__":
    main()
