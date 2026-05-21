#!/usr/bin/env python3
"""
MARC Navigation go-to-goal — navigue vers un point (x,y) de la salle.
Utilise localization.py (position + cap) et envoie les commandes moteur
au serveur principal (/motor).

Usage :
  python3 navigation_goto.py 1.5 0.8     # va vers le point (1.5, 0.8)
"""
import sys
import time
import math
import requests
import urllib3

from localization import localize  # réutilise le module de localisation

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVER_URL = "https://localhost:5000"

# ── Paramètres de contrôle ──
GOAL_TOLERANCE_M   = 0.25    # distance d'arrêt à la cible
ANGLE_TOLERANCE    = 10      # tolérance d'alignement (degrés)
TURN_SPEED         = 90      # vitesse rotation sur place
FORWARD_SPEED      = 90      # vitesse d'avance
KP_TURN            = 3.0     # gain correction d'angle en avançant
MAX_LOST           = 15      # frames sans localisation avant arrêt


def send_motor(move, turn):
    try:
        requests.post(f"{SERVER_URL}/motor",
                      json={"move": int(move), "turn": int(turn)},
                      verify=False, timeout=1)
    except Exception as e:
        print(f"[NAV] Erreur moteur : {e}")


def stop():
    send_motor(0, 0)


def angle_diff(target, current):
    """Différence d'angle normalisée dans [-180, 180]."""
    d = target - current
    return (d + 180) % 360 - 180


def go_to(goal_x, goal_y):
    """Navigue vers le point (goal_x, goal_y)."""
    print(f"[NAV] Cible : ({goal_x}, {goal_y})")
    lost = 0

    while True:
        loc = localize()

        if loc is None:
            lost += 1
            if lost > MAX_LOST:
                print("[NAV] Localisation perdue, arrêt")
                stop()
                return False
            time.sleep(0.05)
            continue
        lost = 0

        x, y, heading = loc["x"], loc["y"], loc["heading"]

        # Distance et direction vers la cible
        dx = goal_x - x
        dy = goal_y - y
        distance = math.hypot(dx, dy)

        # Arrivé ?
        if distance < GOAL_TOLERANCE_M:
            stop()
            print(f"[NAV] ✓ Arrivé ({distance:.2f}m de la cible)")
            return True

        # Direction vers la cible, dans la convention salle
        # (0°=-Y, +90°=+X) → bearing = atan2(dx, -dy)
        bearing = math.degrees(math.atan2(dx, -dy))

        # Erreur d'angle entre où MARC regarde et où est la cible
        err = angle_diff(bearing, heading)

        print(f"[NAV] pos=({x:.2f},{y:.2f}) cap={heading:.0f}° "
              f"cible_dir={bearing:.0f}° err={err:+.0f}° dist={distance:.2f}m")

        if abs(err) > ANGLE_TOLERANCE:
            # Mal aligné : tourner sur place
            # err positif = cible à gauche (anti-horaire) → turn positif = gauche
            turn = TURN_SPEED if err > 0 else -TURN_SPEED
            send_motor(0, turn)
        else:
            # Aligné : avancer avec correction proportionnelle
            turn = int(KP_TURN * err)
            turn = max(-60, min(60, turn))
            send_motor(FORWARD_SPEED, turn)

        time.sleep(0.1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage : python3 navigation_goto.py <x> <y>")
        sys.exit(1)

    gx, gy = float(sys.argv[1]), float(sys.argv[2])
    try:
        go_to(gx, gy)
    except KeyboardInterrupt:
        print("\n[NAV] Arrêt manuel")
    finally:
        stop()
        print("[NAV] Moteurs arrêtés")
