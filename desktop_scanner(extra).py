import cv2
import numpy as np
from pyzbar.pyzbar import decode
from flask import Flask, render_template, Response
app = Flask(__name__)

def decoder(image):
    gray_img = cv2.cvtColor(image, 0)
    barcode = decode(gray_img)

    for obj in barcode:
        points = obj.polygon
        (x, y, w, h) = obj.rect
        pts = np.array(points, np.int32)
        pts = pts.reshape((-1, 1, 2))
        cv2.polylines(image, [pts], True, (0, 255, 0), 3)

        barcodeData = obj.data.decode("utf-8")
        barcodeType = obj.type
        string = "Data " + str(barcodeData) + " | Type " + str(barcodeType)
        cv2.putText(image, string, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

        img = cv2.imread("dog.jpg")
        img = cv2.resize(img, (x, y))
        x_offset = y_offset = 50
        image[y_offset:y_offset + img.shape[0], x_offset:x_offset + img.shape[1]] = img

        print("Barcode: " + barcodeData + " | Type: " + barcodeType)



cap = cv2.VideoCapture(0)
def gen_frames():
    while True:
        ret, frame = cap.read()
        decoder(frame)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/scan')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
  app.run(debug=True)