import cv2
import requests
import numpy as np
from ultralytics import YOLO

stream_url = "http://192.168.0.0/1600x1200.mjpeg"

model = YOLO("yolov8n.pt")

stream = requests.get(stream_url, stream=True)
cv2.namedWindow("Camera Stream", cv2.WINDOW_NORMAL)

buffer = b''

for chunk in stream.iter_content(chunk_size=1024):
    buffer += chunk

    start = buffer.find(b'\xff\xd8')
    end = buffer.find(b'\xff\xd9')

    if start != -1 and end != -1:
        jpg = buffer[start:end + 2]
        buffer = buffer[end + 2:]

        img_np = np.frombuffer(jpg, dtype=np.uint8)
        img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

        results = model(img)

        for r in results[0].boxes:
            class_id = int(r.cls[0])
            confidence = r.conf[0]

            if class_id == 0 and confidence > 0.5:
                x1, y1, x2, y2 = map(int, r.xyxy[0])

                box_width = x2 - x1
                box_height = y2 - y1

                if box_width > box_height * 1.5:
                    text = "Posible caída detectada"
                    cv2.putText(img, text, (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

                person_text = f"Person: {confidence:.2f}"
                cv2.putText(img, person_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow("Camera Stream", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()
