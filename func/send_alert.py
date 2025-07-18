from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import os
from dotenv import load_dotenv
import json
import time
import logging

load_dotenv()

# Configurar logging específico para este módulo
logger = logging.getLogger(__name__)

# Variables de configuración
CLIENT_ID = os.getenv("CLIENT_ID")
ENDPOINT = os.getenv("ENDPOINT")
TOPIC = os.getenv("TOPIC")
CA_PATH = os.getenv("CA_PATH")
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")

def validate_mqtt_config():
    """Valida que todas las variables de configuración MQTT estén presentes"""
    required_vars = {
        "CLIENT_ID": CLIENT_ID,
        "ENDPOINT": ENDPOINT,
        "TOPIC": TOPIC,
        "CA_PATH": CA_PATH,
        "CERT_PATH": CERT_PATH,
        "KEY_PATH": KEY_PATH
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        logger.error(f"Variables de entorno MQTT faltantes: {missing}")
        return False
    
    # Verificar que los archivos de certificados existen
    cert_files = {"CA_PATH": CA_PATH, "CERT_PATH": CERT_PATH, "KEY_PATH": KEY_PATH}
    for name, path in cert_files.items():
        if not os.path.exists(path):
            logger.error(f"Archivo de certificado no encontrado {name}: {path}")
            return False
    
    return True

def publish_mqtt(max_retries=3, retry_delay=2):
    """Publica mensaje MQTT con reintentos y timeout"""
    if not validate_mqtt_config():
        logger.error("Configuración MQTT inválida")
        return False
    
    client = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Intento {attempt + 1} de conexión MQTT...")
            
            # Crear cliente con ID único para evitar conflictos
            unique_client_id = f"{CLIENT_ID}_{int(time.time())}"
            client = AWSIoTMQTTClient(unique_client_id)
            client.configureEndpoint(ENDPOINT, 8883)
            client.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
            
            # Configurar timeouts más conservadores
            client.configureConnectDisconnectTimeout(15)  # 15 segundos
            client.configureMQTTOperationTimeout(10)      # 10 segundos
            client.configureAutoReconnectBackoffTime(1, 32, 20)  # Backoff exponencial
            client.configureOfflinePublishQueueing(-1)    # Queue infinita
            client.configureDrainingFrequency(2)          # 2 Hz
            
            # Conectar
            if not client.connect():
                logger.error("Error al conectar con AWS IoT")
                continue
            
            # Crear mensaje con información adicional
            message = {
                "id_dispositivo": "camara_fall_detector",
                "tipificacion": "caida",
                "mensaje": "¡Caída detectada por sistema de visión computacional!",
                "timestamp": int(time.time()),
                "severity": "HIGH",
                "location": "sala_monitoreo",
                "attempt": attempt + 1
            }
            
            # Publicar mensaje con QoS 1 para garantizar entrega
            message_json = json.dumps(message, ensure_ascii=False)
            success = client.publish(TOPIC, message_json, 1)
            
            if not success:
                logger.error("Error al publicar mensaje")
                client.disconnect()
                continue
            
            # Pequeña pausa para asegurar que el mensaje se envíe
            time.sleep(0.5)
            client.disconnect()
            logger.info("Alerta enviada con éxito")
            return True
            
        except Exception as e:
            logger.error(f"Error en intento {attempt + 1}: {e}")
            if client:
                try:
                    client.disconnect()
                except:
                    pass  # Ignorar errores al desconectar
                    
            if attempt < max_retries - 1:
                logger.info(f"Reintentando en {retry_delay} segundos...")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 10)  # Backoff exponencial limitado
            else:
                logger.error("Agotados todos los intentos de envío")
    
    return False

def send_alert():
    """Función principal para enviar alerta"""
    try:
        logger.info("Iniciando envío de alerta de caída...")
        success = publish_mqtt()
        if not success:
            logger.error("Falló el envío de la alerta MQTT")
            return False
        return True
    except Exception as e:
        logger.error(f"Error crítico en send_alert: {e}")
        return False

# Función de prueba para validar configuración
def test_mqtt_connection():
    """Prueba la conexión MQTT sin enviar alerta real"""
    try:
        if not validate_mqtt_config():
            return False
            
        logger.info("Probando conexión MQTT...")
        client = AWSIoTMQTTClient(f"{CLIENT_ID}_test_{int(time.time())}")
        client.configureEndpoint(ENDPOINT, 8883)
        client.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
        client.configureConnectDisconnectTimeout(10)
        
        if client.connect():
            logger.info("Conexión MQTT exitosa")
            client.disconnect()
            return True
        else:
            logger.error("Falló la conexión MQTT")
            return False
            
    except Exception as e:
        logger.error(f"Error en test de conexión MQTT: {e}")
        return False

if __name__ == "__main__":
    # Permitir ejecución directa para pruebas
    import logging
    logging.basicConfig(level=logging.INFO)
    
    if test_mqtt_connection():
        print("✅ Configuración MQTT válida")
    else:
        print("❌ Error en configuración MQTT")