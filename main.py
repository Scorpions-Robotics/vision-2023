import math
import os
import shlex
import subprocess
import sys
from configparser import ConfigParser

import cv2
import zmq
from mjpeg_streamer import Stream, MjpegServer
from networktables import NetworkTables

config = ConfigParser()
config.read("config.ini")

context = zmq.Context()
annotation_receiver = context.socket(zmq.PULL)
annotation_receiver.connect("tcp://127.0.0.1:5804")
video_receiver = context.socket(zmq.PULL)
video_receiver.connect("tcp://127.0.0.1:5803")

networktables_disabled = config.getboolean("default", "disable_networktables")

if not networktables_disabled:
    try:
        NetworkTables.initialize(server=config.get("default", "networktables_server"))
        nt_table = NetworkTables.getTable("ScorpionsVision")
    except Exception as e:
        print(e)

cmd_v4l2 = f"v4l2-ctl -v width={config.get('default', 'width')},\
height={config.get('default', 'height')},pixelformat=MJPG \
--set-parm {config.get('default', 'fps')} -d {config.get('default', 'camera_index')}"

source_str = config.get("default", "camera_index") if config.get("default", "gstreamer_cap") \
    else f"""'v4l2src device=/dev/video{config.get("default", "camera_index")} ! video/x-raw, width={config.get('default', 'width')}, \
height={config.get('default', 'height')}, pixelformat=MJPG ! videoscale ! videoconvert ! appsink'"""

cmd_yolo = f"""
python3 yolov5_obb/detect.py --source {source_str} --stream \
--weights {config.get('default', 'weights')} --conf-thres {config.get('default', 'confidence_threshold')} \
--device {config.get('default', 'computation_device')} --imgsz {config.get('default', 'size')} \
--max-det {config.get('default', 'max_detections')} {"--half" if config.get('default', 'half_precision') == "True" else ""} \
{"--nosave" if config.get('default', 'save') == "False" else ""} \
{"--hide-labels" if config.get('default', 'hide_labels') == "True" else ""} \
{"--hide-conf" if config.get('default', 'hide_conf') == "True" else ""}
"""

posix = os.name != "nt"
print(
    cmd_v4l2
    if config.getboolean("default", "set_camera_options")
    else "Camera options not set"
)
set_camera_options = (
    subprocess.run(shlex.split(cmd_v4l2, posix=posix))
    if config.getboolean("default", "set_camera_options")
    else None
)

print(cmd_yolo)

stream = Stream("cone", size=(640, 480), quality=10, fps=30)
server = MjpegServer(config.get("default", "ip"), 5807)
server.add_stream(stream)

def angle(result: list) -> int:
    """Takes coordinates (x, y) of a rectangle and returns the degrees from the y-axis."""

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

    returned_degrees = abs(abs(degrees) - 90) * -1 if degrees < 0 else degrees - 90 * -1

    if returned_degrees < -90:
        returned_degrees = returned_degrees + 180 * -1

    elif returned_degrees > 90:
        returned_degrees = (returned_degrees - 180) * -1

    return returned_degrees


def main_func():
    while True:
        video = video_receiver.recv_pyobj()
        angle_data = annotation_receiver.recv_pyobj()
        degrees = angle(angle_data)

        cv2.putText(
            video,
            str(degrees),
            (10, video.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3,
        )

        stream.set_frame(video)
        
        if not networktables_disabled:
            try:
                nt_table.putString("cone", str(degrees))
            except Exception as e:
                print(e)


if __name__ == "__main__":
    try:
        yolo = subprocess.Popen(shlex.split(cmd_yolo, posix=posix))
        server.start()
        main_func()

    except KeyboardInterrupt:
        yolo.kill()
        server.stop()
        print("Program terminated by user")
        sys.exit(0)
    except Exception as e:
        print(e)
