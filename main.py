from fallDetection.run_fall_detection import run_fall_detection
from aws.send_alert import send_alert
from aws.response_listener import wait_for_response
from aws.stream_manager import start_streaming
import os
from dotenv import load_dotenv

load_dotenv()

RESPONSE_TIMEOUT = os.getenv("RESPONSE_TIMEOUT")
STREAM_TIMEOUT = os.getenv("STREAM_TIMEOUT")

def main():
    print("🏁 Iniciando sistema de detección de caídas...")

    while True:
        # Etapa 1: Detección de caídas
        fall_detected = run_fall_detection()
        if not fall_detected:
            print("✅ No se detectaron caídas. Continuando...")
            continue  # Reinicia el bucle para seguir monitoreando

        # Etapa 2: Enviar mensaje de alerta
        print("⚠️ Caída detectada. Enviando alerta...")
        send_alert()

        # Etapa 3: Esperar respuesta para iniciar streaming
        print("⏳ Esperando autorización para iniciar streaming...")
        if wait_for_response(timeout = 60):  
            print("✅ Autorización recibida. Iniciando streaming...")
            start_streaming(timeout = 300)
            print("🏁 Streaming completado. Reiniciando detección...")
        else:
            print("❌ No se recibió autorización. Continuando con la detección...")
            continue  # Volver al inicio del bucle

if __name__ == "__main__":
    main()