import cv2
import requests
import numpy as np
import statistics as st
from datetime import datetime
import time

# Configuración del stream y del modelo
stream_url = "http://192.168.0.0/1600x1200.mjpeg"
model_path = "models/mobilenet_iter_73000.caffemodel"
config_path = "models/deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(config_path, model_path)

confidence_threshold = 0.1
person_class_id = 15  # ID de clase para personas en MobileNet
frame_check_interval = 1  # Detectar cada N fotogramas

# Inicializa el stream y la ventana de OpenCV
stream = requests.get(stream_url, stream=True)
cv2.namedWindow("Camera Stream", cv2.WINDOW_NORMAL)

class FallDetector:
    def __init__(self, scale=0.5):
        self.scale = scale
        self.backSub = cv2.createBackgroundSubtractorMOG2()
        
        # Parámetros de detección y estado
        self.width = []
        self.height = []
        self.xcenter = []
        self.ycenter = []
        self.toBeChecked = False
        self.stationary = False
        self.isFall = False
        self.alertMsgFlag = False
        self.fall_start_time = None
        self.vertical_to_horizontal_transition = False

    def rescaleFrame(self, frame):
        """Escala el fotograma para aumentar la velocidad de procesamiento."""
        width = int(frame.shape[1] * self.scale)
        height = int(frame.shape[0] * self.scale)
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    def analyzePosition(self, box):
        """Analiza la posición de la persona detectada para verificar postura."""
        startX, startY, endX, endY = box
        w, h = endX - startX, endY - startY
        xc, yc = startX + w // 2, startY + h // 2
        self.width.append(w)
        self.height.append(h)
        self.xcenter.append(int(xc))  # Convertir a int nativo
        self.ycenter.append(int(yc))  # Convertir a int nativo
        
        if len(self.width) > 10:
            self.width.pop(0)
            self.height.pop(0)
            self.xcenter.pop(0)
            self.ycenter.pop(0)
        
        # Detectar transición de vertical a horizontal
        avg_width = st.mean(self.width)
        avg_height = st.mean(self.height)
        if avg_width > avg_height and not self.vertical_to_horizontal_transition:
            self.vertical_to_horizontal_transition = True  # Activa la bandera solo una vez durante la transición
            self.fall_start_time = time.time()  # Registra el inicio de la posible caída

        elif avg_width <= avg_height:
            self.vertical_to_horizontal_transition = False  # Resetear si la persona vuelve a posición vertical
            self.isFall = False

    def checkStationary(self):
        """Verifica si la persona permanece inmóvil en la postura horizontal."""
        stddev_x = st.pstdev(map(int, self.xcenter))  # Conversión a tipos nativos
        stddev_y = st.pstdev(map(int, self.ycenter))  # Conversión a tipos nativos
        self.stationary = stddev_x < 2 and stddev_y < 2

    def checkFall(self):
        """Determina si se ha confirmado una caída con un tiempo de espera."""
        if self.toBeChecked and self.stationary and self.vertical_to_horizontal_transition:
            if time.time() - self.fall_start_time <= 1:  # Detecta solo si la transición fue rápida
                self.isFall = True
        else:
            self.isFall = False
            self.fall_start_time = None  # Reinicia el temporizador

    def sendAlert(self, frame):
        """Envía una alerta y guarda una captura si se confirma la caída."""
        if self.isFall and not self.alertMsgFlag:
            print("¡Caída detectada!")
            dt = datetime.now().strftime("%d%m%Y%H%M%S")
            filename = f'Fallshot_{dt}.png'
            cv2.imwrite(filename, frame)
            print(f'Imagen guardada: {filename}')
            self.alertMsgFlag = True

    def drawRectangle(self, frame, box):
        """Dibuja un rectángulo alrededor de la persona, rojo si hay caída."""
        startX, startY, endX, endY = box
        color = (0, 0, 255) if self.isFall else (0, 255, 0)
        status_text = "FALL" if self.isFall else "Normal"
        cv2.rectangle(frame, (startX, startY), (endX, endY), color, 2)
        cv2.putText(frame, status_text, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def processFrame(self, frame, frame_count):
        """Realiza detección de personas y análisis de caídas en cada fotograma."""
        if frame_count % frame_check_interval == 0:
            blob = cv2.dnn.blobFromImage(frame, 0.007843, (300, 300), 127.5)
            net.setInput(blob)
            detections = net.forward()
        
            # Iterar sobre las detecciones para analizar personas
            for i in range(detections.shape[2]):
                confidence = detections[0, 0, i, 2]
                if confidence > confidence_threshold:
                    class_id = int(detections[0, 0, i, 1])
                    if class_id == person_class_id:
                        box = (detections[0, 0, i, 3:7] * 
                               np.array([frame.shape[1], frame.shape[0], frame.shape[1], frame.shape[0]])).astype("int")
                        self.analyzePosition(box)
                        self.checkStationary()
                        self.checkFall()
                        self.drawRectangle(frame, box)
                        self.sendAlert(frame)

# Inicializar el detector de caídas
fall_detector = FallDetector()

# Procesar el stream de video
buffer = b''
frame_count = 0
for chunk in stream.iter_content(chunk_size=1024):
    buffer += chunk

    start = buffer.find(b'\xff\xd8')
    end = buffer.find(b'\xff\xd9')

    if start != -1 and end != -1:
        jpg = buffer[start:end + 2]
        buffer = buffer[end + 2:]

        img_np = np.frombuffer(jpg, dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        # Procesar y mostrar el fotograma
        fall_detector.processFrame(img, frame_count)
        cv2.imshow("Camera Stream", img)

        frame_count += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
