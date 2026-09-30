import cv2
from picamera2 import Picamera2

# Initialize Picamera2
picam2 = Picamera2()

# Request "RGB888" - in libcamera/Picamera2, this outputs BGR-ordered 
# bytes in memory, matching OpenCV's native rendering pipeline!
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

# Continuous autofocus for Camera Module 3
picam2.set_controls({"AfMode": 2})

# OpenCV window setup
cv2.namedWindow("Corrected Color Feed", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

print("Displaying camera feed. Press 'q' to exit.")

try:
    while True:
        # Array arrives directly formatted for OpenCV
        frame = picam2.capture_array("main")

        if frame is None or frame.size == 0:
            continue

        # Flip horizontally for natural mirror view
        frame = cv2.flip(frame, 1)

        # Display frame in OpenCV (Colors will now be 100% accurate)
        cv2.imshow("Corrected Color Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    