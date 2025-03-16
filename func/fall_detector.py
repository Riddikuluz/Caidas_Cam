import cv2
import mediapipe as mp
import time
from send_alert import send_alert

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
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
stage = None
fall_start_time = None
time_2_alert = 10

with mp_pose.Pose(min_detection_confidence=0.9, min_tracking_confidence=0.9) as pose:
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = pose.process(image)
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image_height, image_width, _ = image.shape

        if results.pose_landmarks is None:
            cv2.imshow('Fall Detection', image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
            continue

        landmarks = results.pose_landmarks.landmark

        left_shoulder_x = int(landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * image_width)
        right_shoulder_x = int(landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x * image_width)
        left_hip_x = int(landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x * image_width)
        right_hip_x = int(landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x * image_width)
        body_center_x = int((left_shoulder_x + right_shoulder_x + left_hip_x + right_hip_x) / 4)

        left_foot_x = int(landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x * image_width)
        right_foot_x = int(landmarks[mp_pose.PoseLandmark.RIGHT_FOOT_INDEX.value].x * image_width)
        point_of_action_x = int((left_foot_x + right_foot_x) / 2)

        fall_diff = point_of_action_x - body_center_x
        falling = abs(fall_diff) > 50

        x = point_of_action_x
        y = -(1.251396648 * x) + 618

        if falling:
            if stage != "falling":
                stage = "falling"
                fall_start_time = time.time()
                print(f"Inicio de caída detectado en x={x}, y={y}")
            else:
                elapsed_time = time.time() - fall_start_time if fall_start_time else 0
                if elapsed_time > time_2_alert:
                    send_alert()
                    counter += 1
                    fall_start_time = None
        else:
            if stage == "falling":
                stage = "standing"
                print(f"Se ha levantado en x={x}, y={y}")
                fall_start_time = None

        cv2.putText(image, str(counter), 
                    (10,60), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,0,255), 2, cv2.LINE_AA)
        cv2.putText(image, stage, 
            (60,60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 1, cv2.LINE_AA)
        
        mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.imshow('Fall Detection', image)
       
        if cv2.waitKey(10) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
