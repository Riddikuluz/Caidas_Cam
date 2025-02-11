# response_listener.py
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
    def __init__(self):
        self.response_received = False
        self.action = None  # "start" o "stop"
        self.stream_type = None
        self.client = self._initialize_client()

    def _initialize_client(self):
        client = AWSIoTMQTTClient(CLIENT_ID)
        client.configureEndpoint(ENDPOINT, 8883)
        client.configureCredentials(CA_PATH, KEY_PATH, CERT_PATH)
        client.configureOfflinePublishQueueing(-1)
        client.configureDrainingFrequency(2)
        client.configureConnectDisconnectTimeout(10)
        client.configureMQTTOperationTimeout(5)
        try:
            client.connect()
            print("Cliente MQTT conectado.")
            client.subscribe(TOPIC, 1, self.message_callback)
        except Exception as e:
            print(f"Error al conectar el cliente MQTT: {e}")
        return client

    def message_callback(self, client, userdata, message):
        try:
            payload = json.loads(message.payload.decode("utf-8"))
            action = payload.get("action")
            print(f"Mensaje recibido: {payload}")
            if action == "start_stream_monitor":
                print("Solicitud de inicio de streaming (Monitor) recibida.")
                self.response_received = True
                self.action = "start"
                self.stream_type = "monitor"
            elif action == "start_stream_alerta":
                print("Solicitud de inicio de streaming (Alerta) recibida.")
                self.response_received = True
                self.action = "start"
                self.stream_type = "alerta"
            elif action == "start_stream_ambiental":
                print("Solicitud de inicio de streaming (Ambiental) recibida.")
                self.response_received = True
                self.action = "start"
                self.stream_type = "ambiental"
            elif action == "stop_stream_monitor":
                print("Solicitud de detención de streaming (Monitor) recibida.")
                self.response_received = True
                self.action = "stop"
                self.stream_type = "monitor"
            elif action == "stop_stream_alerta":
                print("Solicitud de detención de streaming (Alerta) recibida.")
                self.response_received = True
                self.action = "stop"
                self.stream_type = "alerta"
            elif action == "stop_stream_ambiental":
                print("Solicitud de detención de streaming (Ambiental) recibida.")
                self.response_received = True
                self.action = "stop"
                self.stream_type = "ambiental"
            else:
                print("Acción desconocida.")
        except json.JSONDecodeError:
            print("JSON inválido.")
        except Exception as e:
            print(f"Error en el callback del mensaje: {e}")

    def disconnect(self):
        try:
            self.client.disconnect()
            print("Cliente MQTT desconectado.")
        except Exception as e:
            print(f"Error al desconectar el cliente MQTT: {e}")
