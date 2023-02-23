import zmq

context = zmq.Context()
receiver = context.socket(zmq.PULL)
receiver.connect("tcp://localhost:5555")


def angle(result: int) -> int:
    ...


while True:
    result = receiver.recv_pyobj()
    print(angle(result))