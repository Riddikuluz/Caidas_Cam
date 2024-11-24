import threading
import time
from dotenv import load_dotenv
from fallDetection.run_fall_detection import run_fall_detection
from aws.send_alert import send_alert
from aws.response_listener import ResponseListener
from aws.stream_manager import start_streaming 

load_dotenv()

stop_detection_event = threading.Event()

def detection_worker():
    """Hilo para ejecutar la detección de caídas."""
    while not stop_detection_event.is_set():
        try:
            fall_detected = run_fall_detection()
            if fall_detected:
                print("⚠️ Caída detectada. Enviando alerta...")
                send_alert()
                fall_detected = False
        except Exception as e:
            print(f"⚠️ Error en run_fall_detection: {e}")
        time.sleep(1)  # Reducir la carga del CPU

    print("⏹️ Hilo de detección detenido.")

def streaming_worker():
    listener = ResponseListener(stop_detection_event)
    while not stop_detection_event.is_set():
        if listener.response_received:
            print("🎥 Solicitud de inicio de streaming recibida.")
            start_streaming(stop_detection_event)
            print("✅ Streaming finalizado.")
            main()
            listener.response_received = False
        time.sleep(1)
    
    print("⏹️ Hilo de streaming detenido.")


def main():
    """Función principal para iniciar los hilos."""
    print("🏁 Iniciando sistema de detección de caídas...")
    
    # Hilo para la detección de caídas
    detection_thread = threading.Thread(target=detection_worker, daemon=True)
    detection_thread.start()

    # Hilo para el streaming
    streaming_thread = threading.Thread(target=streaming_worker, daemon=True)
    streaming_thread.start()

    try:
        while True:
            time.sleep(1)  # Mantener el programa corriendo
    except KeyboardInterrupt:
        print("\n⛔ Finalizando sistema...")
        stop_detection_event.set()  # Detener los hilos y el streaming
        if detection_thread.is_alive():
            detection_thread.join()
        if streaming_thread.is_alive():
            streaming_thread.join()
    finally:
        print("✅ Sistema finalizado.")

if __name__ == "__main__":
    main()