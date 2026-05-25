#!/usr/bin/env python3
"""
MARC Localization — position par marqueur ArUco + cap IMU + fusion odométrie.

- Cap (heading) : fourni par le BNO085 via /odometry (fiable en continu).
- Position (x,y) : calculée depuis un marqueur ArUco visible.
- Fusion : si aucun marqueur visible, on intègre le déplacement odométrique
  depuis le dernier recalage vision.

Repère salle : origine = intersection de carreaux.
Convention angles : 0° = -Y, +90° = +X, sens trigonométrique.
"""
import math
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

CAMERA_URL = "https://localhost:5001"
SERVER_URL = "https://localhost:5000"

# ── CARTE DES MARQUEURS (positions x,y en mètres) ──
MARKERS_MAP = {
    0: (-2.07, 0),
    1: (-2.08, 1.07),
    3: (-0.66, 2.45),
    2: (2.17, 1.05),
    4: (2.17, -0.33),
    5: (0.96, -3.39)
}

# Offset IMU : yaw brut quand MARC est face à -Y (= cap 0° dans la convention salle)
YAW_OFFSET = -5.5

# ── État de la fusion odométrie ──
_fused = {
    "x": 0.0,
    "y": 0.0,
    "heading": 0.0,
    "last_distance": None,   # distance cumulée (cm) au dernier recalage vision
    "valid": False,          # True dès qu'au moins un recalage vision a eu lieu
}


# ─────────────────────────────────────────────
#  Récupération des données capteurs
# ─────────────────────────────────────────────
def get_detections():
    """Marqueurs visibles {id: {distance, angle, ...}}."""
    try:
        r = requests.get(f"{CAMERA_URL}/detections", verify=False, timeout=1)
        return r.json()
    except Exception as e:
        print(f"[LOC] Erreur caméra : {e}")
        return {}


def get_odometry():
    """Retourne (distance_cumulee_cm, yaw_brut) depuis le serveur."""
    try:
        r = requests.get(f"{SERVER_URL}/odometry", verify=False, timeout=1)
        data = r.json()
        return data.get("distance"), data.get("yaw")
    except Exception as e:
        print(f"[LOC] Erreur odométrie : {e}")
        return None, None


# ─────────────────────────────────────────────
#  Conversion du cap
# ─────────────────────────────────────────────
def heading_salle(yaw_brut):
    """Convertit le yaw brut IMU en cap dans le repère salle."""
    h = yaw_brut - YAW_OFFSET
    return (h + 180) % 360 - 180


# ─────────────────────────────────────────────
#  Localisation par vision (marqueur + cap)
# ─────────────────────────────────────────────
def localize(yaw_brut=None, detections=None):
    """
    Position (x,y) + cap par vision.
    Peut recevoir yaw_brut et detections déjà récupérés (évite des requêtes
    redondantes) ; sinon les récupère lui-même.
    Retourne {x, y, heading, n_markers, used} ou None.
    """
    if yaw_brut is None:
        _, yaw_brut = get_odometry()
    if yaw_brut is None:
        return None
    heading = heading_salle(yaw_brut)

    if detections is None:
        detections = get_detections()

    positions = []
    used = []
    for mid_str, data in detections.items():
        mid = int(mid_str)
        if mid not in MARKERS_MAP:
            continue
        d = data.get("distance")
        a = data.get("angle")
        if d is None or a is None:
            continue
        mx, my = MARKERS_MAP[mid]
        bearing = heading - a
        rad = math.radians(bearing)
        # convention salle : devant = (sin, -cos)
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


# ─────────────────────────────────────────────
#  Localisation fusionnée (vision + odométrie)
# ─────────────────────────────────────────────
def localize_fused():
    """
    Si marqueur visible : recale (vision). Sinon : intègre l'odométrie.
    Retourne {x, y, heading, source} ou None.
    """
    global _fused

    distance_cum, yaw_brut = get_odometry()
    if yaw_brut is None:
        return None
    heading = heading_salle(yaw_brut)

    # 1. Tentative vision
    detections = get_detections()
    vision = localize(yaw_brut=yaw_brut, detections=detections)

    if vision is not None:
        _fused["x"] = vision["x"]
        _fused["y"] = vision["y"]
        _fused["heading"] = vision["heading"]
        _fused["last_distance"] = distance_cum
        _fused["valid"] = True
        return {
            "x": vision["x"],
            "y": vision["y"],
            "heading": vision["heading"],
            "source": "vision",
        }

    # 2. Odométrie seule
    if not _fused["valid"] or _fused["last_distance"] is None or distance_cum is None:
        return None

    delta_m = (distance_cum - _fused["last_distance"]) / 100.0  # cm → m
    rad = math.radians(heading)
    _fused["x"] += delta_m * math.sin(rad)
    _fused["y"] += delta_m * (-math.cos(rad))
    _fused["heading"] = heading
    _fused["last_distance"] = distance_cum

    return {
        "x": round(_fused["x"], 3),
        "y": round(_fused["y"], 3),
        "heading": round(heading, 1),
        "source": "odometry",
    }


# ─────────────────────────────────────────────
#  Test standalone
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import time
    print("=== Localisation MARC (vision + odométrie) ===")
    print(f"Carte : {MARKERS_MAP}")
    print(f"YAW_OFFSET : {YAW_OFFSET}°\n")
    try:
        while True:
            loc = localize_fused()
            if loc:
                print(f"x={loc['x']}m  y={loc['y']}m  cap={loc['heading']}°  "
                      f"[{loc['source']}]")
            else:
                print("Pas de localisation (jamais vu de marqueur connu)")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nArrêt")
