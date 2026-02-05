import pygame, os

# Charger tous les sprites
sprites = []
for name in sorted(os.listdir("assets/naruto_frames")):
    if name.endswith(".png"):
        sprites.append(pygame.image.load(f"assets/naruto_frames/{name}").convert_alpha())

# Exemple : animation de marche (frames 0 à 5)
walk_animation = sprites[0:6]
naruto = libgame.AnimatedElement(walk_animation, 100, 100, fps=10, loop=True)