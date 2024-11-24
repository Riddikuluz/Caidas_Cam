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
class ResponseListener:
    def __init__(self, stop_event):
        self.response_received = False
        self.stop_event = stop_event  # Evento para detener el streaming
        self.client = self._initialize_client()
        self.client.subscribe(TOPIC, 1, self.message_callback)

    def _initialize_client(self):
        client = AWSIoTMQTTClient(CLIENT_ID)
        client.configureEndpoint(ENDPOINT, 8883)
        client.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
        client.configureOfflinePublishQueueing(-1)
        client.configureDrainingFrequency(2)
        client.configureConnectDisconnectTimeout(10)
        client.configureMQTTOperationTimeout(5)
        client.connect()
        return client

    def message_callback(self, client, userdata, message):
        """Procesa los mensajes MQTT."""
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            action = payload.get("action")

            if action == "start_stream":
                print("✅ Solicitud de inicio de streaming recibida.")
                self.response_received = True
                self.stop_event.clear()

            elif action == "stop_stream":
                print("🛑 Solicitud de detención de streaming recibida.")
                self.stop_event.set()

            elif payload.get("message"):
                print(f"📥 Mensaje recibido: {payload['message']}")
        except json.JSONDecodeError:
            print("⚠️ Error al procesar el mensaje.")

    def disconnect(self):
        """Desconecta el cliente MQTT."""
        self.client.disconnect()
        print("✅ Cliente MQTT desconectado.")