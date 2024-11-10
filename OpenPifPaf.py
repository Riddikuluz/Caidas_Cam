import cv2
import requests
import numpy as np
import time
import statistics as st
from datetime import datetime
from openpifpaf import Predictor  # Asegúrate de que openpifpaf esté instalado y configurado

# Configura el stream de video
stream_url = "http://192.168.0.0/1600x1200.mjpeg"
stream = requests.get(stream_url, stream=True)
cv2.namedWindow("Camera Stream", cv2.WINDOW_NORMAL)

class FallDetector:
    def __init__(self, scale=0.5):
        self.scale = scale
        self.backSub = cv2.createBackgroundSubtractorMOG2()
        
        # Historial de movimiento
        self.largestContour = []    
        self.width = []
        self.height = []
        self.xcenter = []
        self.ycenter = []
        
        # Flags y estado
        self.toBeChecked = False
        self.isFall = False
        self.stationary = False
        self.alertMsgFlag = False
        self.OutofFrame = False
        
        # Configura el modelo de puntos clave
        self.predictor = Predictor(checkpoint="shufflenetv2k16")  # Modelo ligero

    def rescaleFrame(self, frame):
        """Escala el fotograma para aumentar la velocidad de procesamiento."""
        width = int(frame.shape[1] * self.scale)
        height = int(frame.shape[0] * self.scale)
        return cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    def analyzePosition(self):
        """Analiza la posición del objeto en movimiento para detectar posible caída."""
        x, y, w, h = cv2.boundingRect(self.largestContour)
        self.width.append(w)
        self.height.append(h)
        self.xcenter.append(x + w // 2)
        self.ycenter.append(y + h // 2)
        
        if len(self.width) > 10:
            self.width.pop(0)
            self.height.pop(0)
            self.xcenter.pop(0)
            self.ycenter.pop(0)
        
        # Posición horizontal persistente activa la comprobación
        if st.mean(self.width) > st.mean(self.height):
            self.toBeChecked = True

    def checkStationary(self):
        """Verifica si el objeto está estacionario."""
        stddev_x = st.pstdev(self.xcenter)
        stddev_y = st.pstdev(self.ycenter)
        self.stationary = stddev_x < 2 and stddev_y < 2

    def checkAction(self, frame):
        """Comprueba la acción actual y determina si se confirma la caída."""
        if self.toBeChecked and self.stationary:
            # Activación del modelo de puntos clave para confirmar caída
            self.confirmFallWithKeypoints(frame)
        elif not self.stationary:
            self.isFall = False
            self.toBeChecked = False

    def confirmFallWithKeypoints(self, frame):
        """Usa puntos clave para confirmar la caída."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        keypoints = self.predictor.numpy_image(frame_rgb)[0].data[:, :2]
        
        # Comprobar si hombros y caderas están alineados horizontalmente
        if len(keypoints) > 12:  # Asegurarse de que hay puntos clave suficientes
            shoulder_diff = abs(keypoints[5][1] - keypoints[6][1])
            hip_diff = abs(keypoints[11][1] - keypoints[12][1])
            if shoulder_diff < 10 and hip_diff < 10:
                self.isFall = True
                self.sendAlert(frame)

    def sendAlert(self, frame):
        """Envía una alerta y guarda una imagen si se detecta una caída."""
        if not self.alertMsgFlag:
            print("¡Caída detectada!")
            dt = datetime.now().strftime("%d%m%Y%H%M%S")
            filename = f'Fallshot_{dt}.png'
            cv2.imwrite(filename, frame)
            print(f'Imagen guardada: {filename}')
            self.alertMsgFlag = True

    def processStream(self):
        """Procesa cada fotograma del stream y aplica las etapas de detección."""
        byte_stream = bytes()
        for chunk in stream.iter_content(chunk_size=1024):
            byte_stream += chunk
            a = byte_stream.find(b'\xff\xd8')
            b = byte_stream.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = byte_stream[a:b+2]
                byte_stream = byte_stream[b+2:]
                frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                
                # Escalar y procesar fotograma
                frame = self.rescaleFrame(frame)
                fgmask = self.backSub.apply(frame)
                contours, _ = cv2.findContours(fgmask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
                
                # Encuentra el contorno más grande
                if contours:
                    self.largestContour = max(contours, key=cv2.contourArea)
                    if cv2.contourArea(self.largestContour) > 600:
                        self.analyzePosition()
                        self.checkStationary()
                        self.checkAction(frame)
                
                # Visualización
                cv2.imshow("Camera Stream", frame)
                if cv2.waitKey(1) == 27:  # Presiona ESC para salir
                    break

        cv2.destroyAllWindows()

# Ejecuta el detector de caídas
fd = FallDetector()
fd.processStream()
