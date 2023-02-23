import zmq
import math
import shlex
import subprocess

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:5555")

# subprocess.run(shlex.split(""))

def angle(result: list) -> int:
    result = list(map(float, result))

    x1 = result[0] - result[2]
    y1 = result[1] - result[3]
    x2 = result[4] - result[6]
    y2 = result[5] - result[7]
    
    dy = x2 - x1
    dx = y2 - y1
    
    return math.degrees(math.atan2(dy, dx))


while True:
    result = receiver.recv_pyobj()
    print(angle(result))