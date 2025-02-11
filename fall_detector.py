import cv2
import mediapipe as mp
import numpy as np
import platform
import time
from send_alert import send_alert

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
mp_drawing.DrawingSpec

def calculate_angle(a,b,c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return int(angle) 


if platform.system() != "Linux":
    cap = cv2.VideoCapture(0)
else:
    cap = cv2.VideoCapture(2, cv2.CAP_V4L2)

if not cap.isOpened():
    print("Error: No se pudo acceder a la cámara.")
    exit()

width = 1280
height = 720
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
if actual_width != width or actual_height != height:
    print(f"Advertencia: La cámara no soporta la resolución {width}x{height}. "
          f"Resolución actual: {int(actual_width)}x{int(actual_height)}.")

cv2.namedWindow('Fall Detection', cv2.WND_PROP_FULLSCREEN)
cv2.setWindowProperty('Fall Detection', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

counter = 0
fall = False 
stage = None
fall_start_time = None
time_2_alert = 10

with mp_pose.Pose(min_detection_confidence=0.9, min_tracking_confidence=0.9) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
      
        results = pose.process(image)
    
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image_hight, image_width, _ = image.shape

        try:
            landmarks = results.pose_landmarks.landmark
            
            dot_NOSE_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].x * image_width)
            dot_NOSE_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.NOSE].y * image_hight)
                               
            dot_LEFT_SHOULDER_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].x * image_width)
            dot_LEFT_SHOULDER_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_hight)
            
            dot_RIGHT_SHOULDER_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].x * image_width)
            dot_RIGHT_SHOULDER_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_hight)
            
            dot_LEFT_ELBOW_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW].x * image_width)
            dot_LEFT_ELBOW_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW].y * image_hight)
                        
            dot_RIGHT_ELBOW_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW].x * image_width)
            dot_RIGHT_ELBOW_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ELBOW].y * image_hight)
            
            dot_LEFT_WRIST_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].x * image_width)
            dot_LEFT_WRIST_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST].y * image_hight)
            
            dot_RIGHT_WRIST_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].x * image_width)
            dot_RIGHT_WRIST_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_WRIST].y * image_hight)
            
            dot_LEFT_HIP_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP].x * image_width)
            dot_LEFT_HIP_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP].y * image_hight)
            
            dot_RIGHT_HIP_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP].x * image_width)
            dot_RIGHT_HIP_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HIP].y * image_hight)
            
            dot_LEFT_KNEE_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE].x * image_width)
            dot_LEFT_KNEE_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE].y * image_hight)
                        
            dot_RIGHT_KNEE_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE].x * image_width)
            dot_RIGHT_KNEE_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_KNEE].y * image_hight)

            dot_LEFT_ANKLE_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE].x * image_width)
            dot_LEFT_ANKLE_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE].y * image_hight)
                        
            dot_RIGHT_ANKLE_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE].x * image_width)
            dot_RIGHT_ANKLE_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_ANKLE].y * image_hight)
            
            dot_LEFT_HEEL_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HEEL].x * image_width)
            dot_LEFT_HEEL_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_HEEL].y * image_hight)
           
            dot_RIGHT_HEEL_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HEEL].x * image_width)
            dot_RIGHT_HEEL_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_HEEL].y * image_hight)
            
            dot_LEFT_FOOT_INDEX_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_FOOT_INDEX].x * image_width)
            dot_LEFT_FOOT_INDEX_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.LEFT_FOOT_INDEX].y * image_hight)
           
            dot_RIGHT_FOOT_INDEX_X= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX].x * image_width)
            dot_RIGHT_FOOT_INDEX_Y= int(results.pose_landmarks.landmark[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX].y * image_hight)
        
            dot_NOSE = [ dot_NOSE_X,dot_NOSE_Y]
            
            dot_LEFT_ARM_A_X = int((dot_LEFT_WRIST_X+dot_LEFT_ELBOW_X)/2)
            dot_LEFT_ARM_A_Y = int((dot_LEFT_WRIST_Y+dot_LEFT_ELBOW_Y)/2)
            LEFT_ARM_WRIST_ELBOW = [dot_LEFT_ARM_A_X,dot_LEFT_ARM_A_Y]
            
            dot_RIGHT_ARM_A_X = int((dot_RIGHT_WRIST_X+dot_RIGHT_ELBOW_X)/2)
            dot_RIGHT_ARM_A_Y = int((dot_RIGHT_WRIST_Y+dot_RIGHT_ELBOW_Y)/2)
            RIGHT_ARM_WRIST_ELBOW = [dot_LEFT_ARM_A_X, dot_LEFT_ARM_A_Y]
            
            dot_LEFT_ARM_SHOULDER_ELBOW_X = int((dot_LEFT_SHOULDER_X+dot_LEFT_ELBOW_X)/2)
            dot_LEFT_ARM_SHOULDER_ELBOW_Y = int((dot_LEFT_SHOULDER_Y+dot_LEFT_ELBOW_Y)/2)
            LEFT_ARM_SHOULDER_ELBOW = [dot_LEFT_ARM_SHOULDER_ELBOW_X, dot_LEFT_ARM_SHOULDER_ELBOW_Y]
            
            dot_RIGHT_ARM_SHOULDER_ELBOW_X = int((dot_RIGHT_SHOULDER_X+dot_RIGHT_ELBOW_X)/2)
            dot_RIGHT_ARM_SHOULDER_ELBOW_Y = int((dot_RIGHT_SHOULDER_Y+dot_RIGHT_ELBOW_Y)/2)
            RIGHT_ARM_SHOULDER_ELBOW = [dot_RIGHT_ARM_SHOULDER_ELBOW_X, dot_RIGHT_ARM_SHOULDER_ELBOW_Y]
            
            dot_BODY_SHOULDER_HIP_X = int((dot_RIGHT_SHOULDER_X+dot_RIGHT_HIP_X+dot_LEFT_SHOULDER_X+dot_LEFT_HIP_X)/4)
            dot_BODY_SHOULDER_HIP_Y = int((dot_RIGHT_SHOULDER_Y+dot_RIGHT_HIP_Y+dot_LEFT_SHOULDER_Y+dot_LEFT_HIP_Y)/4)
            BODY_SHOULDER_HIP = [dot_BODY_SHOULDER_HIP_X, dot_BODY_SHOULDER_HIP_Y]
            
            dot_LEFT_LEG_HIP_KNEE_X = int((dot_LEFT_HIP_X+dot_LEFT_KNEE_X)/2)
            dot_LEFT_LEG_HIP_KNEE_Y = int((dot_LEFT_HIP_Y+dot_LEFT_KNEE_Y)/2)
            LEFT_LEG_HIP_KNEE = [dot_LEFT_LEG_HIP_KNEE_X, dot_LEFT_LEG_HIP_KNEE_Y]
            
            dot_RIGHT_LEG_HIP_KNEE_X = int((dot_RIGHT_HIP_X+dot_RIGHT_KNEE_X)/2)
            dot_RIGHT_LEG_HIP_KNEE_Y = int((dot_RIGHT_HIP_Y+dot_RIGHT_KNEE_Y)/2)
            RIGHT_LEG_HIP_KNEE = [dot_RIGHT_LEG_HIP_KNEE_X, dot_RIGHT_LEG_HIP_KNEE_Y]
            
            dot_LEFT_LEG_KNEE_ANKLE_X = int((dot_LEFT_ANKLE_X+dot_LEFT_KNEE_X)/2)
            dot_LEFT_LEG_KNEE_ANKLE_Y = int((dot_LEFT_ANKLE_Y+dot_LEFT_KNEE_Y)/2)
            LEFT_LEG_KNEE_ANKLE = [dot_LEFT_LEG_KNEE_ANKLE_X, dot_LEFT_LEG_KNEE_ANKLE_Y]

            dot_RIGHT_LEG_KNEE_ANKLE_X = int((dot_RIGHT_ANKLE_X+dot_RIGHT_KNEE_X)/2)
            dot_RIGHT_LEG_KNEE_ANKLE_Y = int((dot_RIGHT_ANKLE_Y+dot_RIGHT_KNEE_Y)/2)
            RIGHT_LEG_KNEE_ANKLE = [dot_RIGHT_LEG_KNEE_ANKLE_X, dot_RIGHT_LEG_KNEE_ANKLE_Y]
            
            dot_LEFT_FOOT_INDEX_HEEL_X = int((dot_LEFT_FOOT_INDEX_X+dot_LEFT_HEEL_X)/2)
            dot_LEFT_FOOT_INDEX_HEEL_Y = int((dot_LEFT_FOOT_INDEX_Y+dot_LEFT_HEEL_Y)/2)
            LEFT_FOOT_INDEX_HEEL = [dot_LEFT_FOOT_INDEX_HEEL_X,dot_LEFT_FOOT_INDEX_HEEL_Y]
            
            dot_RIGHT_FOOT_INDEX_HEEL_X = int((dot_RIGHT_FOOT_INDEX_X+dot_RIGHT_HEEL_X)/2)
            dot_RIGHT_FOOT_INDEX_HEEL_Y = int((dot_RIGHT_FOOT_INDEX_Y+dot_RIGHT_HEEL_Y)/2)
            RIGHT_FOOT_INDEX_HEEL = [dot_RIGHT_FOOT_INDEX_HEEL_X, dot_RIGHT_FOOT_INDEX_HEEL_Y]
            
            dot_UPPER_BODY_X = int((dot_NOSE_X+dot_LEFT_ARM_A_X+dot_RIGHT_ARM_A_X+dot_LEFT_ARM_SHOULDER_ELBOW_X+dot_RIGHT_ARM_SHOULDER_ELBOW_X+dot_BODY_SHOULDER_HIP_X)/6)
            dot_UPPER_BODY_Y = int((dot_NOSE_Y+dot_LEFT_ARM_A_Y+dot_RIGHT_ARM_A_Y+dot_LEFT_ARM_SHOULDER_ELBOW_Y+dot_RIGHT_ARM_SHOULDER_ELBOW_Y+dot_BODY_SHOULDER_HIP_Y)/6)
            UPPER_BODY = [dot_UPPER_BODY_X, dot_UPPER_BODY_Y]
            
            dot_LOWER_BODY_X = int((dot_LEFT_LEG_HIP_KNEE_X+dot_RIGHT_LEG_HIP_KNEE_X+dot_LEFT_LEG_KNEE_ANKLE_X+ dot_RIGHT_LEG_KNEE_ANKLE_X+dot_LEFT_FOOT_INDEX_HEEL_X+dot_RIGHT_FOOT_INDEX_HEEL_X)/6)
            dot_LOWER_BODY_Y = int((dot_LEFT_LEG_HIP_KNEE_Y+dot_RIGHT_LEG_HIP_KNEE_Y+dot_LEFT_LEG_KNEE_ANKLE_Y+ dot_RIGHT_LEG_KNEE_ANKLE_Y+dot_LEFT_FOOT_INDEX_HEEL_Y+dot_RIGHT_FOOT_INDEX_HEEL_Y)/6)
            LOWER_BODY = [dot_LOWER_BODY_X, dot_LOWER_BODY_Y]
            
            dot_BODY_X = int( (dot_UPPER_BODY_X + dot_LOWER_BODY_X)/2)
            dot_BODY_Y = int( (dot_UPPER_BODY_Y + dot_LOWER_BODY_Y)/2)
            BODY = [dot_BODY_X, dot_BODY_Y]
            
            shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow_l = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist_l = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            elbow_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            wrist_r = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            
            elbow_l = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            
            elbow_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y]
            shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            
            shoulder_l = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee_l = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            
            shoulder_r = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y]
            hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            knee_r = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            
            hip_l = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee_l = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle_l = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            
            hip_r = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            knee_r = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            ankle_r = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
            
            angle_elbow_l = calculate_angle(shoulder_l, elbow_l, wrist_l)
            
            angle_elbow_r = calculate_angle(shoulder_r, elbow_r, wrist_r)
            
            angle_shoulder_l = calculate_angle(elbow_l, shoulder_l, hip_l)
            
            angle_shoulder_r = calculate_angle(elbow_r, shoulder_r, hip_r)
            
            angle_hip_l = calculate_angle(shoulder_l, hip_l, knee_l)
            
            angle_hip_r = calculate_angle(shoulder_r, hip_r, knee_r)
            
            angle_knee_l = calculate_angle(hip_l, knee_l, ankle_l)
            
            angle_knee_r = calculate_angle(hip_r, knee_r, ankle_r)
            
            Point_of_action_LEFT_X = int( 
                ((dot_LEFT_FOOT_INDEX_X + dot_LEFT_HEEL_X)/2))
            
            Point_of_action_LEFT_Y = int( 
                ((dot_LEFT_FOOT_INDEX_Y + dot_LEFT_HEEL_Y)/2))
               
            Point_of_action_RIGHT_X = int( 
                ((dot_RIGHT_FOOT_INDEX_X + dot_RIGHT_HEEL_X)/2))
            
            Point_of_action_RIGHT_Y = int( 
                ((dot_RIGHT_FOOT_INDEX_Y + dot_RIGHT_HEEL_Y)/2))           
            
            Point_of_action_X = int ((Point_of_action_LEFT_X +  Point_of_action_RIGHT_X)/2)
            Point_of_action_Y = int ((Point_of_action_LEFT_Y +  Point_of_action_RIGHT_Y)/2)
            
            Point_of_action = [Point_of_action_X, Point_of_action_Y]

            fall = Point_of_action_X - dot_BODY_X

            if Point_of_action_X is None or dot_BODY_X is None:
                print("Error: Valores indefinidos para Point_of_action_X o dot_BODY_X")
                  
            falling = abs(fall) > 50
            standing = abs(fall) <= 50
            x = Point_of_action_X
            y = -(1.251396648*x) + 618

            if falling:
                if stage != "falling":
                    stage = "falling"
                    fall_start_time = time.time()
                    print(f"Inicio de caída detectado en x={x}, y={y}")
                else:
                    try:
                        elapsed_time = (time.time() - fall_start_time 
                                        if fall_start_time else 0)
                    except Exception as e:
                        print(f"Error al calcular tiempo: {e}")
                        elapsed_time = 0

                    if elapsed_time > time_2_alert:
                        send_alert()
                        print(f"Alerta enviada después de {elapsed_time:.2f}s")
                        counter +=1
                        fall_start_time = None
            else:
                if stage == "falling":
                    stage = "standing"
                    print(f"Se ha levantado en x={x}, y={y}")
                    cv2.putText(image, 'standing', (320, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2, cv2.LINE_AA)
                    fall_start_time = None
        except:
              pass
        cv2.putText(image, str(counter), 
                    (10,60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,255), 2, cv2.LINE_AA)
        cv2.putText(image, stage, 
            (60,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
        
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
            mp_drawing.DrawingSpec(color=(255,255,255), thickness=2, circle_radius=2), 
            mp_drawing.DrawingSpec(color=(0,0,0), thickness=2,circle_radius=2))               
        
        cv2.imshow('Fall Detection', image)
       
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()