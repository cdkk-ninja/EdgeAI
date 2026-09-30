import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
import numpy as np
import math
from picamera2 import Picamera2 
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Initialize MediaPipe Hand Landmarker
path_MediaPipe_models = "MediaPipe/"
base_options = python.BaseOptions(model_asset_path=path_MediaPipe_models+'hand_landmarker.task')
options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=1
)
landmarker = vision.HandLandmarker.create_from_options(options)

# 2. Configure Picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

# Enable Auto White Balance with continuous autofocus
picam2.set_controls({
    "AfMode": 2,          # Continuous Autofocus
    "AwbMode": 0          # Auto White Balance
})

# Enable window thread for Wayland display compatibility
cv2.namedWindow("Pi 5 Horizontal Scissors Recognition", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

def distance(p1, p2):
    """Calculates Euclidean distance between two MediaPipe landmark points."""
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2 + (p1.z - p2.z)**2)

def is_scissors_gesture(landmarks):
    """
    Landmark Indices:
    - Wrist: 0
    - Index Finger: MCP = 5, Tip = 8
    - Middle Finger: MCP = 9, Tip = 12
    - Ring Finger: MCP = 13, Tip = 16
    - Pinky Finger: MCP = 17, Tip = 20
    """
    wrist = landmarks[0]

    # Distance from wrist to finger tips
    index_dist = distance(landmarks[8], wrist)
    middle_dist = distance(landmarks[12], wrist)
    ring_dist = distance(landmarks[16], wrist)
    pinky_dist = distance(landmarks[20], wrist)

    # Distance from wrist to knuckle joints (MCP joints)
    ring_mcp_dist = distance(landmarks[13], wrist)
    pinky_mcp_dist = distance(landmarks[17], wrist)

    # 1. Index and Middle fingers must be extended (tips far from wrist)
    index_extended = index_dist > 1.2 * distance(landmarks[5], wrist)
    middle_extended = middle_dist > 1.2 * distance(landmarks[9], wrist)

    # 2. Ring and Pinky fingers must be folded (tips close to knuckles/wrist)
    ring_folded = ring_dist < 1.3 * ring_mcp_dist
    pinky_folded = pinky_dist < 1.3 * pinky_mcp_dist

    # 3. Index and Middle finger tips should be separated slightly (scissors blades open/closed)
    fingers_separated = distance(landmarks[8], landmarks[12]) > 0.04

    return index_extended and middle_extended and ring_folded and pinky_folded and fingers_separated

print("Camera started. Point scissors horizontally or vertically! Press 'q' to quit.")

try:
    while True:
        frame_bgr = picam2.capture_array("main")
        
        if frame_bgr is None or frame_bgr.size == 0:
            continue

        # Flip horizontally for natural mirror view
        display_frame = cv2.flip(frame_bgr, 1)

        # Convert BGR array to RGB for MediaPipe
        frame_rgb = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        
        # Perform hand landmark detection
        result = landmarker.detect(mp_image)

        # Draw detected landmarks and check gesture
        if result.hand_landmarks:
            for hand_landmarks in result.hand_landmarks:
                # Draw keypoints on display frame
                for lm in hand_landmarks:
                    h, w, _ = display_frame.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    cv2.circle(display_frame, (cx, cy), 4, (0, 255, 0), -1)

                # Check if gesture matches orientation-agnostic Scissors
                if is_scissors_gesture(hand_landmarks):
                    cv2.putText(
                        display_frame, 
                        "Gesture: SCISSORS", 
                        (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        1.0, 
                        (0, 255, 0), 
                        2, 
                        cv2.LINE_AA
                    )

        # Render display frame
        cv2.imshow("Pi 5 Horizontal Scissors Recognition", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    landmarker.close()
