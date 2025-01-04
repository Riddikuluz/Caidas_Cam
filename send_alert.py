from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import os
from dotenv import load_dotenv
import json

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
ENDPOINT = os.getenv("ENDPOINT")
TOPIC = os.getenv("TOPIC")
CA_PATH = os.getenv("CA_PATH")
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")
STATE_FILE = "streaming_state.json"

def get_streaming_state():
    try:
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
            return state.get("is_streaming", False)
    except FileNotFoundError:
        return False

def publish_mqtt():
    client = AWSIoTMQTTClient(CLIENT_ID)
    client.configureEndpoint(ENDPOINT, 8883)
    client.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
    client.connect()

    message = {
        "id_dispositivo": "cámara",
        "tipificacion": "caída",
        "mensaje": "¡Caída detectada!"
    }
    
    client.publish(TOPIC, json.dumps(message), 1)
    client.disconnect()
    print("Alerta enviada con éxito.")

def send_alert():
    is_streaming = get_streaming_state()
    print("is_streaming:", is_streaming)

    if is_streaming:
        print("No se puede enviar una alerta si se está transmitiendo.")
    else:
        print("Enviando alerta...")
        #publish_mqtt()