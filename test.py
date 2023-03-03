

import cv2

# This pipeline captures screen @ 30 fps, resize to 1280x720, and convert into BGR 
cap = cv2.VideoCapture("ximagesrc use_damage=0 ! nvvidconv ! video/x-raw(memory:NVMM), format=(string)NV12, width=640,height=480,framerate=(fraction)30/1 ! nvvidconv ! video/x-raw, format=(string)BGRx ! videoconvert ! video/x-raw, format=(string)BGR ! queue ! appsink drop=1", cv2.CAP_GSTREAMER)
if not cap.isOpened():
   print('Failed to open camera')
   exit(-1)

# This pipeline converts to NV12 format into NVMM memory, encodes into h264, 
# then forks into one branch streaming as RTP-MP2T to localhost port 5004, 
# and one branch putting into MP4/MOV container and save to file.
out = cv2.VideoWriter("appsrc ! queue ! videoconvert ! video/x-raw,format=BGRx ! nvvidconv ! nvv4l2h264enc insert-sps-pps=1 insert-vui=1 idrinterval=15 ! tee name=t ! queue ! h264parse ! mpegtsmux ! rtpmp2tpay ! udpsink host=127.0.0.1 port=5004", cv2.CAP_GSTREAMER, 0, 30.0, (640,480)) 
if not out.isOpened():
   print('Failed to open output writer')
   cap.release()
   exit(-2)


# Loop for 100 seconds
for i in range(3000):
	# Read image from capture
	ret_val, img = cap.read()
	if not ret_val:
		break

	# Push processed image into writer
	out.write(img)
	
out.release()
cap.release()
