import cv2
from torch import hub

# Load the model
model = hub.load('yolov5_obb', 'custom', path='best.pt', force_reload=True, source='local', device='0')

# Load the image
img = cv2.cvtColor(cv2.imread('test.jpg'), cv2.COLOR_BGR2RGB)

# Detect objects
results = model(img)

# Draw bounding boxes
results.print()
results.show()