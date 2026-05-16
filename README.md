<div align="center">

<img src="docs/images/marc-hero.jpg" alt="MARC - Robot guide autonome" width="700"/>

# 🤖 MARC

### *Mascareignes Assistant and Robot Compagnon*

**Robot mobile autonome, guide vocal du laboratoire de robotique de l'Université des Mascareignes.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-4-C51A4A?logo=raspberrypi&logoColor=white)](https://www.raspberrypi.org/)
[![Arduino](https://img.shields.io/badge/Arduino-Mega%202560-00979D?logo=arduino&logoColor=white)](https://www.arduino.cc/)
[![Flask](https://img.shields.io/badge/Flask-HTTPS-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Ollama](https://img.shields.io/badge/LLM-Mistral%20via%20Ollama-7B68EE)](https://ollama.com/)

[**🎥 Voir la démo**](#-démonstration) · [**🚀 Installation**](#-installation) · [**📖 Documentation**](#-documentation)

</div>

---

## 📺 Démonstration

> 🎬 **[▶️ Cliquez ici pour voir MARC en action sur YouTube](https://youtu.be/REMPLACER_PAR_LIEN_YOUTUBE)**

[![MARC Demo](https://img.youtube.com/vi/REMPLACER_PAR_LIEN_YOUTUBE/maxresdefault.jpg)](https://youtu.be/REMPLACER_PAR_LIEN_YOUTUBE)

*MARC navigue entre les stations du laboratoire, présente les robots et interagit vocalement.*

---

## 📋 Sommaire

- [À propos](#-à-propos)
- [Aperçu](#-aperçu)
- [Architecture](#%EF%B8%8F-architecture)
- [Matériel](#-matériel)
- [Structure du dépôt](#-structure-du-dépôt)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Architecture logicielle](#-architecture-logicielle)
- [Documentation](#-documentation)
- [Auteur](#-auteur)

---

## 🎯 À propos

MARC est un **projet de fin d'études** développé en 3ème année d'Informatique Appliquée à l'**Université des Mascareignes** (Maurice), en partenariat avec l'**Université de Limoges**.

L'objectif : créer un robot guide capable de **se déplacer de manière autonome** entre 7 stations du laboratoire de robotique, de **dialoguer en langage naturel** grâce à un Grand Modèle de Langage, et d'**exprimer des émotions** via une matrice LED. Le tout supervisé depuis une interface web temps réel.

Le robot est entièrement conçu à partir de zéro : **modélisation 3D sur Onshape**, **impression 3D**, **électronique custom**, **firmware embarqué** et **stack logiciel complet**.

---

## ✨ Aperçu

- 🧭 **Navigation autonome** par suivi de ligne (3 capteurs IR) entre 7 stations
- 🎙️ **Pipeline vocal complet** : Speech-to-Text → LLM cloud (Mistral via Ollama) → Text-to-Speech
- 🧠 **Sortie JSON structurée** : le LLM génère directement des commandes exécutables
- 🌐 **Interface web HTTPS temps réel** : parcours SVG, journal d'événements, Push-To-Talk, mises à jour SSE
- 👀 **Matrice LED RGB 64×32** avec 6 expressions GIF (neutre, clignement, suspicieux, disparition, larme, amour)
- ⚖️ **Tentative auto-équilibrante PID** documentée et analysée *(mode finalement abandonné pour la navigation, voir le rapport)*

<div align="center">
<img src="docs/images/marc-led-matrix.jpg" alt="Matrice LED RGB de MARC" width="500"/>
<br/>
<i>La matrice LED RGB 64×32 pendant les tests d'animation</i>
</div>

---

## 🏗️ Architecture

Le système est distribué en trois couches :

```
┌─────────────────────────────────────────────┐
│  Couche matérielle                          │
│  Arduino Mega 2560 — 16 MHz, PID 100 Hz     │
│  Moteurs NEMA 23 · TB6600 · IR · BNO085     │
└──────────────────┬──────────────────────────┘
                   │ UART 115 200 bauds
                   │ (/dev/ttyACM0)
┌──────────────────┴──────────────────────────┐
│  Couche applicative                         │
│  Raspberry Pi 4 Model B — 1 Go RAM          │
│  Flask HTTPS + SSE · pipeline vocal · LED   │
└──────────────────┬──────────────────────────┘
                   │ HTTPS — API Ollama
┌──────────────────┴──────────────────────────┐
│  Intelligence distante                      │
│  Mistral Large via Ollama Cloud             │
│  Sortie JSON structurée                     │
└─────────────────────────────────────────────┘
```

---

## 🔧 Matériel

<div align="center">
<img src="docs/images/marc-hardware.jpg" alt="Plateforme matérielle de MARC" width="600"/>
<br/>
<i>Vue rapprochée du châssis : moteurs NEMA 23, drivers TB6600 et électronique de commande</i>
</div>

| Composant | Référence |
| --- | --- |
| Microcontrôleur | Arduino Mega 2560 |
| Ordinateur de bord | Raspberry Pi 4 Model B (1 Go RAM) |
| Moteurs | Pas-à-pas NEMA 23 ×2 |
| Drivers moteurs | TB6600 ×2 |
| Centrale inertielle | BNO085 (SPI, CS pin 47) |
| Capteurs ligne | 3 capteurs IR — pins 49 (G), 40 (C), 48 (D) |
| Affichage | Matrice LED RGB 64×32 (HUB75) |
| Télécommande | Récepteur IR (pin 46) — réglage PID, manuel |

> 💡 La modélisation 3D complète a été réalisée sur **Onshape** et le robot a été imprimé en 3D au laboratoire de l'UDM.


---

## 🧱 Conception 3D

L'intégralité de la mécanique de MARC a été **modélisée sur Onshape** puis **imprimée en 3D** au laboratoire de l'UDM. Le robot se décompose en **3 sous-ensembles** : la coque externe esthétique, la structure interne porteuse, et la tête (matrice LED).

<div align="center">
<img src="docs/images/marc-onshape-render.png" alt="Modélisation Onshape de MARC" width="600"/>
<br/>
<i>Modèle 3D complet de MARC sur Onshape</i>
</div>

### 🔗 Visualisation interactive

👉 **[Voir le modèle 3D complet sur Onshape](https://cad.onshape.com/documents/bc8d4e2fc1fa99c54b0ae445/w/f22cc56c4e97ab29b572a8dc/e/e2a230c46f8ff9770799be93?renderMode=0&uiState=6a0843f44ea664229f8211eb)**

### 📦 Fichiers 3D disponibles

Tous les fichiers source sont dans [`hardware/3d-models/`](assets/3d-models/), au format **STL** (impression directe) et **STEP** (édition CAO).

> 💡 Astuce : cliquez sur n'importe quel fichier `.stl` directement sur GitHub pour le **visualiser en 3D** dans votre navigateur.

#### 🏛️ Coque externe

Habillage esthétique du robot, imprimé en plusieurs morceaux pour respecter les contraintes du plateau d'impression.

| Pièce | STL | STEP |
|-------|-----|------|
| Colonne V3 | [STL](assets/3d-models/ColonneV3.stl) | [STEP](assets/3d-models/ColonneV3.step) |
| Corps Bas — Avant | [STL](assets/3d-models/CorpsBasAvant.stl) | [STEP](assets/3d-models/CorpsBasAvant.step) |
| Corps Bas — Arrière | [STL](assets/3d-models/CorpsBasArriere.stl) | [STEP](assets/3d-models/CorpsBasArriere.step) |
| Corps Haut — Avant | [STL](assets/3d-models/CorpsHautAvant.stl) | [STEP](assets/3d-models/CorpsHautAvant.step) |
| Corps Haut — Arrière | [STL](assets/3d-models/CorpsHautArriere.stl) | [STEP](assets/3d-models/CorpsHautArriere.step) |
| Étage 0 (base) | [STL](assets/3d-models/Etage0.stl) | [STEP](assets/3d-models/Etage0.step) |
| Porte d'accès | [STL](assets/3d-models/Porte.stl) | [STEP](assets/3d-models/Porte.step) |
| Support capteurs IR | [STL](assets/3d-models/SupportTrackingSensor.stl) | [STEP](assets/3d-models/SupportTrackingSensor.step) |

#### 🦴 Structure interne

Squelette porteur qui supporte l'électronique, les moteurs et les batteries.

| Pièce | STL | STEP |
|-------|-----|------|
| Colonne V1 | [STL](assets/3d-models/ColonneV1.stl) | [STEP](assets/3d-models/ColonneV1.step) |
| Coque interne | [STL](assets/3d-models/Coque.stl) | [STEP](assets/3d-models/Coque.step) |
| Étage 1 | [STL](assets/3d-models/Etage1.stl) | [STEP](assets/3d-models/Etage1.step) |
| Étage 2 | [STL](assets/3d-models/Etage2.stl) | [STEP](assets/3d-models/Etage2.step) |
| Étage 3 | [STL](assets/3d-models/Etage3.stl) | [STEP](assets/3d-models/Etage3.step) |
| Bague de réduction | [STL](assets/3d-models/BagueDeReduction.stl) | [STEP](assets/3d-models/BagueDeReduction.step) |
| Roue | [STL](assets/3d-models/Roue.stl) | [STEP](assets/3d-models/Roue.step) |
| Part 8 | [STL](assets/3d-models/Part8.stl) | [STEP](assets/3d-models/Part8.step) |

#### 🤖 Tête

Module supérieur portant la matrice LED 64×32 (le « visage » de MARC).

| Pièce | STL | STEP |
|-------|-----|------|
| Tête — partie basse | [STL](assets/3d-models/TeteBas.stl) | [STEP](assets/3d-models/TeteBas.step) |
| Tête — partie haute | [STL](assets/3d-models/Tete-Haut.stl) | [STEP](assets/3d-models/TeteHaut.step) |
| Cadre matrice LED | [STL](assets/3d-models/tete/Matrice-Led.stl) | [STEP](assets/3d-models/MatriceLed.step) |



---



## 📁 Structure du dépôt

```
.
├── ControlMoteur/                 # Code embarqué Arduino Mega
│   ├── ControlMoteur.ino          # Boucle principale : PID, suivi de ligne, série
│   ├── header.h                   # Définitions broches, constantes, objets PID
│   └── fonctions.ino              # Fonctions auxiliaires (setMotors, lineTracking…)
│
├── Local-Voice/                   # Pipeline vocal Python (fork m15-ai/Local-Voice)
│   ├── voiceAssistant.py          # STT (Google) → LLM (Ollama cloud) → TTS (Edge)
│   ├── modelfile.txt              # Prompt système + base de connaissances
│   ├── requirements.txt
│   └── piper/                     # (optionnel) binaire Piper + voix offline
│
├── matrixLed/                     # Pilotage de la matrice LED RGB 64×32
│   ├── eye_manager.py             # Gestion thread-safe des animations + clignement
│   ├── gif_viewer.py              # Lecteur GIF simple (test standalone)
│   ├── SplitEyes.py               # Génération des GIFs depuis une vidéo source
│   ├── style1/                    # Set d'expressions style 1 (6 GIF)
│   └── style2/                    # Set d'expressions style 2 (6 GIF)
│
├── web/                           # Serveur Flask + interface web
│   ├── server.py                  # Flask HTTPS + SSE + worker série
│   ├── index.html                 # Application monopage HTML/CSS/JS
│   ├── style.css                  # Styles (parcours SVG, journal, Push-To-Talk)
│   ├── cert.pem / key.pem         # Certificat SSL auto-signé (à générer)
│   └── ...
│
├── docs/
│   ├── images/                    # Photos et captures du projet
│   └── Rapport_PFE_MARC.pdf       # Rapport complet du projet
│
└── .gitignore
```

---

## 🚀 Installation

### Prérequis

- Raspberry Pi 4 (Raspberry Pi OS 64 bits recommandé)
- Arduino Mega 2560 + IDE Arduino
- Python 3.9 ou supérieur
- Compte [Ollama](https://ollama.com) avec accès à l'API cloud (clé API)
- Réseau Wi-Fi local
- `ffmpeg`, `mpg123`, `sox`, `alsa-utils` installés sur le Pi

### Côté Arduino

1. Ouvrir `ControlMoteur/ControlMoteur.ino` dans l'IDE Arduino.
2. Installer via le gestionnaire de bibliothèques :
   - [`FastAccelStepper`](https://github.com/gin66/FastAccelStepper)
   - [`IRremote`](https://github.com/Arduino-IRremote/Arduino-IRremote)
   - [`SparkFun BNO08x Arduino Library`](https://github.com/sparkfun/SparkFun_BNO08x_Arduino_Library)
   - `PID_v1` (Brett Beauregard)
3. Vérifier les broches dans `header.h` (STEP/DIR/ENABLE moteurs, capteurs IR, BNO085, télécommande IR).
4. Compiler et téléverser sur l'Arduino Mega.

### Côté Raspberry Pi

```bash
# Cloner le dépôt
git clone https://github.com/SALLAH-JP/MARC.git
cd MARC

# Environnement Python
python3 -m venv env
source env/bin/activate
pip install -r Local-Voice/requirements.txt
pip install flask pyserial speechrecognition edge-tts pydub pillow

# Bibliothèque matrice LED (compilation native, requiert sudo plus tard)
git clone https://github.com/hzeller/rpi-rgb-led-matrix
cd rpi-rgb-led-matrix && make build-python PYTHON=$(which python3) && cd ..

# Dépendances système
sudo apt install ffmpeg mpg123 sox alsa-utils portaudio19-dev

# Certificat SSL auto-signé (HTTPS obligatoire pour le micro côté navigateur)
cd web
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
cd ..

# Variables d'environnement Ollama
export OLLAMA_API_KEY="<votre_clé>"
export OLLAMA_HOST="https://ollama.com"
```

### Lancement

```bash
# Terminal 1 — serveur web (HTTPS, port 5000) + matrice LED
cd web
sudo -E python3 server.py

# Terminal 2 — assistant vocal (wake word + commande)
cd Local-Voice
python3 voiceAssistant.py
```

L'interface web est accessible sur `https://<ip-du-pi>:5000` depuis n'importe quel appareil du réseau local. Le navigateur affichera un avertissement de sécurité dû au certificat auto-signé — c'est normal sur un réseau local, accepter l'exception.

> ⚠️ **Note** : `sudo` est nécessaire pour `server.py` car la bibliothèque `rpi-rgb-led-matrix` requiert un accès direct aux GPIO. Le drapeau `-E` préserve les variables d'environnement.

---

## 🎮 Utilisation

### Commande vocale

1. Dire le mot de réveil : *« Salut Marc »*.
2. Énoncer la commande, par exemple :
   - *« Va voir Pepper »* → navigation autonome jusqu'à la station Pepper
   - *« Présente-moi NAO »* → MARC s'y rend et donne une présentation
   - *« Reviens à la base »* → retour station 0
   - *« Change tes yeux »* → bascule entre style 1 et 2
3. MARC interprète la requête, confirme oralement et exécute.

### Interface web

- Cliquer sur une station du parcours SVG pour y envoyer le robot
- Activer ou désactiver le mode guide
- Push-To-Talk pour enregistrer une commande vocale depuis le navigateur
- Suivre le journal des événements en temps réel (SSE — pas de rechargement)

### Stations disponibles

| ID web | Numéro physique | Équipement |
| --- | --- | --- |
| base | 0 | Point de départ |
| nao | 1 | Robot humanoïde NAO |
| vector | 2 | Robot mobile Vector |
| pepper | 3 | Robot humanoïde Pepper |
| imp3d | 4 | Imprimante 3D Zortrax |
| baxter | 5 | Robot industriel Baxter |
| bras | 6 | Bras Franka Panda |

---

## 🧩 Architecture logicielle

**`ControlMoteur/`** — boucle Arduino à 200–500 Hz qui lit l'IMU, interprète les trames série venant du Pi (`C:move:turn` et `M:0/1`), exécute soit le suivi de ligne soit la télécommande IR, calcule les deux PID (équilibre + vitesse) et envoie les pas aux moteurs via FastAccelStepper. Quand une nouvelle station est détectée, l'Arduino renvoie `S:N` au Pi.

**`web/server.py`** — serveur Flask HTTPS qui héberge l'interface, expose les routes `/command`, `/vocal_command`, `/transcribe`, `/status`, `/line_following`, et un flux SSE `/events` pour les mises à jour temps réel vers le navigateur. Un thread daemon tourne en parallèle pour la communication série.

**`Local-Voice/voiceAssistant.py`** — pipeline vocal indépendant : écoute permanente du wake word via SpeechRecognition (Google STT), interprétation par Mistral Large via l'API Ollama cloud avec sortie JSON contrainte, synthèse vocale française avec `edge-tts` (voix `fr-FR-HenriNeural`), envoi de la commande au serveur Flask via HTTPS POST.

**`matrixLed/eye_manager.py`** — gestionnaire thread-safe de la matrice LED, clignement aléatoire en arrière-plan (3 à 7 secondes), interruption immédiate pour jouer une animation à la demande, rechargement à chaud lors d'un changement de style.

---

## 📖 Documentation

Le rapport complet de Projet de Fin d'Études détaille :
- l'analyse des besoins
- les choix d'architecture
- l'analyse du conflit PID-équilibre vs suivi de ligne
- les tests d'une vingtaine de modèles LLM réalisés sur Raspberry Pi 4
- la modélisation 3D sur Onshape
- les résultats expérimentaux

📄 Disponible dans [`docs/Rapport_PFE_MARC.pdf`](docs/Rapport_PFE_MARC.pdf).

---

## 👤 Auteur

**SALLAH Assiongbon Théodore Jean-Paul**
Étudiant en 3ème année — Informatique Appliquée
🎓 Université des Mascareignes · Université de Limoges
📅 Année universitaire 2024 / 2025

**Encadrant pédagogique :** M. Khadimoullah Ramoth

[![GitHub](https://img.shields.io/badge/GitHub-SALLAH--JP-181717?logo=github)](https://github.com/SALLAH-JP)

---

## 🙏 Remerciements

Ce projet doit beaucoup à plusieurs contributions extérieures :

- Le projet [Local-Voice](https://github.com/m15-ai/Local-Voice) de M15.ai, dont l'architecture a inspiré le pipeline vocal
- La plateforme [Ollama](https://ollama.com) et le modèle Mistral Large
- La bibliothèque [FastAccelStepper](https://github.com/gin66/FastAccelStepper) de J. Kerschbaumer
- La bibliothèque [rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix) de H. Zeller
- [edge-tts](https://github.com/rany2/edge-tts), [Flask](https://flask.palletsprojects.com), [SpeechRecognition](https://github.com/Uberi/speech_recognition)
- Les fournisseurs locaux Advanced Electronique et Transcom (Maurice)

---

## 📜 Licence

Ce projet est distribué sous licence **MIT** — voir le fichier [`LICENSE`](LICENSE).

Le code des bibliothèques tierces utilisées reste sous leurs licences respectives.

---

<div align="center">

*Si ce projet vous a plu, n'hésitez pas à laisser une ⭐ !*

</div>