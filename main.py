import threading
import time
from dotenv import load_dotenv
from fallDetection.run_fall_detection import run_fall_detection
from streaming.response_listener import ResponseListener
from streaming.stream_manager import start_streaming

load_dotenv()

stop_detection_event = threading.Event()

def detection_worker():
    try:
        print("📹 Iniciando detección de caídas...")
        run_fall_detection()
    except Exception as e:
        print(f"⚠️ Error en la detección de caídas: {e}")

def streaming_worker():
    """Hilo encargado de manejar las solicitudes de streaming."""
    listener = ResponseListener(stop_detection_event)
    print("🎧 Escuchando respuestas para streaming...")
    
    while not stop_detection_event.is_set():
        try:
            if listener.response_received:
                print("🎥 Solicitud de inicio de streaming recibida.")
                start_streaming(stop_detection_event)
                print("✅ Streaming finalizado.")
                listener.response_received = False
        except Exception as e:
            print(f"⚠️ Error en el hilo de streaming: {e}")
        time.sleep(1)
    
    print("⏹️ Hilo de streaming detenido.")

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
    finally:
        for thread in threads:
            thread.join()
        print("✅ Sistema finalizado.")

if __name__ == "__main__":
    main()