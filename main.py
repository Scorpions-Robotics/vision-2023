import math
import os
import shlex
import subprocess
import sys
import threading
from configparser import ConfigParser

import cv2
import imutils
import zmq
from flask import Flask, Response, render_template, request

config = ConfigParser()
config.read("config.ini")

context = zmq.Context()
annotation_receiver = context.socket(zmq.PULL)
annotation_receiver.connect("tcp://127.0.0.1:5805")
video_receiver = context.socket(zmq.PULL)
video_receiver.connect("tcp://127.0.0.1:5806")

browser_frame = None
lock = threading.Lock()

cmd = f"""
python3 yolov5_obb/detect.py --source {config.get('default', 'source')} --stream \
--weights {config.get('default', 'weights')} --conf-thres {config.get('default', 'confidence_threshold')} \
--device {config.get('default', 'device')} --imgsz {config.get('default', 'size')} \
--max-det {config.get('default', 'max_detections')} {"--half" if config.get('default', 'half_precision') == "True" else ""} \
{"--nosave" if config.get('default', 'save') == "False" else ""} \
{"--hide-labels" if config.get('default', 'hide_labels') == "True" else ""} \
{"--hide-conf" if config.get('default', 'hide_conf') == "True" else ""}
"""

yolo = subprocess.Popen(shlex.split(cmd, posix=os.name != "nt"))


def angle(result: list) -> int:
    """Takes coordinates (x, y) of a rectangle and returns the angles to turn."""

    if isinstance(result, str):
        return result

    result = list(map(float, result))

    x1 = result[1] - result[3]
    y1 = result[2] - result[4]
    x2 = result[5] - result[7]
    y2 = result[6] - result[8]

    dy = x2 - x1
    dx = y2 - y1
    degrees = round(math.degrees(math.atan2(dy, dx)))

    return math.abs(math.abs(degrees) - 90) if degrees < 0 else degrees - 90


def data():
    global browser_frame, lock

    while True:
        r_data: tuple = annotation_receiver.recv_pyobj(), video_receiver.recv_pyobj()
        data[0] = imutils.resize(r_data[0], width=config.get("default", "size"))
        degrees = angle(r_data[1])

        cv2.putText(
            r_data[0],
            degrees,
            (10, r_data[0].shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.35,
            (0, 0, 255),
            1,
        )

        with lock:
            browser_frame = r_data[0].copy()


def generate():
    global browser_frame, lock

    while True:
        with lock:
            if browser_frame is None:
                continue

            val, encodedImage = cv2.imencode(".jpg", browser_frame)

            if not val:
                continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + bytearray(encodedImage) + b"\r\n"
        )


# Flask Section
app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")


def shutdown_server():
    sd_func = request.environ.get("werkzeug.server.shutdown")
    if sd_func is None:
        print("Server not running")
    sd_func()


if __name__ == "__main__":
    try:
        t = threading.Thread(target=data)
        t.daemon = True
        t.start()

        app.run(
            host=config.get("default", "flask_ip"),
            port=5807,
            debug=True,
            threaded=True,
            use_reloader=False,
        )

    except KeyboardInterrupt:
        yolo.kill()
        shutdown_server()
        print("Program terminated by user")
        sys.exit(0)
