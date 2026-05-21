#!/usr/bin/env python3
"""
MARC Localization — position par marqueur unique + cap IMU (BNO085).
L'orientation vient de l'IMU (fiable), la position d'UN marqueur ArUco.

Repère salle : origine = intersection de carreaux.
Angles salle : 0° = +Y, sens TRIGONOMÉTRIQUE (anti-horaire).
Le yaw IMU augmente en HORAIRE → on le convertit.
"""
import math
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CAMERA_URL = "https://localhost:5001"
SERVER_URL = "https://localhost:5000"

# ── CARTE DES MARQUEURS (positions x,y en mètres) ──
# (l'orientation des marqueurs n'est plus nécessaire grâce à l'IMU)
MARKERS_MAP = {
    3: (-0.58, 2.50),
    2: ( 2.17, 0.96),
    0: ( 0.55, -4.35),
}

# Offset IMU : yaw brut du BNO quand MARC est face à +Y de la salle.
# À CALIBRER au premier test (voir instructions).
#YAW_OFFSET = 171.6
YAW_OFFSET = 0


def get_detections():
    try:
        r = requests.get(f"{CAMERA_URL}/detections", verify=False, timeout=1)
        return r.json()
    except Exception as e:
        print(f"[LOC] Erreur caméra : {e}")
        return {}


def get_yaw():
    """Cap brut du BNO depuis le serveur."""
    try:
        r = requests.get(f"{SERVER_URL}/heading", verify=False, timeout=1)
        return r.json().get("yaw")
    except Exception as e:
        print(f"[LOC] Erreur cap : {e}")
        return None


def heading_salle(yaw_brut):
    """
    Convertit le yaw brut IMU (horaire) en cap dans le repère salle
    (trigo, 0° = +Y). Applique l'offset de calibration.
    """
    # yaw augmente en horaire ; repère salle est trigo (anti-horaire)
    # → on inverse le signe, et on retire l'offset
    h = (yaw_brut - YAW_OFFSET)
    return (h)  # normalise [-180, 180]


def localize():
    """
    Calcule (x, y, heading) de MARC.
    Utilise le cap IMU + chaque marqueur visible, moyenne les positions.
    Retourne {x, y, heading, n_markers, used} ou None.
    """
    yaw_brut = get_yaw()
    if yaw_brut is None:
        return None

    heading = heading_salle(yaw_brut)   # cap de MARC dans la salle

    detections = get_detections()
    positions = []
    used = []

    for mid_str, data in detections.items():
        mid = int(mid_str)
        if mid not in MARKERS_MAP:
            continue
        d = data.get("distance")
        a = data.get("angle")   # + = marqueur à droite de MARC
        if d is None or a is None:
            continue

        mx, my = MARKERS_MAP[mid]
        # Direction du marqueur dans le repère salle.
        # MARC regarde dans 'heading'. Le marqueur est vu à 'a' degrés
        # à droite → en repère trigo, on soustrait a.
        bearing = heading - a
        rad = math.radians(bearing)
        # 0° = +Y, trigo → x = -sin? Non : on définit x = sin, y = cos
        # (cap 0 = +Y ; cap +90 trigo = -X). Ajusté au test.
        marc_x = mx - d * math.sin(rad)
        marc_y = my + d * math.cos(rad)
        positions.append((marc_x, marc_y))
        used.append(mid)

    if not positions:
        return None

    avg_x = sum(p[0] for p in positions) / len(positions)
    avg_y = sum(p[1] for p in positions) / len(positions)

    return {
        "x": round(avg_x, 3),
        "y": round(avg_y, 3),
        "heading": round(heading, 1),
        "n_markers": len(positions),
        "used": used,
    }


if __name__ == "__main__":
    import time
    print("=== Localisation MARC (IMU + marqueur) ===")
    print(f"Carte : {MARKERS_MAP}")
    print(f"YAW_OFFSET actuel : {YAW_OFFSET}°\n")
    try:
        while True:
            loc = localize()
            if loc:
                print(f"x={loc['x']}m  y={loc['y']}m  cap={loc['heading']}°  "
                      f"(marqueurs {loc['used']})")
            else:
                yaw = get_yaw()
                print(f"Pas de localisation (cap brut IMU = {yaw}, "
                      f"aucun marqueur connu visible)")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nArrêt")
