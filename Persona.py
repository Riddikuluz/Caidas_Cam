import cv2
import requests
import numpy as np

stream_url = "http://192.168.0.0/1600x1200.mjpeg"

model_path = "models/mobilenet_iter_73000.caffemodel"
config_path = "models/deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(config_path, model_path)

# CUDA
# net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
# net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

confidence_threshold = 0.5
person_class_id = 15

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

        blob = cv2.dnn.blobFromImage(img, 0.007843, (300, 300), 127.5)
        net.setInput(blob)
        detections = net.forward()

        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            if confidence > confidence_threshold:
                class_id = int(detections[0, 0, i, 1])
                if class_id == person_class_id:
                    box = detections[0, 0, i, 3:7] * [img.shape[1], img.shape[0], img.shape[1], img.shape[0]]
                    (startX, startY, endX, endY) = box.astype("int")
                    cv2.rectangle(img, (startX, startY), (endX, endY), (0, 255, 0), 2)
                    text = f"Person: {confidence:.2f}"
                    cv2.putText(img, text, (startX, startY - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.imshow("Camera Stream", img)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cv2.destroyAllWindows()