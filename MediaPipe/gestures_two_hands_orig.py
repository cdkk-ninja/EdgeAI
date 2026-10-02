import os
os.environ['GLOG_minloglevel'] = '2'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import cv2
from picamera2 import Picamera2 
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# 1. Initialize Gesture Recognizer with multi-hand support
path_MediaPipe_models = "MediaPipe/"
base_options = python.BaseOptions(model_asset_path=path_MediaPipe_models+'gesture_recognizer.task')
options = vision.GestureRecognizerOptions(
    base_options=base_options,
    num_hands=2  # <--- Detects up to 2 hands simultaneously
)
recognizer = vision.GestureRecognizer.create_from_options(options)

# 2. Configure Picamera2
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

# Enable continuous autofocus and auto white balance
picam2.set_controls({
    "AfMode": 2,
    "AwbMode": 0
})

# Setup display window thread for Wayland compatibility
cv2.namedWindow("Pi 5 Multi-Hand Gesture Recognizer", cv2.WINDOW_AUTOSIZE)
cv2.startWindowThread()

print("Camera active with GestureRecognizer. Show up to 2 hands! Press 'q' to quit.")

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
        
        # Recognize gestures across all detected hands
        result = recognizer.recognize(mp_image)

        # Process each hand's detected gesture and landmarks
        if result.gestures:
            for idx, hand_gestures in enumerate(result.gestures):
                if not hand_gestures:
                    continue

                # Get top predicted gesture name and confidence score
                top_gesture = hand_gestures[0]
                gesture_name = top_gesture.category_name
                score = top_gesture.score

                # Draw landmark points for this hand (if available)
                if result.hand_landmarks and len(result.hand_landmarks) > idx:
                    hand_landmarks = result.hand_landmarks[idx]
                    for lm in hand_landmarks:
                        h, w, _ = display_frame.shape
                        cx, cy = int(lm.x * w), int(lm.y * h)
                        cv2.circle(display_frame, (cx, cy), 4, (0, 255, 0), -1)

                    # Position label near the wrist of this specific hand
                    h, w, _ = display_frame.shape
                    wrist_x = int(hand_landmarks[0].x * w)
                    wrist_y = int(hand_landmarks[0].y * h) - 20
                else:
                    # Fallback coordinate if landmarks aren't mapped
                    wrist_x, wrist_y = 30, 50 + (idx * 40)

                # Render label above the hand
                label = f"Hand {idx+1}: {gesture_name} ({score:.2f})"
                cv2.putText(
                    display_frame, 
                    label, 
                    (max(10, wrist_x - 50), max(30, wrist_y)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.8, 
                    (0, 255, 255), 
                    2, 
                    cv2.LINE_AA
                )

        # Display output
        cv2.imshow("Pi 5 Multi-Hand Gesture Recognizer", display_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    recognizer.close()