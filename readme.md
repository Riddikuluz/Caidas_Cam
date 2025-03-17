# Sistema de Monitoreo con Cámara para Detección de Caídas

Este repositorio contiene la implementación modular y actualizada de un sistema de monitoreo basado en cámara, orientado a la detección de caídas y al envío de alertas en tiempo real. El sistema integra técnicas avanzadas de procesamiento de imágenes, análisis de poses y comunicación mediante MQTT a través de AWS IoT, permitiendo una respuesta inmediata ante eventos críticos.

## Ramas del Repositorio

- **x11**: Implementación optimizada para sistemas basados en Linux, que utiliza el método de captura _x11grab_.
- **win**: Versión funcional para sistemas operativos Windows.

## Características

- **Detección de Caídas**  
  Emplea algoritmos optimizados de procesamiento de imagen y reconocimiento de patrones (utilizando MediaPipe y OpenCV) para identificar incidentes de caída con alta precisión, minimizando los falsos positivos.

- **Gestión de Respuestas**  
  Permite la recepción y procesamiento de comandos de control a través del protocolo MQTT (mediante AWS IoT), facilitando el inicio o la detención de transmisiones de video y la activación de alertas según los eventos detectados.

- **Envío de Alertas**  
  Publica notificaciones a través de canales seguros para informar de manera inmediata a los responsables sobre eventos críticos, asegurando una rápida respuesta ante situaciones de emergencia.

- **Arquitectura Modular**  
  La estructura del sistema se divide en varios módulos (por ejemplo, `main.py`, `response_listener.py`, `send_alert.py` y `fall_detector.py`), lo que favorece la escalabilidad, el mantenimiento y la integración con otros sistemas.

## Estructura del Proyecto

```plaintext
.
├── main.py                   # Punto de entrada del sistema que orquesta la detección y el streaming.
├── func/
│   ├── response_listener.py  # Gestión de la recepción y el procesamiento de comandos vía MQTT.
│   ├── send_alert.py         # Envío de alertas mediante la publicación de mensajes MQTT.
│   └── fall_detector.py      # Lógica de detección de caídas utilizando OpenCV y MediaPipe.
├── .env                      # Archivo de configuración de variables de entorno (no incluido).
├── certs/                    # Directorio que contiene los certificados de AWS IoT.
├── requirements.txt          # Lista de dependencias del proyecto.
└── README.md                 # Documentación y guía de instalación.
```

## Instalación

### Requisitos Previos

- **Python 3.7** hasta **3.12**.
- **PIP** (gestor de paquetes de Python).
- Dependencias principales:
  - OpenCV (paquete `opencv-contrib-python`).
  - MediaPipe.
  - boto3.
  - AWSIoTPythonSDK.
  - python-dotenv.

### Clonación del Repositorio

Para clonar el repositorio en el equipo local, se debe ejecutar:

```bash
git clone https://github.com/Riddikuluz/Caidas_Cam.git
```

Luego, acceda al directorio del repositorio:

```bash
cd Caidas_Cam
```

### Instalación de Dependencias

Se recomienda el uso de un entorno virtual para gestionar las dependencias. Por ejemplo, utilizando `venv`:

```bash
python -m venv venv
source venv/bin/activate      # En Linux/Mac
venv\Scripts\activate         # En Windows
```

Instale las dependencias ejecutando:

```bash
pip install -r requirements.txt
```

En caso de no disponer del archivo `requirements.txt`, las dependencias se pueden instalar manualmente:

```bash
pip install opencv-contrib-python mediapipe python-dotenv AWSIoTPythonSDK boto3
```

### Configuración de Variables de Entorno

En la raíz del repositorio, se debe crear un archivo `.env` con la siguiente configuración:

```dotenv
# Configuración AWS IoT
CLIENT_ID=tu_client_id
ENDPOINT=tu_endpoint_de_aws_iot
TOPIC=tu_topico_mqtt
CA_PATH=ruta_al_certificado_ca
CERT_PATH=ruta_al_certificado
KEY_PATH=ruta_a_la_llave

# Configuración de Streaming (para main.py)
INGEST_URL_Monitor=tu_ingest_url_monitor
STREAM_KEY_Monitor=tu_stream_key_monitor

INGEST_URL_Alerta=tu_ingest_url_alerta
STREAM_KEY_Alerta=tu_stream_key_alerta
```

Se deberán reemplazar los valores por la información correspondiente a la configuración específica.

## Ejecución

### Iniciar el Sistema de Monitoreo

Para ejecutar el sistema, que abarca la detección de caídas y la gestión del streaming, se debe ejecutar:

```bash
python main.py
```

Este comando inicia el proceso central encargado de orquestar la detección de caídas, la transmisión en vivo y la comunicación mediante MQTT.
