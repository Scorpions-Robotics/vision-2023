import zmq
import os
import math
import shlex
import subprocess
from configparser import ConfigParser

config = ConfigParser()
config.read("config.ini")

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:5555")

cmd = f"""
python yolov5_obb/detec.py --source {config.get('default', 'source')} \
--weights {config.get('default', 'weights')} --conf-thres {config.get('default', 'confidence_threshold')} \
--device {config.get('default', 'device')} --imgsz {config.get('default', 'size')} \
--max-det {config.get('default', 'max_detections')} {"--half" if config.get('default', 'half_precision') == "True" else ""} \
{"--nosave" if config.get('default', 'save') == "False" else ""} \
{"--view-img" if config.get('default', 'view_img') == "True" else ""} \
{"--stream-img" if config.get('default', 'stream_img') == "True" else ""} \
{"--hide-labels" if config.get('default', 'hide_labels') == "True" else ""} \
{"--hide-conf" if config.get('default', 'hide_conf') == "True" else ""}
"""

yolo = subprocess.Popen(shlex.split(cmd, posix=os.name != "nt"), shell=True, check=True)


def angle(result: list) -> int:
    result = list(map(float, result))

    x1 = result[1] - result[3]
    y1 = result[2] - result[4]
    x2 = result[5] - result[7]
    y2 = result[6] - result[8]

    dy = x2 - x1
    dx = y2 - y1

    return math.degrees(math.atan2(dy, dx))


while True:
    result = receiver.recv_pyobj()
    print(angle(result))
