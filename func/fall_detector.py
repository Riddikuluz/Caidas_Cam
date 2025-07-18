import cv2
import mediapipe as mp
import time
import math
import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agregar el directorio padre al path para importaciones
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from func.send_alert import send_alert
except ImportError as e:
    logger.error(f"Error importando send_alert: {e}")
    sys.exit(1)

# Inicialización de MediaPipe
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    """Calcula el ángulo entre tres puntos"""
    a = [a.x, a.y]
    b = [b.x, b.y]
    c = [c.x, c.y]
    
    radians = math.atan2(c[1]-b[1], c[0]-b[0]) - math.atan2(a[1]-b[1], a[0]-b[0])
    angle = math.abs(radians*180.0/math.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle

def is_person_fallen(landmarks, image_width, image_height):
    """Algoritmo mejorado para detectar caídas"""
    try:
        # Verificar que todos los landmarks necesarios estén disponibles
        required_landmarks = [
            mp_pose.PoseLandmark.LEFT_SHOULDER.value,
            mp_pose.PoseLandmark.RIGHT_SHOULDER.value,
            mp_pose.PoseLandmark.LEFT_HIP.value,
            mp_pose.PoseLandmark.RIGHT_HIP.value,
            mp_pose.PoseLandmark.LEFT_ANKLE.value,
            mp_pose.PoseLandmark.RIGHT_ANKLE.value
        ]
        
        # Verificar visibilidad de landmarks críticos
        for landmark_idx in required_landmarks:
            if landmarks[landmark_idx].visibility < 0.5:
                return False, 0, 0
        
        # Obtener puntos clave del cuerpo
        left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
        left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value]
        
        # Calcular centro del torso
        torso_center_y = (left_shoulder.y + right_shoulder.y + left_hip.y + right_hip.y) / 4
        
        # Calcular altura promedio de los tobillos
        ankle_avg_y = (left_ankle.y + right_ankle.y) / 2
        
        # Diferencia de altura entre torso y pies (normalizada)
        height_diff = abs(torso_center_y - ankle_avg_y)
        
        # Ángulo del torso (inclinación)
        shoulder_center = [(left_shoulder.x + right_shoulder.x) / 2, 
                          (left_shoulder.y + right_shoulder.y) / 2]
        hip_center = [(left_hip.x + right_hip.x) / 2, 
                     (left_hip.y + right_hip.y) / 2]
        
        # Calcular ángulo de inclinación del torso
        torso_angle = math.atan2(abs(shoulder_center[0] - hip_center[0]), 
                                abs(shoulder_center[1] - hip_center[1])) * 180 / math.pi
        
        # Condiciones para detectar caída (ajustadas)
        is_horizontal = height_diff < 0.15  # Torso y pies a similar altura
        is_tilted = torso_angle > 60  # Torso muy inclinado
        
        return is_horizontal or is_tilted, height_diff, torso_angle
        
    except (IndexError, AttributeError, KeyError) as e:
        logger.error(f"Error en detección de caída: {e}")
        return False, 0, 0

def setup_camera():
    """Configura y valida la cámara"""
    try:
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        if not cap.isOpened():
            logger.error("No se pudo acceder a la cámara")
            return None
        
        # Configuración de resolución
        width, height = 1280, 720
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        
        # Verificar resolución real
        actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        if actual_width != width or actual_height != height:
            logger.warning(f"Resolución {width}x{height} no soportada. "
                          f"Usando: {int(actual_width)}x{int(actual_height)}")
        
        return cap
    except Exception as e:
        logger.error(f"Error configurando cámara: {e}")
        return None

def main():
    """Función principal del detector de caídas"""
    # Configuración de cámara
    cap = setup_camera()
    if cap is None:
        return 1
    
    # Configuración de ventana
    window_name = 'Fall Detection'
    try:
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)  # Usar WINDOW_NORMAL para mejor compatibilidad
        cv2.resizeWindow(window_name, 1280, 720)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    except Exception as e:
        logger.warning(f"Error configurando ventana: {e}")
    
    # Variables de estado
    counter = 0
    stage = None
    fall_start_time = None
    time_2_alert = 10
    no_detection_count = 0
    max_no_detection = 30
    
    logger.info("Detector de caídas iniciado. Presiona 'q' para salir")
    
    try:
        with mp_pose.Pose(min_detection_confidence=0.9, min_tracking_confidence=0.9) as pose:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    logger.error("No se pudo leer frame de la cámara")
                    break
    
                # Procesamiento de imagen
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = pose.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                image_height, image_width, _ = image.shape
    
                if results.pose_landmarks is None:
                    no_detection_count += 1
                    
                    # Reset después de pérdida prolongada
                    if no_detection_count > max_no_detection and stage in ["falling", "alert_sent"]:
                        logger.info("Detección perdida - Reseteando estado")
                        stage = None
                        fall_start_time = None
                        no_detection_count = 0
                    
                    # Mostrar información
                    cv2.putText(image, "No person detected", 
                                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
                    cv2.putText(image, f"Counter: {counter}", 
                                (10,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)
                    cv2.putText(image, f"Stage: {stage if stage else 'None'}", 
                                (10,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                    
                else:
                    # Reset contador de no detección
                    no_detection_count = 0
                    landmarks = results.pose_landmarks.landmark
                    
                    # Detectar caída
                    falling, height_diff, torso_angle = is_person_fallen(landmarks, image_width, image_height)
                    
                    # Lógica de estados
                    if falling:
                        if stage not in ["falling", "alert_sent"]:
                            stage = "falling"
                            fall_start_time = time.time()
                            logger.info(f"Caída detectada - Altura: {height_diff:.2f}, Ángulo: {torso_angle:.1f}°")
                        elif stage == "falling" and fall_start_time:
                            elapsed_time = time.time() - fall_start_time
                            if elapsed_time > time_2_alert:
                                try:
                                    success = send_alert()
                                    if success:
                                        counter += 1
                                        stage = "alert_sent"
                                        logger.info(f"ALERTA ENVIADA - Caída confirmada después de {elapsed_time:.1f}s")
                                    else:
                                        logger.error("Falló el envío de la alerta")
                                except Exception as e:
                                    logger.error(f"Error al enviar alerta: {e}")
                    else:
                        if stage in ["falling", "alert_sent"]:
                            stage = "standing"
                            logger.info("Persona se ha levantado")
                            fall_start_time = None
                    
                    # Mostrar información en pantalla
                    cv2.putText(image, f"Altura: {height_diff:.2f}", 
                                (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                    cv2.putText(image, f"Angulo: {torso_angle:.1f}°", 
                                (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                    cv2.putText(image, f"Counter: {counter}", 
                                (10,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,0,255), 2)
                    cv2.putText(image, f"Stage: {stage if stage else 'None'}", 
                                (10,90), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
                    
                    # Mostrar tiempo de caída
                    if stage == "falling" and fall_start_time:
                        elapsed = time.time() - fall_start_time
                        cv2.putText(image, f"Falling time: {elapsed:.1f}s", 
                                    (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
                    
                    # Dibujar landmarks
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                cv2.imshow(window_name, image)
                
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break
    
    except KeyboardInterrupt:
        logger.info("Interrupción recibida. Cerrando detector...")
    except Exception as e:
        logger.error(f"Error inesperado: {e}")
        return 1
    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Detector de caídas finalizado correctamente")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
