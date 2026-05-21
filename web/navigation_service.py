#!/usr/bin/env python3
"""
MARC Navigation Service — process de navigation ArUco dédié.
Lit les détections du service caméra (port 5001), pilote MARC
via la route /motor du serveur principal (port 5000).

Architecture :
  camera_service.py (5001) --/detections--> [CE PROCESS] --/motor--> server.py (5000)

Usage :
  python3 navigation_service.py          # mode interactif (tape un ID)
  python3 navigation_service.py 2        # va directement vers l'ID 2
"""
import sys
import time
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── CONFIG ──
CAMERA_URL = "https://localhost:5001"   # service caméra (HTTPS)
SERVER_URL = "https://localhost:5000"   # serveur principal (HTTPS)

# Carte des cibles (IDs des marqueurs sur les robots)
# Pour l'instant tu as l'ID 2. Ajoute les autres quand tu les auras.
KNOWN_TARGETS = [0, 1, 2, 3, 4, 5, 6]

# ── Paramètres de contrôle ──
STOP_DISTANCE_M    = 0.75    # distance d'arrêt devant la cible
ANGLE_TOLERANCE    = 6       # alignement acceptable (degrés)
SCAN_TIMEOUT_S     = 40      # temps max de recherche
ANGLE_OFFSET = -5.5          # biais caméra : l'angle réel = angle mesuré - ANGLE_OFFSET

# Vitesses moteur (rappel : avance nécessite move >= 50 côté Arduino)
TURN_SPEED         = 45      # rotation sur place (turn, move=0)
FORWARD_SPEED      = 80      # avance (move, turn=0)
FORWARD_TURN_SPEED = 40      # correction légère en avançant

# turn positif = GAUCHE, négatif = DROITE (d'après setMotors Arduino)
# angle positif = cible à DROITE → il faut tourner à droite → turn négatif


def get_detections():
    """Récupère les marqueurs détectés depuis le service caméra."""
    try:
        r = requests.get(f"{CAMERA_URL}/detections", verify=False, timeout=1)
        return r.json()
    except Exception as e:
        print(f"[NAV] Erreur lecture caméra : {e}")
        return {}


def send_motor(move, turn):
    """Envoie une commande moteur au serveur principal."""
    try:
        requests.post(f"{SERVER_URL}/motor",
                      json={"move": move, "turn": turn},
                      verify=False, timeout=1)
    except Exception as e:
        print(f"[NAV] Erreur envoi moteur : {e}")


def notify_server(event, target):
    """Informe le serveur d'un événement de navigation."""
    try:
        requests.post(f"{SERVER_URL}/navigation",
                      json={"event": event, "target": target},
                      verify=False, timeout=1)
    except Exception:
        pass


def stop():
    send_motor(0, 0)


def scan_for_target(target_id):
    """Tourne sur place jusqu'à voir la cible."""
    print(f"[NAV] Recherche de la cible {target_id}...")
    start = time.time()

    while time.time() - start < SCAN_TIMEOUT_S:
        dets = get_detections()
        if str(target_id) in dets:
            stop()
            print(f"[NAV] Cible {target_id} trouvée")
            return True

        # Tourne à droite par petits pas (turn négatif = droite)
        send_motor(0, -TURN_SPEED)
        time.sleep(0.35)
        stop()
        time.sleep(0.4)   # pause pour stabiliser l'image avant re-scan

    print(f"[NAV] Timeout : cible {target_id} introuvable")
    return False


def approach_target(target_id):
    """Visual servoing proportionnel : avance en corrigeant en continu."""
    print(f"[NAV] Approche de la cible {target_id}")
    lost = 0
    MAX_LOST = 8
    KP_TURN = 4.0   # gain de correction (à ajuster)

    while True:
        dets = get_detections()

        if str(target_id) not in dets:
            lost += 1
            if lost > MAX_LOST:
                print("[NAV] Cible perdue définitivement")
                stop()
                return False
            time.sleep(0.05)
            continue

        lost = 0
        d = dets[str(target_id)]
        distance = d.get("distance")
        angle = d.get("angle")

        if distance is None or angle is None:
            stop()
            return False

        angle = angle - ANGLE_OFFSET
        print(f"[NAV] dist={distance:.2f}m angle={angle:+.1f}°")

        if distance < STOP_DISTANCE_M:
            stop()
            print(f"[NAV] ✓ Arrivé ({distance:.2f}m)")
            return True

        # Correction proportionnelle à l'angle (turn positif = gauche)
        # angle positif = cible à droite → turn négatif
        turn = int(-KP_TURN * angle)
        # Limite la correction
        turn = max(-120, min(120, turn))

        # Si très désaligné, rotation pure ; sinon avance + correction
        if abs(angle) > 5:
            send_motor(0, turn)
        else:
            send_motor(FORWARD_SPEED, turn)

        time.sleep(0.08)


def go_to_target(target_id):
    """Pipeline complet : scan puis approche."""
    if target_id not in KNOWN_TARGETS:
        print(f"[NAV] ID {target_id} inconnu")
        return False

    notify_server("start", target_id)

    if not scan_for_target(target_id):
        notify_server("lost", target_id)
        stop()
        return False

    arrived = approach_target(target_id)
    stop()

    if arrived:
        notify_server("arrived", target_id)
    else:
        notify_server("lost", target_id)
    return arrived


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            target = int(sys.argv[1])
            go_to_target(target)
        else:
            print("=== Navigation ArUco MARC ===")
            print(f"Cibles connues : {KNOWN_TARGETS}")
            while True:
                raw = input("\nID cible (ou 'q' pour quitter) : ").strip()
                if raw.lower() == 'q':
                    break
                try:
                    go_to_target(int(raw))
                except ValueError:
                    print("Entre un nombre valide")
    except KeyboardInterrupt:
        print("\n[NAV] Arrêt")
    finally:
        stop()
        print("[NAV] Moteurs arrêtés")
