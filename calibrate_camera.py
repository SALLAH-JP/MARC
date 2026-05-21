"""
Calibration caméra IMX219 avec damier 9x6 (coins internes).
Montre le damier (téléphone) sous différents angles, le script capture auto.
"""
import cv2
import numpy as np
from picamera2 import Picamera2
import time
import os

CHESSBOARD_SIZE = (9, 6)   # COINS INTERNES (= 10x7 cases)
SQUARE_SIZE_M = 0.010      # 10mm par case sur ton téléphone
NUM_CAPTURES = 20
output_file = os.path.expanduser("~/PFE/camera_calibration.npz")

objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
objp *= SQUARE_SIZE_M

objpoints, imgpoints = [], []

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (1280, 720), "format": "RGB888"}))
picam2.start()
time.sleep(2)

print(f"Objectif : {NUM_CAPTURES} captures. Bouge le damier sous différents angles.\n")
captures = 0
last_t = 0

try:
    while captures < NUM_CAPTURES:
        frame = picam2.capture_array()
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD_SIZE,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_NORMALIZE_IMAGE)
        now = time.time()
        if ret and (now - last_t) > 2.0:
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            objpoints.append(objp)
            imgpoints.append(corners2)
            captures += 1
            last_t = now
            print(f"  Capture {captures}/{NUM_CAPTURES} OK")
        time.sleep(0.1)

    print("\nCalcul...")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None)

    total_error = 0
    for i in range(len(objpoints)):
        imgp2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], mtx, dist)
        total_error += cv2.norm(imgpoints[i], imgp2, cv2.NORM_L2) / len(imgp2)
    mean_error = total_error / len(objpoints)

    np.savez(output_file, camera_matrix=mtx, dist_coeffs=dist, mean_error=mean_error)
    print(f"\nOK Calibration sauvée : {output_file}")
    print(f"Erreur moyenne : {mean_error:.4f} px (<0.5 excellent, <1.0 bon)")
finally:
    picam2.stop()
