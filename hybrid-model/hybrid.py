from flask import Flask, render_template, Response, request, jsonify
import cv2
import os
import time
import pytesseract
from PIL import Image
import requests

app = Flask(__name__)

KNOWN_DISTANCE = 1.143
VEHICLE_WIDTH = 70
CONFIDENCE_THRESHOLD = 0.4
NMS_THRESHOLD = 0.1
plate_detector = cv2.CascadeClassifier("BD_numberPlate_cascade_v1.xml")

cap = cv2.VideoCapture('./Data/vid5.mp4')
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

home_dir = os.path.expanduser("~")
save_dir = os.path.join(home_dir, "Captured_Plates")

yoloNet = cv2.dnn.readNet('yolov4-tiny.weights', 'yolov4-tiny.cfg')
yoloNet.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
yoloNet.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA_FP16)

# OCR function
def perform_ocr(image_path):
    # Use pytesseract to perform OCR on the image
    text = pytesseract.image_to_string(Image.open(image_path))
    return text

# Specify the scaling factor for the captured plate image
scaling_factor = 5

model = cv2.dnn_DetectionModel(yoloNet)
model.setInputParams(size=(416, 416), scale=1/255, swapRB=True)

def process_frames():
    while True:
        ret, frame = cap.read()

        if not ret:
            break

        frame = cv2.resize(frame, (464, 464))
        classes, scores, boxes = model.detect(frame, CONFIDENCE_THRESHOLD, NMS_THRESHOLD)

        if classes is not None:
            high_confidence_indices = [i for i, score in enumerate(scores) if score >= CONFIDENCE_THRESHOLD]

            for i in high_confidence_indices:
                classid = int(classes[i])
                score = float(scores[i])
                box = boxes[i]

                if classid == 2 or classid == 7 or classid == 3:
                    distance = (VEHICLE_WIDTH * KNOWN_DISTANCE) / box[2]
                    vehicle_color = (0, 255, 0)  # Green
                    text_color = (0, 0, 0)  # Black

                    if distance < 1:
                        vehicle_color = (0, 0, 255)  # Red
                        text_color = (0, 0, 255)  # Red

                    cv2.rectangle(frame, box, vehicle_color, 1)

                    distance_text = f"{round(distance, 2)} m"
                    text_size, _ = cv2.getTextSize(distance_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                    text_x = box[0] + int((box[2] - text_size[0]) / 2)
                    text_y = box[1] - 10
                    cv2.rectangle(frame, (text_x - 2, text_y - text_size[1] - 2),
                                  (text_x + text_size[0] + 2, text_y + 2), (0, 0, 0), -1)
                    cv2.putText(frame, distance_text, (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

                    if distance < 1:
                        alert_text = "Vehicle Detected!"
                        alert_size, _ = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                        alert_x = box[0] + int((box[2] - alert_size[0]) / 2)
                        alert_y = box[1] + box[3] + 20
                        cv2.rectangle(frame, (alert_x - 2, alert_y - alert_size[1] - 2),
                                      (alert_x + alert_size[0] + 2, alert_y + 2), (0, 0, 0), -1)
                        cv2.putText(frame, alert_text, (alert_x, alert_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, text_color, 1, cv2.LINE_AA)

                        plate = plate_detector.detectMultiScale(
                            frame[box[1]:box[1]+box[3], box[0]:box[0]+box[2]], scaleFactor=1.05, minNeighbors=5, minSize=(60, 80))

                        for (x_plate, y_plate, w_plate, h_plate) in plate:
                            cv2.rectangle(frame, (x_plate + box[0], y_plate + box[1]),
                                          (x_plate + w_plate + box[0], y_plate + h_plate + box[1]), (0, 0, 255), 2)
                            cv2.putText(frame, text='BRTA-Approved License Plate', org=(x_plate + box[0] - 3, y_plate + box[1] - 3),
                                        fontFace=cv2.FONT_HERSHEY_COMPLEX, color=(0, 0, 255), thickness=1, fontScale=0.6)

                            # Save the image temporarily
                            temp_image_path = 'temp_plate_image.png'
                            plate_region = frame[y_plate + box[1]:y_plate + h_plate + box[1], x_plate + box[0]:x_plate + w_plate + box[0]]
                            resized_plate = cv2.resize(plate_region, None, fx=scaling_factor, fy=scaling_factor)
                            cv2.imwrite(temp_image_path, resized_plate)

                            # Perform OCR on the image
                            ocr_result = perform_ocr(temp_image_path)

                            # Send the OCR result to a separate backend server
                            backend_url = 'http://localhost:3000/api/process_ocr'
                            payload = {'text': ocr_result}

                            response = requests.post(backend_url, json=payload)
                            response.raise_for_status()

                            response_data = response.json()
                            print(response_data)

                            # Clean up the temporary image file
                            if os.path.exists(temp_image_path):
                                os.remove(temp_image_path)

        ret, jpeg = cv2.imencode('.jpg', frame)

        if not ret:
            print("Error encoding frame to JPEG.")
            continue

        frame_data = jpeg.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

        time.sleep(0.1)

    cap.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(process_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
