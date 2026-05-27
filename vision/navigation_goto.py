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

# Évitement obstacles
OBSTACLE_THRESHOLD = 35.0   # cm : obstacle centre → contournement franc
SIDE_THRESHOLD     = 50.0   # cm : obstacle latéral → correction douce
KP_SIDE            = 1.2    # gain de la correction latérale
MAX_SIDE_TURN      = 40     # correction latérale max

def send_motor(move, turn):
    try:
        requests.post(f"{SERVER_URL}/motor",
                      json={"move": int(move), "turn": int(turn)},
                      verify=False, timeout=1)
    except Exception as e:
        print(f"[NAV] Erreur moteur : {e}")


def stop():
    send_motor(0, 0)

def get_obstacles():
    """
    Retourne (centre, gauche, droite) en cm.
    -1 (hors portée) est converti en grande valeur (= voie libre).
    """
    try:
        r = requests.get(f"{SERVER_URL}/obstacles", verify=False, timeout=1)
        d = r.json()
        def clean(v):
            return 999.0 if v is None or v < 0 else v   # -1 → voie libre
        return clean(d.get("centre")), clean(d.get("gauche")), clean(d.get("droite"))
    except Exception:
        return 999.0, 999.0, 999.0   # en cas d'erreur, on suppose voie libre


def angle_diff(target, current):
    """Différence d'angle normalisée dans [-180, 180]."""
    return (target - current + 180) % 360 - 180


def go_to(goal_x, goal_y):
    print(f"[NAV] Cible : ({goal_x}, {goal_y})")
    lost = 0

    while True:
        loc = localize_fused()
        if loc is None:
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
            print(f"[NAV] ✓ Arrivé ({distance:.2f}m)")
            return True

        centre, gauche, droite = get_obstacles()

        # ── 1. Obstacle LATÉRAL : tourner jusqu'à ce que centre soit libre ──
        if gauche < SIDE_THRESHOLD and centre < OBSTACLE_THRESHOLD:
            print(f"[NAV] ⚠️  Obstacle gauche (G={gauche:.0f}) → tourne droite")
            while True:
                send_motor(0, -TURN_SPEED)
                time.sleep(0.1)
                centre, gauche, droite = get_obstacles()
                print(f"[NAV] ... C={centre:.0f} G={gauche:.0f} D={droite:.0f}")
                if centre > OBSTACLE_THRESHOLD:
                    print("[NAV] Centre libre → reprise")
                    break
            continue

        if droite < SIDE_THRESHOLD and centre < OBSTACLE_THRESHOLD:
            print(f"[NAV] ⚠️  Obstacle droite (D={droite:.0f}) → tourne gauche")
            while True:
                send_motor(0, TURN_SPEED)
                time.sleep(0.1)
                centre, gauche, droite = get_obstacles()
                print(f"[NAV] ... C={centre:.0f} G={gauche:.0f} D={droite:.0f}")
                if centre > OBSTACLE_THRESHOLD:
                    print("[NAV] Centre libre → reprise")
                    break
            continue

        # ── 2. Obstacle CENTRE : choisir le côté le plus dégagé,
        #       tourner 90°, avancer un peu, reprendre ──
        if centre < OBSTACLE_THRESHOLD:
            if droite >= gauche:
                direction = -TURN_SPEED   # droite plus dégagée → tourner à droite
                label = "DROITE"
            else:
                direction = TURN_SPEED    # gauche plus dégagée → tourner à gauche
                label = "GAUCHE"

            print(f"[NAV] 🚧 Obstacle centre (C={centre:.0f}) → {label} 90°")

            # Tourner ~90° (0.1s * vitesse calibrée — à ajuster selon ton robot)
            t_90 = 0.0
            target_turn = 90.0
            yaw_start = heading
            while True:
                send_motor(0, direction)
                time.sleep(0.1)
                _, yaw_brut = get_odometry()
                if yaw_brut is None:
                    t_90 += 0.1
                    if t_90 > 3.0:
                        break
                    continue
                current_heading = heading_salle(yaw_brut)
                turned = abs(angle_diff(current_heading, yaw_start))
                if turned >= target_turn:
                    break

            # Avancer un peu
            print("[NAV] Avance dégagement...")
            send_motor(FORWARD_SPEED, 0)
            time.sleep(0.6)
            stop()
            time.sleep(0.1)
            continue

        # ── 3. Navigation normale ──
        bearing = math.degrees(math.atan2(dx, -dy))
        err = angle_diff(bearing, heading)

        # Correction latérale douce (obstacles proches mais pas bloquants)
        side_turn = 0
        if gauche < SIDE_THRESHOLD:
            intensite = (SIDE_THRESHOLD - gauche) / SIDE_THRESHOLD
            side_turn -= int(KP_SIDE * intensite * MAX_SIDE_TURN)
        if droite < SIDE_THRESHOLD:
            intensite = (SIDE_THRESHOLD - droite) / SIDE_THRESHOLD
            side_turn += int(KP_SIDE * intensite * MAX_SIDE_TURN)
        side_turn = max(-MAX_SIDE_TURN, min(MAX_SIDE_TURN, side_turn))

        if abs(err) > ANGLE_TOLERANCE:
            turn = TURN_SPEED if err > 0 else -TURN_SPEED
            turn += side_turn
            turn = max(-TURN_SPEED, min(TURN_SPEED, turn))
            send_motor(0, turn)
        else:
            turn = int(KP_TURN * err) + side_turn
            turn = max(-60, min(60, turn))
            send_motor(FORWARD_SPEED, turn)

        if side_turn != 0:
            print(f"[NAV] pos=({x:.2f},{y:.2f}) cap={heading:.0f}° err={err:+.0f}° "
                  f"dist={distance:.2f}m G={gauche:.0f} D={droite:.0f} side={side_turn:+d} [{src}]")
        else:
            print(f"[NAV] pos=({x:.2f},{y:.2f}) cap={heading:.0f}° err={err:+.0f}° "
                  f"dist={distance:.2f}m [{src}]")

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
