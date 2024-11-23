import time
import json
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
ENDPOINT = os.getenv("ENDPOINT")
TOPIC = os.getenv("TOPIC")
CA_PATH = os.getenv("CA_PATH")
CERT_PATH = os.getenv("CERT_PATH")
KEY_PATH = os.getenv("KEY_PATH")


response_received = False

def message_callback(client, userdata, message):
    global response_received
    try:
        payload = json.loads(message.payload.decode("utf-8"))
        if payload.get("action") == "start_stream":
            response_received = True
        elif payload.get("message"):
            print(f"Mensaje recibido: {payload['message']}")
            response_received = False

    except json.JSONDecodeError:
        print("⚠️ Error al procesar el mensaje.")


def wait_for_response(timeout=60):
    global response_received
    client = AWSIoTMQTTClient(CLIENT_ID)
    client.configureEndpoint(ENDPOINT, 8883)
    client.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
    client.connect()
    client.subscribe(TOPIC, 1, message_callback)

    start_time = time.time()
    while time.time() - start_time < timeout:
        if response_received:
            client.disconnect()
            return True
        time.sleep(1)

    client.disconnect()
    return False
