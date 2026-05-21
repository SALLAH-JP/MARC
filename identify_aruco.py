"""
Identifie les marqueurs ArUco visibles : teste les dictionnaires courants
et affiche les IDs détectés. Montre les 4 marqueurs à la caméra.
"""
from picamera2 import Picamera2
import cv2
import cv2.aruco as aruco
import time

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"}))
picam2.start()
time.sleep(2)

dicts = {
    "DICT_4X4_50": aruco.DICT_4X4_50,
    "DICT_5X5_50": aruco.DICT_5X5_50,
    "DICT_6X6_50": aruco.DICT_6X6_50,
    "DICT_7X7_50": aruco.DICT_7X7_50,
    "DICT_ARUCO_ORIGINAL": aruco.DICT_ARUCO_ORIGINAL,
}

print("Montre tes marqueurs à la caméra... (Ctrl+C pour arrêter)\n")

try:
    while True:
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        
        for name, dict_id in dicts.items():
            d = aruco.getPredefinedDictionary(dict_id)
            detector = aruco.ArucoDetector(d, aruco.DetectorParameters())
            corners, ids, _ = detector.detectMarkers(gray)
            if ids is not None:
                print(f"[{name}] détecté IDs : {sorted(ids.flatten().tolist())}")
        
        time.sleep(1)
except KeyboardInterrupt:
    print("\nArrêt")
finally:
    picam2.stop()
