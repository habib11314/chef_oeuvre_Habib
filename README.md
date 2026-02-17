# 🎮 Naruto vs Sasuke - Jeu de Combat 2D

![Python](https://img.shields.io/badge/Python-68.1%25-blue)
![JavaScript](https://img.shields.io/badge/JavaScript-21.2%25-yellow)
![HTML](https://img.shields.io/badge/HTML-7.6%25-orange)

> **Un jeu de combat 2D développé avec Python et Pygame, mettant en scène Naruto et Sasuke dans un affrontement épique.**

---

## 📋 Table des matières

- [Présentation](#-présentation)
- [Caractéristiques](#-caractéristiques)
- [Technologies utilisées](#-technologies-utilisées)
- [Architecture du projet](#-architecture-du-projet)
- [Installation et démarrage](#-installation-et-démarrage)
- [Contrôles du jeu](#-contrôles-du-jeu)
- [Démonstration](#-démonstration)
- [Documentation technique](#-documentation-technique)
- [Auteur](#-auteur)

---

## 🎯 Présentation

**Naruto vs Sasuke** est un jeu de combat 2D développé dans le cadre du **Module Programmation Multimédia**. Ce projet de chef-d'œuvre combine programmation orientée objet, traitement d'images, et développement de jeux vidéo pour créer une expérience de combat dynamique et fluide.

### Contexte pédagogique

- **Module** : Programmation Multimédia
- **Date** : Janvier 2026
- **Étudiant** : Habib
- **Type** : Chef-d'œuvre

---

## ✨ Caractéristiques

### Gameplay

- ⚔️ **Combat 1v1** : Naruto vs Sasuke avec système de santé
- 🎮 **Contrôles fluides** : Déplacement, sauts, attaques légères et lourdes
- 🌀 **Attaques spéciales** : Rasengan et Chidori avec projectiles animés
- 🎨 **Animations** : Machine à états avec sprites animés pour chaque action
- 🏃 **Physique réaliste** : Gravité, vitesse, collisions avec hitboxes

### Technique

- 🖼️ **Traitement d'images** : Extraction automatique de sprites avec OpenCV
- 🎭 **Transparence intelligente** : Suppression du fond bleu tout en préservant les effets visuels
- 🎯 **Système de hitbox** : Détection de collision précise
- 🎬 **Animations fluides** : 60 FPS avec gestion du temps delta
- 🎨 **Interface utilisateur** : Barres de santé, écrans de victoire

---

## 🛠️ Technologies utilisées

### Langages et bibliothèques

| Technologie | Pourcentage | Usage |
|-------------|-------------|-------|
| **Python** | 68.1% | Logique du jeu, gameplay, IA |
| **JavaScript** | 21.2% | Documentation interactive |
| **HTML** | 7.6% | Rapport et documentation |
| **C** | 1.6% | Dépendances natives |
| **CSS** | 0.6% | Styles de documentation |

### Bibliothèques principales

- **Pygame** : Moteur de jeu et rendu graphique
- **OpenCV (cv2)** : Traitement d'images et extraction de sprites
- **NumPy** : Calculs matriciels et manipulation de données

---

## 📁 Architecture du projet

```
chef_oeuvre_Habib/
├── Projet/
│   ├── naruto_vs_sasuke.py          # Fichier principal du jeu
│   ├── extract_sasuke_sprites.py    # Script d'extraction de sprites
│   ├── rapport_naruto.ipynb         # Rapport technique détaillé
│   ├── README.md                    # Ce fichier
│   └── assets/
│       ├── naruto_frames/           # Sprites de Naruto
│       ├── sasuke_frames/           # Sprites de Sasuke
│       └── Training Field.png       # Arrière-plan du terrain
├── Sasuke.png                       # Sprite sheet original
├── .venv/                           # Environnement virtuel Python
└── venv/                            # Environnement virtuel (alternatif)
```

### Structure du code

#### Classes principales

```python
class ChakraOrb:
    """Projectile d'orbe de chakra pour les attaques spéciales"""
    - Gestion des animations de projectiles
    - Détection de collision
    - Effets visuels (Rasengan, Chidori)

class Fighter:
    """Classe représentant un combattant (Naruto ou Sasuke)"""
    - Machine à états (idle, walk, attack, jump, hurt)
    - Système d'animations
    - Gestion des attaques et de la santé
    - Hitbox dynamiques
```

#### Constantes de configuration

```python
WIN_W, WIN_H = 1200, 600           # Dimensions de la fenêtre
FPS = 60                           # Images par seconde
PLAYER_SPEED = 200                 # Vitesse de déplacement
JUMP_FORCE = -400                  # Force du saut
GRAVITY = 1200                     # Gravité
LIGHT_ATTACK_DAMAGE = 5            # Dégâts attaque légère
HEAVY_ATTACK_DAMAGE = 12           # Dégâts attaque lourde
MAX_HEALTH = 100                   # Santé maximale
```

---

## 🚀 Installation et démarrage

### Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Installation rapide

#### 1. Cloner le dépôt

```bash
git clone https://github.com/habib11314/chef_oeuvre_Habib.git
cd chef_oeuvre_Habib
```

#### 2. Créer un environnement virtuel

```bash
python3 -m venv .venv
```

#### 3. Activer l'environnement virtuel

**Linux/macOS :**
```bash
source .venv/bin/activate
```

**Windows :**
```bash
.venv\Scripts\activate
```

#### 4. Installer les dépendances

```bash
pip install pygame opencv-python numpy
```

#### 5. Lancer le jeu

```bash
cd Projet/
python naruto_vs_sasuke.py
```

### Désactivation de l'environnement

```bash
deactivate
```

---

## 🎮 Contrôles du jeu

### Joueur 1 (Naruto)

| Touche | Action |
|--------|--------|
| **Q/D** | Déplacement gauche/droite |
| **Z** | Saut |
| **F** | Attaque légère |
| **G** | Attaque lourde |
| **H** | Attaque spéciale (Rasengan) |

### Joueur 2 (Sasuke) - À implémenter selon le mode de jeu

| Touche | Action |
|--------|--------|
| **←/→** | Déplacement gauche/droite |
| **↑** | Saut |
| **K** | Attaque légère |
| **L** | Attaque lourde |
| **M** | Attaque spéciale (Chidori) |

---

## 🎬 Démonstration

### Captures d'écran

> *Ajoutez ici des captures d'écran du jeu en action*

### Fonctionnalités clés

#### 1. Extraction de sprites avec OpenCV

Le projet utilise OpenCV pour extraire automatiquement les sprites des sprite sheets :

```python
def remove_blue_background_cv(image_path):
    """Retire le fond bleu des sprites avec OpenCV"""
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Détection du fond bleu (Hue > 100) tout en préservant 
    # les effets cyan du Rasengan (Hue < 100)
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(img_hsv, lower_blue, upper_blue)
    
    # Création d'un canal alpha pour la transparence
    alpha_channel = np.ones(img_rgb.shape[:2], dtype=np.uint8) * 255
    alpha_channel[mask_blue > 0] = 0
    img_rgba = np.dstack((img_rgb, alpha_channel))
    
    return pygame.image.frombuffer(img_rgba.tobytes(), 
                                   img_rgba.shape[1::-1], "RGBA")
```

**Innovation technique** : Le système détecte et retire le fond bleu (Hue 105-110) tout en préservant les effets visuels cyan du Rasengan (Hue < 100).

#### 2. Machine à états pour les animations

```
IDLE → WALK → ATTACK → JUMP → HURT → DEATH
  ↓      ↓       ↓       ↓       ↓
  └──────┴───────┴───────┴───────┘
```

#### 3. Système de projectiles animés

Les attaques spéciales (Rasengan, Chidori) sont des projectiles animés avec :
- Sprites animés en boucle
- Collision detection
- Effets visuels (particules, rotation)
- Dégâts au contact (20 HP)

---

## 📚 Documentation technique

### Rapport complet

Le rapport détaillé du projet est disponible dans le fichier **`rapport_naruto.ipynb`** (Jupyter Notebook).

#### Contenu du rapport

1. **Introduction**
   - Contexte historique des jeux de combat 2D
   - Motivations et objectifs du projet

2. **Architecture logicielle**
   - Environnement de développement
   - Gestion des données avec NumPy
   - Gestion des entrées/sorties

3. **Gestion des assets multimédias**
   - Récupération des sprites
   - Traitement avec OpenCV
   - Transparence et masquage

4. **Programmation orientée objet**
   - Classes principales
   - Machine à états
   - Système de hitbox

5. **Gameplay et physique**
   - Mouvements et collisions
   - Système de combat
   - Effets spéciaux

### Consulter le rapport

**Avec Jupyter Notebook :**
```bash
pip install jupyter
jupyter notebook Projet/rapport_naruto.ipynb
```

**Avec VS Code :**
- Installer l'extension "Jupyter"
- Ouvrir le fichier `.ipynb`

---

## 🔧 Personnalisation et développement

### Ajouter de nouveaux personnages

1. Extraire les sprites avec `extract_sasuke_sprites.py`
2. Créer un dossier dans `assets/`
3. Définir les animations dans le code
4. Ajuster les paramètres de combat

### Modifier les paramètres de jeu

Les constantes de configuration sont définies en haut du fichier `naruto_vs_sasuke.py` :

```python
# Paramètres de combat
PLAYER_SPEED = 200        # Augmenter pour un jeu plus rapide
JUMP_FORCE = -400         # Augmenter pour des sauts plus hauts
LIGHT_ATTACK_DAMAGE = 5   # Ajuster l'équilibrage
HEAVY_ATTACK_DAMAGE = 12
```

---

## 🤝 Contributions

Ce projet est un chef-d'œuvre pédagogique. Les suggestions d'amélioration sont les bienvenues :

- Ajout de nouveaux personnages
- Système de combos
- Mode multijoueur en ligne
- Niveaux et modes de jeu supplémentaires
- Effets sonores et musique

---

## 📄 Licence

Ce projet est développé dans un cadre pédagogique. Les sprites Naruto et Sasuke sont la propriété de leurs créateurs respectifs.

---

## 👤 Auteur

**Habib**  
📧 Contact : [habib11314](https://github.com/habib11314)  
🎓 Module : Programmation Multimédia  
📅 Date : Janvier 2026

---

## 🙏 Remerciements

- **Masashi Kishimoto** pour l'univers Naruto
- **Pygame Community** pour la bibliothèque de développement
- **OpenCV Team** pour les outils de traitement d'images
- Mes enseignants pour leur accompagnement

---

## 📈 Statistiques du projet

- **Lignes de code** : ~2000+ lignes
- **Sprites extraits** : 100+ frames d'animation
- **Temps de développement** : Janvier 2026
- **Langages** : Python (68.1%), JavaScript (21.2%), HTML (7.6%)

---

<div align="center">

**⭐ Si ce projet vous plaît, n'hésitez pas à lui donner une étoile !**

[🎮 Jouer maintenant](#-installation-et-démarrage) | [📖 Documentation](#-documentation-technique) | [🐛 Signaler un bug](https://github.com/habib11314/chef_oeuvre_Habib/issues)

</div>
