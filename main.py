import threading
import time
import subprocess
import os
from dotenv import load_dotenv
from func.response_listener import ResponseListener

load_dotenv()

stop_detection_event = threading.Event()

ffmpeg_processes = {"monitor": None, "alerta": None}

def detection_worker():
    try:
        print("Iniciando detección de caídas...")
        subprocess.run(["python", "./func/fall_detector.py"])
    except Exception as e:
        print(f"Error en la detección de caídas: {e}")

def streaming_worker():
    listener = ResponseListener()
    print("Escuchando respuestas para streaming...")

    while not stop_detection_event.is_set():
        try:
            if listener.response_received:
                stream_type = listener.stream_type
                if listener.action == "start":
                    print(f"Solicitud de inicio para {stream_type} recibida.")
                    t = threading.Thread(target=start_streaming, args=(stream_type,), daemon=True)
                    t.start()
                elif listener.action == "stop":
                    print(f"Solicitud de detención para {stream_type} recibida.")
                    stop_streaming(stream_type)
                listener.response_received = False
                listener.action = None
                listener.stream_type = None
        except Exception as e:
            print(f"Error en el hilo de streaming: {e}")
        time.sleep(1)
    print("Hilo de streaming detenido.")

def stop_streaming(stream_type):
    global ffmpeg_processes
    proc = ffmpeg_processes.get(stream_type)
    if proc:
        try:
            proc.terminate()
            time.sleep(1)
            if proc.poll() is None:
                proc.kill()
            proc.wait()
            print(f"FFmpeg ({stream_type}) detenido correctamente.")
        except Exception as e:
            print(f"Error al detener FFmpeg ({stream_type}): {e}")
        finally:
            ffmpeg_processes[stream_type] = None
    else:
        print(f"No hay un proceso FFmpeg activo para {stream_type}.")

def start_streaming(stream_type):
    global ffmpeg_processes
    if ffmpeg_processes.get(stream_type):
        print(f"Ya existe un streaming activo para {stream_type}, deteniéndolo...")
        stop_streaming(stream_type)

    if stream_type == "monitor":
        ingest_url = os.getenv("INGEST_URL_Monitor")
        stream_key = os.getenv("STREAM_KEY_Monitor")
    elif stream_type == "alerta":
        ingest_url = os.getenv("INGEST_URL_Alerta")
        stream_key = os.getenv("STREAM_KEY_Alerta")
    else:
        print("Tipo de streaming no válido.")
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
    try:
        proc = subprocess.Popen(
            ffmpeg_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        ffmpeg_processes[stream_type] = proc

        while True:
            if proc.poll() is not None:
                print(f"FFmpeg ({stream_type}) terminó inesperadamente.")
                break
            time.sleep(1)
    except Exception as e:
        print(f"Error durante el streaming ({stream_type}): {e}")
    finally:
        stop_streaming(stream_type)

def main():
    print("Iniciando sistema de detección de caídas...")

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
        for stream in list(ffmpeg_processes.keys()):
            stop_streaming(stream)
    finally:
        detection_thread.join()
        streaming_thread.join()
        print("Sistema finalizado.")

if __name__ == "__main__":
    main()
