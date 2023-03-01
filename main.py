import zmq
import cv2
import os
import math
import shlex
import subprocess
from configparser import ConfigParser


config = ConfigParser()
config.read("config.ini")

context = zmq.Context()
angle_receiver = context.socket(zmq.PULL)
angle_receiver.connect("tcp://localhost:5805")
video_receiver = context.socket(zmq.PULL)
video_receiver.connect("tcp://localhost:5806")

cmd = f"""
python3 yolov5_obb/detect.py --source {config.get('default', 'source')} \
--weights {config.get('default', 'weights')} --conf-thres {config.get('default', 'confidence_threshold')} \
--device {config.get('default', 'device')} --imgsz {config.get('default', 'size')} \
--max-det {config.get('default', 'max_detections')} {"--half" if config.get('default', 'half_precision') == "True" else ""} \
{"--nosave" if config.get('default', 'save') == "False" else ""} \
{"--view-img" if config.get('default', 'view_img') == "True" else ""} \
{"--stream" if config.get('default', 'stream') == "True" else ""} \
{"--hide-labels" if config.get('default', 'hide_labels') == "True" else ""} \
{"--hide-conf" if config.get('default', 'hide_conf') == "True" else ""}
"""

yolo = subprocess.Popen(shlex.split(cmd, posix=os.name != "nt"))


def angle(result: list) -> int:
    if isinstance(result, str):
        return result

    result = list(map(float, result))

    x1 = result[1] - result[3]
    y1 = result[2] - result[4]
    x2 = result[5] - result[7]
    y2 = result[6] - result[8]

    dy = x2 - x1
    dx = y2 - y1
    degrees =  math.degrees(math.atan2(dy, dx))
    return math.abs(degrees - 90), math.degrees(math.atan2(dy, dx))  # degrees to turn, raw degrees


while True:
    if config.getboolean('default', 'stream'):
        result = angle_receiver.recv_pyobj()
        print(angle(result))
        video = video_receiver.recv_pyobj()
        cv2.imshow("video", video)
        cv2.waitKey(1)
