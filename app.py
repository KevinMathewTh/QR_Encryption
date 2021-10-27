from flask import Flask, render_template, Response, request
from flask_mysqldb import MySQL
from main import AES_Object
from AES import AESCipher
import string
import random
import qrcode
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import MySQLdb
import base64
import os
from werkzeug.utils import secure_filename
import time





app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'aes_qr_db'

mysql = MySQL(app)


def decoder(image,aes_key):
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
        # string = "Data " + str(barcodeData) + " | Type " + str(barcodeType)
        # cv2.putText(image, string, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

        # Open database connection
        db = MySQLdb.connect("localhost", "root", "", "aes_qr_db")

        # prepare a cursor object using cursor() method
        cursor = db.cursor()

        # execute SQL query using execute() method.
        cursor.execute("SELECT string FROM qr_table WHERE qr_key = '"+barcodeData +"' ")

        # Fetch a single row using fetchone() method.
        data = str(cursor.fetchone()[0])
        print("Database version : %s " % data)

        # disconnect from server
        db.close()
        AES_Obj1 = AESCipher(aes_key)
        # print(type(data))
        try:
            start_time = time.time()
            aes_decrypt = AES_Obj1.decrypt(data)
            aes_decrypt = aes_decrypt.encode("utf-8")
            imgdata = base64.b64decode(aes_decrypt)

            filename = 'decrypted'+barcodeData+'.jpg'  # I assume you have a way of picking unique filenames
            with open(filename, 'wb') as f:
                f.write(imgdata)

            img = cv2.imread("decrypted"+barcodeData+".jpg")
            img = cv2.resize(img, (x, y))
            x_offset = y_offset = 50
            image[y_offset:y_offset + img.shape[0], x_offset:x_offset + img.shape[1]] = img
            os.remove("decrypted" + barcodeData + ".jpg")
            print("Decryption time --- %s seconds ---" % (time.time() - start_time))
        except:
            img = cv2.imread("404.png")
            img = cv2.resize(img, (x, y))
            x_offset = y_offset = 50
            image[y_offset:y_offset + img.shape[0], x_offset:x_offset + img.shape[1]] = img


        print("Barcode: " + barcodeData + " | Type: " + barcodeType)

cap = cv2.VideoCapture(0)

def gen_frames(aes_key):
    while True:
        ret, frame = cap.read()
        decoder(frame,aes_key)
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # concat frame one by one and show result

@app.route('/scan', methods=['POST', 'GET'])
def video_feed():
    if request.method == 'GET':
        return "Login via the login Form"

    if request.method == 'POST':
        aes_key = request.form['aes_key']
        return Response(gen_frames(aes_key), mimetype='multipart/x-mixed-replace; boundary=frame')



@app.route('/enterkey')
def enter_key():
    return render_template('form_enterkey.html')


@app.route('/')
def form():
    return render_template('form.html')



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return "Login via the login Form"

    if request.method == 'POST':
        start_time = time.time()
        length = 5
        qr_key = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        img = qrcode.make(qr_key)
        img.save("static/qrcode.png")
        aes_key = request.form['aes_key']
        f = request.files['file']
        filename="encrypted" + qr_key + ".jpg"
        f.save(secure_filename(filename))

        AES_Obj = AES_Object(aes_key,filename)
        AES_str = AES_Obj.return_aes_encrypt()
        cursor = mysql.connection.cursor()
        cursor.execute(''' INSERT INTO qr_table VALUES(%s,%s)''', (qr_key,AES_str))
        mysql.connection.commit()
        cursor.close()
        os.remove(filename)
        print("Encryption time --- %s seconds ---" % (time.time() - start_time))
        return render_template('QR.html')


app.run(host='localhost', port=5000)