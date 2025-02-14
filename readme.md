# Sistema de Monitoreo con Cámara para Detección de Caídas

Este repositorio contiene una implementación modular y actualizada de un sistema de monitoreo mediante cámara, orientado a la detección de caídas y al envío de alertas en tiempo real. El sistema integra técnicas avanzadas de procesamiento de imagen, análisis de pose y comunicación mediante MQTT (a través de AWS IoT), permitiendo una respuesta inmediata ante eventos críticos.

## Ramas del Repositorio

- **x11**: Implementación optimizada para sistemas basados en Linux, especialmente en Raspberry Pi, que utiliza el método de captura _x11grab_.
- **win**: Versión funcional para sistemas operativos Windows. Esta rama se menciona únicamente para referencia, ya que la solución desplegada se basa en la rama **x11**.

## Características

- **Detección de Caídas:**  
  Utiliza algoritmos optimizados de procesamiento de imagen y reconocimiento de patrones (con Mediapipe y OpenCV) para identificar incidentes de caída con alta precisión y reducir falsos positivos.

- **Gestión de Respuestas:**  
  Recibe y procesa comandos de control a través del protocolo MQTT (mediante AWS IoT), permitiendo iniciar o detener transmisiones de video y activar alertas en función de los eventos detectados.

- **Envío de Alertas:**  
  Publica notificaciones a través de canales seguros para informar a los responsables de la detección de caídas, asegurando una rápida respuesta ante situaciones críticas.

- **Arquitectura Modular:**  
  El sistema está dividido en varios módulos (main.py, response_listener.py, send_alert.py y fall_detector.py), facilitando la escalabilidad, el mantenimiento y la integración con otros sistemas.

## Estructura del Proyecto

```plaintext
.
├── main.py              # Punto de entrada del sistema, orquesta detección y streaming
├── response_listener.py # Gestión de recepción y procesamiento de comandos vía MQTT
├── send_alert.py        # Envío de alertas mediante publicación de mensajes MQTT
├── fall_detector.py     # Lógica de detección de caídas utilizando OpenCV y Mediapipe
├── .env                 # Archivo de configuración de variables de entorno (no incluido)
├── requirements.txt     # Lista de dependencias del proyecto
└── README.md            # Documentación y guía de instalación
```

## Instalación

### Requisitos Previos

- **Python 3.7** o superior
- **PIP** (gestor de paquetes de Python)
- Dependencias principales:
  - OpenCV (`opencv-contrib-python`)
  - Mediapipe
  - boto3
  - AWSIoTPythonSDK
  - python-dotenv

### Clonar el Repositorio

Clonar el repositorio en el equipo local:

```bash
git clone https://github.com/Riddikuluz/Caidas_Cam.git
```

Acceder a la carpeta del repositorio:

```bash
cd Caidas_Cam
```

### Instalación de Dependencias

Se recomienda utilizar un entorno virtual para gestionar las dependencias. Por ejemplo, utilizando `venv`:

```bash
python -m venv venv
source venv/bin/activate      # En Linux/Mac
venv\Scripts\activate         # En Windows
```

Instalar las dependencias:

```bash
pip install -r requirements.txt
```

Si no se dispone de un archivo `requirements.txt`, instale manualmente:

```bash
pip install opencv-contrib-python mediapipe python-dotenv AWSIoTPythonSDK boto3
```

### Configuración de Variables de Entorno

Crear un archivo `.env` en la raíz del repositorio y definir las siguientes variables:

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

INGEST_URL_Ambiental=tu_ingest_url_ambiental
STREAM_KEY_Ambiental=tu_stream_key_ambiental
```

Reemplace los valores con la información correspondiente a su configuración.

## Ejecución

### Iniciar el Sistema de Monitoreo

Para ejecutar el sistema (detección de caídas y gestión de streaming), ejecute:

```bash
python main.py
```

Este comando inicia el proceso central que orquesta la detección de caídas, la gestión del streaming y la comunicación a través de MQTT.

### Prueba de Detección de Caídas

El módulo `fall_detector.py` se encarga de capturar y procesar el video en tiempo real, analizando la pose corporal para detectar caídas. Durante la ejecución, la interfaz gráfica mostrará el video junto con indicadores (por ejemplo, el contador de caídas y el estado actual: "falling" o "standing"). Para detener la ejecución, presione la tecla `q`.
