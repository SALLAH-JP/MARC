#!/usr/bin/env python3
"""
MARC Camera Service — process caméra dédié.
Ouvre la caméra UNE fois, expose :
  /video       → flux MJPEG (pour l'interface web)
  /detections  → JSON des ArUco détectés (pour la navigation)
Port 5001 (HTTP simple, pas de SSL nécessaire en local).
"""
import os
import time
import math
import threading

import cv2
import cv2.aruco as aruco
import numpy as np
from flask import Flask, Response, jsonify
from picamera2 import Picamera2

# ── CONFIG ──
MARKER_SIZE_M = 0.077   # ⚠️ ta mesure : 77mm = 0.077 m
DISTANCE_CORRECTION = 0.738   # corrige le biais proportionnel mesuré
CALIB_FILE = os.path.expanduser("~/MARC/vision/camera_calibration.npz")
RESOLUTION = (640, 480)

# ── Calibration (optionnelle : si absente, pas de distance/angle) ──
calib_ok = False
camera_matrix = None
dist_coeffs = None
if os.path.exists(CALIB_FILE):
    calib = np.load(CALIB_FILE)
    camera_matrix = calib['camera_matrix']
    dist_coeffs = calib['dist_coeffs']
    calib_ok = True
    print(f"[CAM] Calibration chargée (erreur {calib['mean_error']:.3f} px)")
else:
    print("[CAM] ⚠️  Pas de calibration — distances indisponibles")

# ── Caméra ──
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(
    main={"size": RESOLUTION, "format": "RGB888"}))
picam2.start()
time.sleep(2)
print("[CAM] Caméra démarrée")

# ── ArUco ──
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
detector = aruco.ArucoDetector(aruco_dict, aruco.DetectorParameters())

# ── État partagé ──
latest_detections = {}     # {id: {distance, angle}}
latest_frame_jpeg = None   # dernier JPEG annoté
state_lock = threading.Lock()


def camera_loop():
    """Boucle unique : capture → détecte → annote → stocke."""
    global latest_detections, latest_frame_jpeg

    marker_pts = np.array([
        [-MARKER_SIZE_M/2,  MARKER_SIZE_M/2, 0],
        [ MARKER_SIZE_M/2,  MARKER_SIZE_M/2, 0],
        [ MARKER_SIZE_M/2, -MARKER_SIZE_M/2, 0],
        [-MARKER_SIZE_M/2, -MARKER_SIZE_M/2, 0]
    ], dtype=np.float32)

    while True:
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        corners, ids, _ = detector.detectMarkers(gray)

        frame_bgr = frame.copy()
        detections = {}

        if ids is not None:
            aruco.drawDetectedMarkers(frame_bgr, corners, ids)
            for i, mid in enumerate(ids.flatten()):
                entry = {}
                if calib_ok:
                    ok, rvec, tvec = cv2.solvePnP(
                        marker_pts, corners[i][0], camera_matrix, dist_coeffs)
                    if ok:
                        distance = float(np.linalg.norm(tvec)) * DISTANCE_CORRECTION
                        angle = math.degrees(math.atan2(tvec[0][0], tvec[2][0]))
                        entry = {'distance': round(distance, 3),
                                 'angle': round(angle, 1)}
                        cv2.drawFrameAxes(frame_bgr, camera_matrix, dist_coeffs,
                                          rvec, tvec, MARKER_SIZE_M/2)
                        c = corners[i][0][0]
                        label = f"ID{mid} {distance:.2f}m {angle:+.0f}deg"
                        cv2.putText(frame_bgr, label, (int(c[0]), int(c[1]) - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    else:
                        entry = {'distance': None, 'angle': None}
                else:
                    # Pas de calibration : on signale juste la présence
                    c = corners[i][0][0]
                    cv2.putText(frame_bgr, f"ID{mid}", (int(c[0]), int(c[1]) - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    entry = {'distance': None, 'angle': None}
                detections[int(mid)] = entry

        _, buf = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])

        with state_lock:
            latest_detections = detections
            latest_frame_jpeg = buf.tobytes()


app = Flask(__name__)


@app.route('/video')
def video():
    def gen():
        while True:
            with state_lock:
                frame = latest_frame_jpeg
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.04)  # ~25 fps max côté HTTP
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/detections')
def detections():
    with state_lock:
        return jsonify(latest_detections)


@app.route('/health')
def health():
    return jsonify({"calibration": calib_ok, "marker_size_m": MARKER_SIZE_M})


if __name__ == '__main__':
    threading.Thread(target=camera_loop, daemon=True).start()
    WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")
    cert = os.path.join(WEB_DIR, 'cert.pem')
    key  = os.path.join(WEB_DIR, 'key.pem')
    print("[CAM] Service démarré sur https://0.0.0.0:5001")
    app.run(host='0.0.0.0', port=5001, threaded=True,
            ssl_context=(cert, key))
