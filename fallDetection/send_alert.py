from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
ENDPOINT = os.getenv("ENDPOINT")
TOPIC = os.getenv("TOPIC")
CA_PATH = os.getenv("CA_PATH")
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")

def send_alert():
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
