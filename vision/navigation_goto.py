#!/usr/bin/env python3
"""
MARC Navigation go-to-goal — navigue vers un point (x,y) de la salle.
Utilise localize_fused() (vision + odométrie) et envoie les commandes
moteur au serveur principal (/motor).

Usage :
  python3 navigation_goto.py 1.5 0.8
"""
import sys
import time
import math
import requests
import urllib3

from localization import localize_fused, get_odometry, heading_salle

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SERVER_URL = "https://localhost:5000"

# ── Paramètres de contrôle ──
GOAL_TOLERANCE_M = 0.25    # distance d'arrêt à la cible
ANGLE_TOLERANCE  = 15      # tolérance d'alignement (degrés)
TURN_SPEED       = 30      # vitesse rotation sur place
FORWARD_SPEED    = 90      # vitesse d'avance
KP_TURN          = 3.0     # gain correction d'angle en avançant
MAX_LOST         = 20      # cycles sans localisation avant arrêt


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
    return (target - current + 180) % 360 - 180


def go_to(goal_x, goal_y):
    """Navigue vers le point (goal_x, goal_y)."""
    print(f"[NAV] Cible : ({goal_x}, {goal_y})")
    lost = 0

    while True:
        loc = localize_fused()

        if loc is None:
            # pas encore localisé : affiche au moins le cap si dispo
            _, yaw = get_odometry()
            cap = f"{heading_salle(yaw):.0f}" if yaw is not None else "?"
            print(f"[NAV] pos=None cap={cap}°")
            lost += 1
            if lost > MAX_LOST:
                print("[NAV] Localisation perdue, arrêt")
                stop()
                return False
            time.sleep(0.05)
            continue
        lost = 0

        x, y, heading = loc["x"], loc["y"], loc["heading"]
        src = loc.get("source", "?")

        dx = goal_x - x
        dy = goal_y - y
        distance = math.hypot(dx, dy)

        if distance < GOAL_TOLERANCE_M:
            stop()
            print(f"[NAV] ✓ Arrivé ({distance:.2f}m de la cible)")
            return True

        # Direction vers la cible (convention salle : 0°=-Y, +90°=+X)
        bearing = math.degrees(math.atan2(dx, -dy))
        err = angle_diff(bearing, heading)

        print(f"[NAV] pos=({x:.2f},{y:.2f}) cap={heading:.0f}° "
              f"dir={bearing:.0f}° err={err:+.0f}° dist={distance:.2f}m [{src}]")

        if abs(err) > ANGLE_TOLERANCE:
            # mal aligné : tourner sur place
            # err positif = cible à gauche (trigo) → turn positif = gauche
            turn = TURN_SPEED if err > 0 else -TURN_SPEED
            send_motor(0, turn)
        else:
            # aligné : avancer avec correction proportionnelle
            turn = max(-60, min(60, int(KP_TURN * err)))
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
