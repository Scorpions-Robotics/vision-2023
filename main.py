# import cv2
# from torch import hub

# # Load the model
# model = hub.load('yolov5_obb', 'custom', path='best.pt', force_reload=True, source='local', device='0')

# # Load the image
# img = cv2.cvtColor(cv2.imread('test.jpg'), cv2.COLOR_BGR2RGB)

# # Detect objects
# results = model(img)

# # Draw bounding boxes
# results.print()
# results.show()

import cv2

cap = cv2.VideoCapture(1)

while True:
    ret, frame = cap.read()
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break