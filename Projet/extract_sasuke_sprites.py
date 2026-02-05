import cv2
import numpy as np
import os

# Charger l'image
image_path = "../Sasuke.png"
if not os.path.exists(image_path):
    print(f"Erreur : fichier {image_path} introuvable")
    exit(1)

print(f"Fichier trouvé : {image_path}")
img = cv2.imread(image_path)
if img is None:
    print("Erreur : impossible de charger l'image")
    exit(1)

print(f"Image chargée : {img.shape}")
height, width = img.shape[:2]

# Convertir en HSV pour détecter le fond bleu
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Masque pour le fond bleu (même logique que pour Naruto)
lower_blue = np.array([90, 50, 50])
upper_blue = np.array([130, 255, 255])
blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

# Inverser le masque pour avoir les sprites
sprite_mask = cv2.bitwise_not(blue_mask)

# Trouver les contours des sprites
contours, _ = cv2.findContours(sprite_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# Filtrer et trier les contours
valid_contours = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    area = w * h
    # Filtrer les petits artefacts et les zones trop grandes
    if area > 500 and area < 50000 and w > 10 and h > 10:
        valid_contours.append((x, y, w, h, cnt))

# Trier de haut en bas, puis de gauche à droite
valid_contours.sort(key=lambda c: (c[1] // 100, c[0]))

print(f"{len(valid_contours)} sprites détectés")

# Créer le dossier de sortie
output_dir = "assets/sasuke_frames"
os.makedirs(output_dir, exist_ok=True)

sprite_count = 0

for x, y, w, h, cnt in valid_contours:
    # Ajouter un padding
    padding = 5
    x1 = max(0, x - padding)
    y1 = max(0, y - padding)
    x2 = min(width, x + w + padding)
    y2 = min(height, y + h + padding)
    
    # Extraire le sprite
    sprite = img[y1:y2, x1:x2]
    
    # Sauvegarder
    output_path = os.path.join(output_dir, f"sasuke_{sprite_count:03d}.png")
    cv2.imwrite(output_path, sprite)
    print(f"Sprite {sprite_count} : {sprite.shape[1]}x{sprite.shape[0]} à position ({x},{y})")
    sprite_count += 1

print(f"\n{sprite_count} sprites extraits dans {output_dir}")
