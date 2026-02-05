import os
import pygame
import sys
import cv2
import numpy as np

# Configuration
WIN_W, WIN_H = 1200, 600
FPS = 60
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "naruto_frames")
BACKGROUND_IMAGE = os.path.join(ASSETS_DIR, "Training Field.png")

# Paramètres de combat
PLAYER_SPEED = 200
ENEMY_SPEED = 150
JUMP_FORCE = -400
GRAVITY = 1200
GROUND_Y = 350  # Sol visible du terrain

# Limites du terrain (zone sans bleu, basé sur analyse CV)
TERRAIN_LEFT = 60
TERRAIN_RIGHT = 1140
TERRAIN_TOP = 230  # Début du terrain non-bleu
TERRAIN_BOTTOM = 490  # Avant la zone bleue du bas

# Dégâts
LIGHT_ATTACK_DAMAGE = 5
HEAVY_ATTACK_DAMAGE = 12
MAX_HEALTH = 100


def remove_blue_background_cv(image_path):
    """Retire le fond bleu des sprites avec OpenCV"""
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Détecter le bleu (ajusté pour ne pas effacer le Rasengan qui est cyan/bleu: Hue ~96)
    # Le fond est bleu pur (Hue ~105-110), le Rasengan est plus cyan (Hue < 100)
    # On commence la détection à Hue=100 pour garder le Rasengan visible
    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([130, 255, 255])
    mask_blue = cv2.inRange(img_hsv, lower_blue, upper_blue)
    
    # Créer canal alpha
    alpha_channel = np.ones(img_rgb.shape[:2], dtype=np.uint8) * 255
    alpha_channel[mask_blue > 0] = 0
    img_rgba = np.dstack((img_rgb, alpha_channel))
    
    return pygame.image.frombuffer(img_rgba.tobytes(), img_rgba.shape[1::-1], "RGBA")


class ChakraOrb:
    """Projectile d'orbe de chakra pour l'attaque spéciale"""
    def __init__(self, x, y, direction, owner, sprites):
        self.x = x
        self.y = y
        self.vx = 600 * direction
        self.direction = direction
        self.owner = owner
        self.sprites = sprites
        self.frame_idx = 0
        self.anim_timer = 0
        self.anim_fps = 12
        self.active = True
        self.has_hit = False
        self.damage = 20
        
    def update(self, dt):
        if not self.active:
            return
        self.x += self.vx * dt
        self.anim_timer += dt
        if self.anim_timer >= 1.0 / self.anim_fps:
            self.anim_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(self.sprites)
        if self.x < -100 or self.x > WIN_W + 100:
            self.active = False
    
    def draw(self, screen):
        if not self.active:
            return
        sprite = self.sprites[self.frame_idx]
        if self.direction < 0:
            sprite = pygame.transform.flip(sprite, True, False)
        screen.blit(sprite, (int(self.x), int(self.y)))
    
    def get_hitbox(self):
        if not self.active:
            return None
        sprite = self.sprites[self.frame_idx]
        w, h = sprite.get_size()
        return pygame.Rect(int(self.x), int(self.y), w, h)


def load_sprite(sprite_idx):
    """Charge un sprite par son numéro"""
    filename = f"sprite_{sprite_idx:03d}.png"
    path = os.path.join(ASSETS_DIR, filename)
    if os.path.exists(path):
        return remove_blue_background_cv(path)
    raise RuntimeError(f"Sprite {filename} non trouvé")


def load_sprites(sprite_indices):
    """Charge plusieurs sprites"""
    return [load_sprite(idx) for idx in sprite_indices]


def load_sprite_sasuke(sprite_idx):
    """Charge un sprite de Sasuke par son numéro"""
    filename = f"sasuke_{sprite_idx:03d}.png"
    sasuke_dir = os.path.join(os.path.dirname(__file__), "assets", "sasuke_frames")
    path = os.path.join(sasuke_dir, filename)
    if os.path.exists(path):
        return remove_blue_background_cv(path)
    # Fallback sur les sprites Naruto si non trouvé
    return load_sprite(sprite_idx)


def load_sprites_sasuke(sprite_indices):
    """Charge plusieurs sprites de Sasuke"""
    return [load_sprite_sasuke(idx) for idx in sprite_indices]


class Fighter:
    """Classe de base pour les combattants (Naruto et Sasuke)"""
    def __init__(self, x, y, name, sprites_dict, facing_right=True):
        self.x = x
        self.y = y
        self.name = name
        self.sprites = sprites_dict
        self.facing_right = facing_right
        
        # État
        self.state = "idle"
        self.frame_idx = 0
        self.anim_timer = 0
        self.anim_fps = 10
        
        # Mouvement
        self.vx = 0
        self.vy = 0
        self.on_ground = True
        
        # Combat
        self.health = MAX_HEALTH
        self.is_attacking = False
        self.attack_cooldown = 0
        self.attack_damage = 0  # Dégâts de l'attaque en cours
        self.attack_type = "light"  # Type d'attaque: light, heavy, teleport, combo
        self.attack_hit = False  # Pour éviter de toucher plusieurs fois avec une seule attaque
        self.is_hit = False
        self.hit_timer = 0
        self.invincible = False  # Invincibilité temporaire
        self.invincible_timer = 0
        self.knockback_vx = 0  # Vitesse de recul
        
        # Bouclier
        self.is_blocking = False
        self.block_stamina = 100  # Stamina du bouclier
        self.block_stamina_max = 100
        self.block_regen_rate = 30  # Régénération par seconde
        self.block_drain_rate = 40  # Drain par seconde quand on bloque
        
        # Chakra
        self.chakra = 100  # Chakra pour attaques spéciales
        self.chakra_max = 100
        self.chakra_regen_rate = 15  # Régénération par seconde
        self.orb_sprites = []
        self.should_spawn_orb = False
        
        # Mode Kyubi (Barre rouge)
        self.kyubi_energy = 0
        self.kyubi_max = 100
        self.kyubi_beam_sprites = [] # Sprites du rayon
        self.is_firing_beam = False # En train de tirer le rayon
        self.beam_timer = 0
        self.beam_duration = 1.0 # Durée du rayon réduite (était 2.0)
        
        # Téléportation
        self.teleporting = False
        self.teleport_phase = 0  # 0: disparition, 1: invisible, 2: réapparition en l'air, 3: atterrissage
        self.teleport_timer = 0
        self.teleport_target_x = 0
        
        # Attaque sous-sol
        self.underground_attack = False
        self.underground_phase = 0  # 0: intro (104-105), 1: fumée (116), 2: surgissement (106-108)
        self.underground_timer = 0
        self.underground_sprites = []
        self.ground_crack_sprites = []  # Sprites du sol qui se casse (122-124)
        self.underground_target_x = 0
        
    def get_current_frames(self):
        """Retourne les frames de l'état actuel"""
        return self.sprites.get(self.state, self.sprites["idle"])
    
    def update(self, dt, keys=None, target=None):
        """Met à jour le combattant"""
        # Gestion spéciale de l'attaque sous-sol
        if self.underground_attack:
            self.underground_timer += dt
            
            # Phase 0: Intro - frappe le sol (sprites 104-105) - 0.4s
            if self.underground_phase == 0:
                if self.underground_timer < 0.2:
                    self.frame_idx = 0  # Sprite 104
                elif self.underground_timer < 0.4:
                    self.frame_idx = 1  # Sprite 105
                else:
                    self.underground_phase = 1
                    self.underground_timer = 0
                    # Calculer la position cible (derrière l'ennemi)
                    if target:
                        if self.facing_right:
                            self.underground_target_x = target.x + 80
                        else:
                            self.underground_target_x = target.x - 80
                    else:
                        self.underground_target_x = self.x + (200 if self.facing_right else -200)
            
            # Phase 1: Fumée (sprite 116) - 0.4s
            elif self.underground_phase == 1:
                self.frame_idx = 0  # Sprite 116 - fumée qui remplace Naruto
                if self.underground_timer >= 0.4:
                    self.underground_phase = 2
                    self.underground_timer = 0
                    # Téléporter sous terre vers la cible
                    self.x = self.underground_target_x
            
            # Phase 2: Surgissement du sol (sprites 106-108) - 0.6s
            elif self.underground_phase == 2:
                if self.underground_timer < 0.2:
                    self.frame_idx = 0  # Sprite 106
                elif self.underground_timer < 0.4:
                    self.frame_idx = 1  # Sprite 107
                elif self.underground_timer < 0.6:
                    self.frame_idx = 2  # Sprite 108
                else:
                    # Fin de l'attaque
                    self.underground_attack = False
                    self.underground_phase = 0
                    self.underground_timer = 0
                    self.is_attacking = False
                    self.state = "idle"
                    self.frame_idx = 0
            
            return
        
        # Gestion spéciale de la téléportation
        if self.teleporting:
            self.teleport_timer += dt
            
            # Phase 0: Disparition (sprites 37-38) - 0.3s
            if self.teleport_phase == 0:
                if self.teleport_timer < 0.15:
                    self.frame_idx = 0  # Sprite 37
                elif self.teleport_timer < 0.3:
                    self.frame_idx = 1  # Sprite 38
                else:
                    self.teleport_phase = 1
                    self.teleport_timer = 0
                    # Téléporter derrière l'ennemi
                    if target:
                        if self.facing_right:
                            self.teleport_target_x = target.x + 100
                        else:
                            self.teleport_target_x = target.x - 100
                    else:
                        self.teleport_target_x = self.x + (200 if self.facing_right else -200)
            
            # Phase 1: Invisible/téléportation - 0.2s
            elif self.teleport_phase == 1:
                if self.teleport_timer < 0.2:
                    self.frame_idx = 1  # Reste invisible (sprite 38)
                else:
                    self.teleport_phase = 2
                    self.teleport_timer = 0
                    # Apparaître à la nouvelle position en l'air
                    self.x = self.teleport_target_x
                    self.y = GROUND_Y - 150  # En l'air
                    self.vy = 0
                    self.on_ground = False
            
            # Phase 2: Réapparition en l'air (sprite 39) - 0.2s
            elif self.teleport_phase == 2:
                self.frame_idx = 2  # Sprite 39 (chute libre)
                self.vy += GRAVITY * dt  # Gravité
                self.y += self.vy * dt
                
                if self.teleport_timer >= 0.2 or self.y >= GROUND_Y:
                    self.teleport_phase = 3
                    self.teleport_timer = 0
            
            # Phase 3: Atterrissage (sprite 40) - 0.15s
            elif self.teleport_phase == 3:
                self.frame_idx = 3  # Sprite 40
                self.y = GROUND_Y
                self.vy = 0
                self.on_ground = True
                
                if self.teleport_timer >= 0.15:
                    # Fin de la téléportation
                    self.teleporting = False
                    self.teleport_phase = 0
                    self.teleport_timer = 0
                    self.is_attacking = False
                    self.state = "idle"
                    self.frame_idx = 0
            
            return  # Ne pas exécuter le reste de update pendant la téléportation
        
        # Animation normale
        self.anim_timer += dt
        frames = self.get_current_frames()
        
        # Vitesse d'animation adaptée
        anim_speed = self.anim_fps
        if self.state == "attack_combo":
            anim_speed = 15  # Plus rapide pour le combo
        elif self.state == "attack_special":
            anim_speed = 12  # Vitesse moyenne pour bien voir l'orbe
        
        # Gestion de l'attaque Kyubi (Beam)
        if self.state == "attack_kyubi":
            # Si on arrive à la fin de la transformation (sprite 258 est le dernier de la liste passée)
            if self.frame_idx == len(frames) - 1:
                # Maintenir le dernier sprite (Naruto en pose de tir)
                self.is_firing_beam = True
                self.beam_timer += dt
                
                # Calculer la fin du rayon
                if self.facing_right:
                    self.beam_end_x = WIN_W
                    if target and target.x > self.x: # Hit
                         hb = target.get_hitbox()
                         self.beam_end_x = hb.left if hb else target.x
                else:
                    self.beam_end_x = 0
                    if target and target.x < self.x:
                         hb = target.get_hitbox()
                         self.beam_end_x = hb.right if hb else target.x

                # Rester sur la frame 258 (index 10 dans la liste [248...258])
                self.frame_idx = len(frames) - 1
                self.anim_timer = 0 # Bloquer l'avancement normal de l'animation
                
                # Fin du rayon
                if self.beam_timer >= self.beam_duration:
                    self.is_firing_beam = False
                    self.is_attacking = False
                    self.state = "idle"
                    self.frame_idx = 0
                    self.beam_timer = 0
                    self.kyubi_energy = 0 # Reset énergie
        
        if self.anim_timer >= 1.0 / anim_speed and self.state != "attack_kyubi": # Sauf si kyubi bloqué
            self.anim_timer = 0
            
            # Gestion spéciale pour l'animation de mort par rayon (ne pas boucler)
            if self.state == "hit_kyubi":
                if self.frame_idx < len(frames) - 1:
                    self.frame_idx += 1
                # Sinon on reste sur la dernière frame (par terre)
            else:
                self.frame_idx = (self.frame_idx + 1) % len(frames)
            
            # Note: Plus de projectile pour l'attaque spéciale, c'est une attaque au corps à corps maintenant
            # si on voulait remettre le projectile, c'était ici.
            
            # Reset hit flag pour Combo (permet 2 coups : poing puis pied)
            # On réactive la possibilité de toucher à mi-parcours
            if self.state == "attack_combo" and self.frame_idx == 7:
                 self.attack_hit = False

            # Fin de l'animation d'attaque
            if self.is_attacking and self.frame_idx == 0:
                self.is_attacking = False
                self.attack_damage = 0
                self.attack_hit = False
                self.state = "idle"
        
        # Cas spécial: animation Kyubi avant le tir
        if self.state == "attack_kyubi" and not self.is_firing_beam:
             if self.anim_timer >= 1.0 / 10: # Vitesse transformation
                self.anim_timer = 0
                if self.frame_idx < len(frames) - 1:
                    self.frame_idx += 1
        
        # Cooldowns
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt
        
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.invincible = False
        
        if self.hit_timer > 0:
            self.hit_timer -= dt
            if self.hit_timer <= 0:
                self.is_hit = False
                self.state = "idle"
        
        # Gestion de la stamina du bouclier
        if self.is_blocking:
            self.block_stamina = max(0, self.block_stamina - self.block_drain_rate * dt)
            if self.block_stamina <= 0:
                self.is_blocking = False  # Bouclier cassé
                self.state = "idle"
        else:
            # Régénération de la stamina
            self.block_stamina = min(self.block_stamina_max, self.block_stamina + self.block_regen_rate * dt)
        
        # Régénération du chakra
        if not self.is_attacking:
            self.chakra = min(self.chakra_max, self.chakra + self.chakra_regen_rate * dt)
        
        # Gravité
        if not self.on_ground:
            self.vy += GRAVITY * dt
        
        # Mouvement (inclure knockback)
        total_vx = self.vx + self.knockback_vx
        self.x += total_vx * dt
        self.y += self.vy * dt
        
        # Réduire le knockback progressivement
        if abs(self.knockback_vx) > 0:
            self.knockback_vx *= 0.85  # Friction
            if abs(self.knockback_vx) < 10:
                self.knockback_vx = 0
        
        # Sol
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vy = 0
            self.on_ground = True
            if self.state == "jump":
                self.state = "idle"
        
        # Limites du terrain - BLOQUER dans les zones bleues
        sprite_w = self.get_current_frames()[0].get_width() if self.get_current_frames() else 50
        
        if self.x < TERRAIN_LEFT:
            self.x = TERRAIN_LEFT
            self.vx = 0
            self.knockback_vx = 0
        elif self.x + sprite_w > TERRAIN_RIGHT:
            self.x = TERRAIN_RIGHT - sprite_w
            self.vx = 0
            self.knockback_vx = 0
        
        if self.y < TERRAIN_TOP:
            self.y = TERRAIN_TOP
            self.vy = 0
        elif self.y > TERRAIN_BOTTOM:
            self.y = TERRAIN_BOTTOM
            self.vy = 0
    
    def move(self, direction):
        """Déplace le combattant"""
        if not self.is_attacking and not self.is_hit:
            self.vx = direction * (PLAYER_SPEED if self.name == "Naruto" else ENEMY_SPEED)
            if direction != 0:
                self.facing_right = (direction > 0)
                if self.state == "idle" and self.on_ground:
                    self.state = "run"
            elif self.on_ground and self.state == "run":
                self.state = "idle"
    
    def jump(self):
        """Fait sauter le combattant"""
        if self.on_ground and not self.is_attacking and not self.is_hit:
            self.vy = JUMP_FORCE
            self.on_ground = False
            self.state = "jump"
    
    def attack(self, attack_type="light"):
        """Lance une attaque"""
        if not self.is_attacking and not self.is_hit and self.attack_cooldown <= 0:
            self.is_attacking = True
            self.attack_type = attack_type
            self.attack_hit = False
            self.vx = 0
            self.frame_idx = 0
            
            # Définir les dégâts et l'animation selon le type
            if attack_type == "light":
                self.attack_damage = LIGHT_ATTACK_DAMAGE
                self.state = "attack"
                self.attack_cooldown = 0.4
            elif attack_type == "heavy":
                self.attack_damage = HEAVY_ATTACK_DAMAGE
                # Utiliser sprites différents selon si on est au sol ou en l'air
                if self.on_ground:
                    self.state = "attack_heavy"
                else:
                    self.state = "attack_heavy_air"
                self.attack_cooldown = 0.6
            elif attack_type == "teleport":
                self.attack_damage = HEAVY_ATTACK_DAMAGE + 3
                self.state = "attack_teleport"
                self.attack_cooldown = 1.5
                # Démarrer la téléportation
                self.teleporting = True
                self.teleport_phase = 0
                self.teleport_timer = 0
            elif attack_type == "combo":
                self.attack_damage = LIGHT_ATTACK_DAMAGE + 3
                self.state = "attack_combo"
                self.attack_cooldown = 0.8
            elif attack_type == "special":
                # Attaque spéciale nécessite 50 chakra
                if self.chakra >= 50:
                    self.attack_damage = HEAVY_ATTACK_DAMAGE + 8  # 20 dégâts
                    self.state = "attack_special"
                    self.attack_cooldown = 2.0
                    self.chakra -= 50
                    self.should_spawn_orb = False  # Reset le flag
                else:
                    self.is_attacking = False
                    # Pas assez de chakra
                    return None
            elif attack_type == "kyubi":
                # Attaque ultime Kyubi - Nécessite jauge pleine
                if self.kyubi_energy >= self.kyubi_max:
                    self.attack_damage = 1 # Dégâts par frame !
                    self.state = "attack_kyubi"
                    self.attack_cooldown = 3.0
                    # Ne pas vider tout de suite, on vide à la fin
                else:
                    self.is_attacking = False
                    return None
            elif attack_type == "underground":
                # Attaque sous-sol (nécessite 30 chakra)
                if self.chakra >= 30:
                    self.attack_damage = HEAVY_ATTACK_DAMAGE + 15  # 27 dégâts
                    self.state = "attack_underground"
                    self.attack_cooldown = 2.5
                    self.chakra -= 30
                    # Démarrer l'attaque sous-sol
                    self.underground_attack = True
                    self.underground_phase = 0
                    self.underground_timer = 0
                else:
                    self.is_attacking = False
                    return None
            
            return attack_type
        return None
    
    def start_block(self):
        """Commence à bloquer"""
        if not self.is_attacking and not self.is_hit and self.block_stamina > 0:
            self.is_blocking = True
            self.state = "block"
            self.vx = 0
            self.frame_idx = 0
    
    def stop_block(self):
        """Arrête de bloquer"""
        if self.is_blocking:
            self.is_blocking = False
            self.state = "idle"
            self.frame_idx = 0
    
    def take_damage(self, damage, attacker_facing_right=True, attack_type="light"):
        """Reçoit des dégâts avec knockback et animation selon le type de coup"""
        # Si on bloque et que l'attaque vient de face
        if self.is_blocking and self.block_stamina > 0:
            # Vérifier si l'attaque vient de face (directions opposées)
            # Si je regarde à droite, l'attaquant doit regarder à gauche (m'attaquer de face)
            attack_from_front = self.facing_right != attacker_facing_right
            
            if attack_from_front:
                # Bloquer l'attaque : réduire les dégâts de 90% (très efficace)
                blocked_damage = int(damage * 0.1)
                self.health = max(0, self.health - blocked_damage)
                
                # Drain de stamina supplémentaire
                stamina_cost = damage * 0.5
                self.block_stamina = max(0, self.block_stamina - stamina_cost)
                
                # Petit recul
                knockback_force = 100
                self.knockback_vx = knockback_force if attacker_facing_right else -knockback_force
                
                print(f"{self.name} BLOQUE ! Dégâts réduits: {blocked_damage} (stamina: {int(self.block_stamina)})")
                return True
        
        # Sinon, dégâts normaux
        if not self.invincible and not self.is_hit:
            self.health = max(0, self.health - damage)
            
            # MORT INSTANTANÉE PAR RAYON KYUBI
            if attack_type == "kyubi_beam":
                self.health = 0 # Force 0 HP
                self.is_hit = True # On bloque les mouvements
                self.invincible = True
                self.state = "hit_kyubi" # Anim demandée: 55->52
                self.frame_idx = 0
                self.hit_timer = 2.0 # Temps pour voir l'anim complète
                self.invincible_timer = 2.0
                print(f"{self.name} PULVÉRISÉ PAR LE RAYON ! (Anim 55->52)")
                return True

            self.is_hit = True
            self.invincible = True
            self.frame_idx = 0
            self.vx = 0
            
            # Annuler toute attaque en cours (IMPORTANT pour le combo)
            self.is_attacking = False
            self.teleporting = False
            self.underground_attack = False
            self.is_firing_beam = False
            
            # Désactiver le blocage si on est touché
            self.is_blocking = False
            
            # Animation et knockback selon la sévérité du coup
            if damage >= 25 or attack_type == "heavy" or attack_type == "teleport":
                # Si le personnage est en l'air, état knockdown
                if not self.on_ground:
                    self.state = "hit_knockdown"
                else:
                    # Coup lourd : grosse réaction
                    self.state = "hit_heavy"
                self.hit_timer = 0.5
                self.invincible_timer = 1.0
                knockback_force = 500
            elif damage >= 15 or attack_type == "combo":
                # Coup moyen
                self.state = "hit_heavy"
                self.hit_timer = 0.4
                self.invincible_timer = 0.8
                knockback_force = 350
            else:
                # Coup léger
                self.state = "hit_light"
                self.hit_timer = 0.3
                self.invincible_timer = 0.6
                knockback_force = 250
            
            # Knockback : repoussé dans la direction opposée à l'attaquant
            self.knockback_vx = knockback_force if attacker_facing_right else -knockback_force
            
            return True
        return False
    
    def get_hitbox(self):
        """Retourne la hitbox du combattant (corps uniquement)"""
        frames = self.get_current_frames()
        # Protection contre l'index hors limites
        if self.frame_idx >= len(frames):
            self.frame_idx = 0
        frame = frames[self.frame_idx]
        w, h = frame.get_size()
        # Hitbox réduite : centrée sur le corps (60% largeur, 80% hauteur)
        hitbox_w = int(w * 0.6)
        hitbox_h = int(h * 0.8)
        hitbox_x = self.x + (w - hitbox_w) // 2
        hitbox_y = self.y + (h - hitbox_h) // 2
        return pygame.Rect(hitbox_x, hitbox_y, hitbox_w, hitbox_h)
    
    def get_attack_box(self):
        """Retourne la zone d'attaque (active uniquement sur les frames d'impact)"""
        if self.is_attacking and not self.attack_hit:
            # Téléportation : hitbox active en phases 2 et 3 (apparition/atterrissage)
            if self.teleporting and self.teleport_phase >= 2:
                frames = self.get_current_frames()
                if self.frame_idx < len(frames):
                    frame = frames[self.frame_idx]
                    w, h = frame.get_size()
                    # Grande zone d'attaque autour du personnage pour la téléportation
                    attack_w = int(w * 0.8)
                    attack_h = int(h * 0.8)
                    attack_x = self.x + (w - attack_w) // 2
                    attack_y = self.y + (h - attack_h) // 2
                    return pygame.Rect(attack_x, attack_y, attack_w, attack_h)
            
            # Attaque sous-sol : hitbox active en phase 2 (surgissement)
            elif self.underground_attack:
                if self.underground_phase == 2:
                    frames = self.get_current_frames()
                    # Utiliser les sprites de surgissement (index 3 à 5)
                    sprite_idx = 3 + self.frame_idx
                    if sprite_idx < len(frames):
                        frame = frames[sprite_idx]
                        w, h = frame.get_size()
                        # Grande zone d'attaque autour de Naruto qui surgit du sol
                        attack_w = int(w * 0.9)
                        attack_h = int(h * 0.9)
                        attack_x = self.x + (w - attack_w) // 2
                        attack_y = self.y + (h - attack_h) // 2
                        return pygame.Rect(attack_x, attack_y, attack_w, attack_h)
                return None

            # Attaques normales
            elif not self.teleporting:
                frames = self.get_current_frames()
                # Protection contre l'index hors limites
                if self.frame_idx >= len(frames):
                    self.frame_idx = 0
                
                # Gestion spécifique pour l'attaque spéciale (Rasengan en main)
                if self.state == "attack_special":
                    # L'orbe apparaît à l'index 9 (sprite 143) et disparaît vers la fin
                    if 9 <= self.frame_idx <= 12:
                        frame = frames[self.frame_idx]
                        w, h = frame.get_size()
                        # Hitbox généreuse pour le Rasengan (taille augmentée)
                        attack_w = int(w * 0.7)
                        attack_h = int(h * 0.7)
                        if self.facing_right:
                            attack_x = self.x + w * 0.6
                        else:
                            attack_x = self.x - attack_w + w * 0.4
                        attack_y = self.y + h * 0.2
                        return pygame.Rect(attack_x, attack_y, attack_w, attack_h)
                    return None
                
                # Gestion spécifique pour le mode Kyubi (Rayon)
                if self.state == "attack_kyubi":
                    # On active la hitbox seulement après un court délai visuel (0.5s)
                    # Cela permet de voir le rayon sortir avant que Sasuke ne meure
                    if getattr(self, 'is_firing_beam', False) and self.beam_timer > 0.5: 
                        # Rayon horizontal sur toute la largeur devant
                        attack_w = WIN_W  # Toute la longueur
                        attack_h = 100
                        if self.facing_right:
                            attack_x = self.x + 130 # Ajusté selon le visuel
                        else:
                            attack_x = self.x - attack_w + 50
                        attack_y = self.y + 40
                        return pygame.Rect(attack_x, attack_y, attack_w, attack_h)
                    return None
                
                # Gestion spécifique pour le combo (Hitbox active sur poings et pieds)
                if self.state == "attack_combo":
                    # frames 2-5 (poings) et 8-12 (pieds)
                    if (2 <= self.frame_idx <= 5) or (8 <= self.frame_idx <= 12):
                        frame = frames[self.frame_idx]
                        w, h = frame.get_size()
                        attack_w = int(w * 0.5)
                        attack_h = int(h * 0.5)
                        if self.facing_right:
                            attack_x = self.x + w * 0.6
                        else:
                            attack_x = self.x - attack_w + w * 0.4
                        attack_y = self.y + h * 0.3
                        return pygame.Rect(attack_x, attack_y, attack_w, attack_h)
                    return None

                # ACTIVER LA HITBOX UNIQUEMENT SUR LES FRAMES D'IMPACT
                # Frame d'impact = milieu de l'animation (où le coup touche)
                num_frames = len(frames)
                impact_frame = num_frames // 2  # Frame du milieu
                
                # Hitbox active seulement sur la frame d'impact (± 1 frame)
                if abs(self.frame_idx - impact_frame) <= 1:
                    frame = frames[self.frame_idx]
                    w, h = frame.get_size()
                    # Attack box réduite : 40% de la largeur du sprite, positionnée devant
                    attack_w = int(w * 0.4)
                    attack_h = int(h * 0.5)
                    if self.facing_right:
                        attack_x = self.x + w * 0.7  # Devant le personnage
                    else:
                        attack_x = self.x - attack_w + w * 0.3  # Devant le personnage (gauche)
                    attack_y = self.y + h * 0.3
                    return pygame.Rect(attack_x, attack_y, attack_w, attack_h)
        return None
    
    def draw(self, surface, debug_hitboxes=False):
        """Dessine le combattant"""
        # Gestion spéciale pour l'attaque sous-sol
        if self.underground_attack and self.state == "attack_underground":
            frames = self.get_current_frames()
            
            # Selon la phase, on affiche différents sprites
            if self.underground_phase == 0:
                # Phase 0: sprites 104-105 (index 0-1) - frappe le sol
                frame = frames[self.frame_idx]
                draw_x = int(self.x)
                draw_y = int(self.y)
            elif self.underground_phase == 1:
                # Phase 1: sprite 116 (index 2) - fumée
                frame = frames[2]
                draw_x = int(self.x)
                draw_y = int(self.y)
            elif self.underground_phase == 2:
                # Phase 2: sprites 106-108 (index 3-5) - surgissement du sol
                frame = frames[3 + self.frame_idx]
                draw_x = int(self.x)
                # Descendre Naruto pour montrer qu'il attaque d'en bas
                # Plus on avance dans l'animation (106->107->108), plus il remonte
                offset_y = 60 - (self.frame_idx * 20)  # 60, 40, 20 pixels en dessous
                draw_y = int(self.y) + offset_y
            else:
                frame = frames[0]
                draw_x = int(self.x)
                draw_y = int(self.y)
            
            # Inverser si regarde à gauche
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            
            # Dessiner Naruto d'abord
            surface.blit(frame, (draw_x, draw_y))
            
            # Dessiner le sol qui se casse PAR-DESSUS Naruto pendant la phase 2 pour l'effet de déchirement
            if self.underground_phase == 2 and len(self.ground_crack_sprites) >= 3:
                crack_sprite = self.ground_crack_sprites[self.frame_idx]
                if not self.facing_right:
                    crack_sprite = pygame.transform.flip(crack_sprite, True, False)
                # Centrer le sol qui se casse sur Naruto
                naruto_w = frame.get_width()
                crack_w = crack_sprite.get_width()
                crack_x = draw_x + (naruto_w - crack_w) // 2  # Centrer horizontalement
                crack_y = int(self.y) + 50  # Au niveau des pieds
                surface.blit(crack_sprite, (crack_x, crack_y))
            
            # Debug hitboxes
            if debug_hitboxes:
                attack_box = self.get_attack_box()
                if attack_box:
                    pygame.draw.rect(surface, (255, 0, 0), attack_box, 2)
                hitbox = self.get_hitbox()
                pygame.draw.rect(surface, (0, 255, 0), hitbox, 2)
            return
        
        frames = self.get_current_frames()
        # Protection contre l'index hors limites
        if self.frame_idx >= len(frames):
            self.frame_idx = 0
        frame = frames[self.frame_idx]
        
        # Inverser si regarde à gauche
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        
        # Calcul de la position de dessin (avec correction de hauteur pour Kyubi)
        draw_x = int(self.x)
        draw_y = int(self.y)
        
        if self.state == "attack_kyubi":
             # Aligner le bas du sprite avec le sol (basé sur la hauteur idle moyenne ~80px-100px ?)
             # On utilise le premier sprite idle comme référence de hauteur "standard"
             ref_h = self.sprites["idle"][0].get_height()
             curr_h = frame.get_height()
             
             # Si le sprite actuel est plus grand, on le remonte pour que les pieds restent au sol
             if curr_h > ref_h:
                  draw_y -= (curr_h - ref_h)
             
             # Ajustement supplémentaire demandé (remonter un peu plus)
             draw_y -= 25

        # Effet de flash quand touché ou invincible
        # Pas de flash rouge pour l'animation spécifique "hit_kyubi" pour bien voir les sprites
        if self.state != "hit_kyubi" and self.is_hit and int(self.hit_timer * 10) % 2:
            # Créer effet rouge
            red_overlay = frame.copy()
            red_overlay.fill((255, 0, 0, 100), special_flags=pygame.BLEND_ADD)
            surface.blit(red_overlay, (draw_x, draw_y))
        elif self.invincible and int(self.invincible_timer * 8) % 2:
            # Clignotement pendant invincibilité (sauf hit_kyubi)
            if self.state != "hit_kyubi":
                frame.set_alpha(128)
                surface.blit(frame, (draw_x, draw_y))
                frame.set_alpha(255)
            else:
                surface.blit(frame, (draw_x, draw_y))
        else:
            surface.blit(frame, (draw_x, draw_y))
        
        # Effet Kyubi Beam
        if self.state == "attack_kyubi" and self.is_firing_beam:
            # Le rayon part de la main, ajusté avec draw_y
            beam_start_y = draw_y + 35
            
            if len(self.kyubi_beam_sprites) >= 3:
                # 258(Start), 259(End), 260(Mid)
                sp_start = self.kyubi_beam_sprites[0]
                sp_end = self.kyubi_beam_sprites[1]
                sp_mid = self.kyubi_beam_sprites[2]
                
                if not self.facing_right:
                    sp_start = pygame.transform.flip(sp_start, True, False)
                    sp_end = pygame.transform.flip(sp_end, True, False)
                    sp_mid = pygame.transform.flip(sp_mid, True, False)
                
                target_x = getattr(self, 'beam_end_x', WIN_W if self.facing_right else 0)
                
                # User request: "au bout du rayon le sprits 259 inversé"
                # Donc on le re-flip horizontalement (soit il regarde vers Naruto soit l'inverse de d'habitude)
                sp_final_cap = pygame.transform.flip(sp_end, True, False)
                
                # Centrage vertical du rayon (260) par rapport au départ (258)
                # Si le départ est plus grand, on décale le rayon vers le bas pour le centrer
                mid_y_offset = (sp_start.get_height() - sp_mid.get_height()) // 2
                end_y_offset = (sp_start.get_height() - sp_final_cap.get_height()) // 2

                if self.facing_right:
                    # Plus loin de la bouche (encore plus à droite)
                    beam_start_x = self.x + 130
                    # 1. Start
                    surface.blit(sp_start, (beam_start_x, beam_start_y))
                    
                    # CORRECTION DU DÉCALAGE : On chevauche les sprites pour éviter le trou
                    # On recule le début de la boucle car le sprite de départ a probablement de la transparence à droite
                    overlap = 45 # Chevauchement important pour fermer le trou
                    current_x = beam_start_x + sp_start.get_width() - overlap
                    
                    # 2. Mid Loop
                    while current_x + sp_final_cap.get_width() < target_x:
                        surface.blit(sp_mid, (current_x, beam_start_y + mid_y_offset))
                        current_x += sp_mid.get_width() # On peut aussi ajouter un petit overlap ici si besoin (-1)
                    # 3. End
                    surface.blit(sp_final_cap, (target_x - sp_final_cap.get_width(), beam_start_y + end_y_offset))
                
                else:
                    # Ajustement pour la gauche aussi (miroir)
                    beam_start_x = self.x - 70
                    # 1. Start (dessiné vers la gauche)
                    draw_x = beam_start_x - sp_start.get_width()
                    surface.blit(sp_start, (draw_x, beam_start_y))
                    
                    # CORRECTION GAUCHE
                    overlap = 45
                    current_x = draw_x + overlap
                    
                    # 2. Mid Loop
                    while current_x - sp_final_cap.get_width() > target_x:
                        current_x -= sp_mid.get_width()
                        surface.blit(sp_mid, (current_x, beam_start_y + mid_y_offset))
                    # 3. End
                    surface.blit(sp_final_cap, (target_x, beam_start_y + end_y_offset))

        # Mode debug : afficher les hitbox
        if debug_hitboxes:
            # Hitbox du corps (vert)
            hitbox = self.get_hitbox()
            pygame.draw.rect(surface, (0, 255, 0), hitbox, 2)
            
            # Attack box (rouge)
            attack_box = self.get_attack_box()
            if attack_box:
                pygame.draw.rect(surface, (255, 0, 0), attack_box, 2)


class EnemyAI:
    """Intelligence artificielle pour Sasuke"""
    def __init__(self, fighter):
        self.fighter = fighter
        self.state = "patrol"
        self.patrol_timer = 0
        self.attack_range = 100
        self.detection_range = 300
        self.ai_attack_cooldown = 0
    
    def update(self, dt, player):
        """Met à jour l'IA"""
        if self.ai_attack_cooldown > 0:
            self.ai_attack_cooldown -= dt

        distance = abs(self.fighter.x - player.x)
        
        # État: Attaque
        if distance < self.attack_range and not self.fighter.is_attacking:
            if self.ai_attack_cooldown <= 0:
                self.state = "attack"
                self.fighter.attack("light")
                self.fighter.attack_damage = LIGHT_ATTACK_DAMAGE
                self.fighter.move(0)
                # Cooldown entre les attaques de l'IA (1.5 à 2.5 secondes)
                import random
                self.ai_attack_cooldown = random.uniform(1.5, 2.5)
            else:
                # Si en cooldown, reculer ou bloquer parfois
                pass
        
        # État: Poursuite
        elif distance < self.detection_range:
            self.state = "chase"
            direction = 1 if player.x > self.fighter.x else -1
            self.fighter.move(direction)
            
            # Sauter si le joueur est en l'air
            if not player.on_ground and self.fighter.on_ground:
                self.fighter.jump()
        
        # État: Patrouille
        else:
            self.state = "patrol"
            self.patrol_timer -= dt
            
            if self.patrol_timer <= 0:
                # Changer de direction aléatoirement
                import random
                direction = random.choice([-1, 0, 1])
                self.fighter.move(direction)
                self.patrol_timer = random.uniform(1, 3)



def draw_start_screen(screen):
    """Affiche l'écran d'accueil"""
    font_title = pygame.font.SysFont("Arial", 80, bold=True)
    font_button = pygame.font.SysFont("Arial", 50, bold=True)
    
    # Charger l'image de fond si possible, sinon couleur unie
    try:
        bg = pygame.image.load(BACKGROUND_IMAGE).convert()
        bg = pygame.transform.scale(bg, (WIN_W, WIN_H))
        # Assombrir le fond pour la lisibilité
        overlay = pygame.Surface((WIN_W, WIN_H))
        overlay.set_alpha(128)
        overlay.fill((0, 0, 0))
    except:
        bg = pygame.Surface((WIN_W, WIN_H))
        bg.fill((30, 30, 30))
        overlay = None

    # Bouton Jouer
    button_rect = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 50, 200, 80)
    button_color = (255, 140, 0) # Orange Naruto
    button_hover_color = (255, 100, 0)
    
    waiting = True
    clock = pygame.time.Clock()
    
    while waiting:
        clock.tick(60)
        mouse_pos = pygame.mouse.get_pos()
        is_hover = button_rect.collidepoint(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and is_hover:
                    waiting = False
        
        # Dessin
        screen.blit(bg, (0, 0))
        if overlay:
            screen.blit(overlay, (0, 0))
            
        # Titre (avec ombre)
        title_text = "NARUTO vs SASUKE"
        shadow_surf = font_title.render(title_text, True, (0, 0, 0))
        shadow_rect = shadow_surf.get_rect(center=(WIN_W // 2 + 4, WIN_H // 2 - 50 + 4))
        screen.blit(shadow_surf, shadow_rect)
        
        title_surf = font_title.render(title_text, True, (255, 215, 0))
        title_rect = title_surf.get_rect(center=(WIN_W // 2, WIN_H // 2 - 50))
        screen.blit(title_surf, title_rect)
        
        # Bouton
        color = button_hover_color if is_hover else button_color
        pygame.draw.rect(screen, color, button_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), button_rect, 3, border_radius=10) # Bordure blanche
        
        text_surf = font_button.render("JOUER", True, (255, 255, 255))
        text_rect = text_surf.get_rect(center=button_rect.center)
        screen.blit(text_surf, text_rect)
        
        pygame.display.flip()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_W, WIN_H))
    pygame.display.set_caption("Naruto vs Sasuke - Combat")
    
    # Afficher l'écran d'accueil avant le chargement
    draw_start_screen(screen)
    
    clock = pygame.time.Clock()
    
    print("Chargement du jeu de combat...")
    
    # Charger le fond
    try:
        background = pygame.image.load(BACKGROUND_IMAGE).convert()
        background = pygame.transform.scale(background, (WIN_W, WIN_H))
    except:
        background = pygame.Surface((WIN_W, WIN_H))
        background.fill((150, 180, 220))
    
    # Charger les sprites Naruto (orange)
    print("Chargement des sprites Naruto...")
    try:
        # Création des sprites composites pour l'attaque spéciale (Naruto 142 + Orbe)
        sp_start = load_sprites([133, 134, 135, 136, 138, 139, 140, 141, 142])
        sp_base = load_sprite(142)
        # On utilise uniquement le sprite 143 (orbe pleine) répété pour maintenir l'attaque visible
        sp_orbs = load_sprites([143, 143, 143, 143, 143])
        sp_end = []
        for orb in sp_orbs:
            # Calculer les offsets
            # Décaler vers la droite et le haut pour être sur la main (+45px, -15px)
            ox = (sp_base.get_width() - orb.get_width()) // 2 + 45
            oy = (sp_base.get_height() - orb.get_height()) // 2 - 15
            
            # Créer une image composite assez grande pour tout contenir
            final_w = max(sp_base.get_width(), ox + orb.get_width())
            final_h = max(sp_base.get_height(), oy + orb.get_height())
            
            # Surface transparente (RGBA)
            comp = pygame.Surface((final_w, final_h), pygame.SRCALPHA)
            
            # Dessiner Naruto (base) puis l'orbe
            comp.blit(sp_base, (0, 0))
            comp.blit(orb, (ox, oy))
            sp_end.append(comp)

        naruto_sprites = {
            "idle": load_sprites([26, 27, 28, 29, 30]),
            "run": load_sprites([31, 32, 33, 34, 35, 36]),
            "jump": load_sprites([41]),
            "attack": load_sprites([60, 61, 62, 63, 64, 65]),  # Attaque gauche-droite
            "attack_heavy": load_sprites([94, 95, 96, 97, 98, 99]),  # Attaque lourde au sol
            "attack_heavy_air": load_sprites([81, 83, 84, 85, 86, 87, 88]),  # Attaque lourde en l'air
            "attack_teleport": load_sprites([37, 38, 39, 40]),  # Téléportation: disparition -> air -> atterrissage
            "attack_combo": load_sprites(list(range(60, 74))),  # Combo long (sprites 60-73)
            "attack_special": sp_start + sp_end,  # Attaque spéciale composite
            "attack_kyubi": load_sprites([248, 249, 250, 251, 252, 253, 254]), # Transformation jusqu'a la pose
            "attack_underground": load_sprites([104, 105, 116, 106, 107, 108]),  # Attaque sous-sol: frappe, fumée, surgissement
            "block": load_sprites([43]),  # Bouclier
            "hit_light": load_sprites([44, 45]),  # Coup léger: simple recul
            "hit_heavy": load_sprites([54, 55]),  # Coup lourd: plus de réaction
            "hit_knockdown": load_sprites([56, 57])  # Projeter au sol
        }
    except Exception as e:
        print(f"Erreur Naruto: {e}")
        # Utiliser des sprites de base qui existent
        naruto_sprites = {
            "idle": load_sprites([13]),
            "run": load_sprites([31, 32, 33, 34, 35, 36]),
            "jump": load_sprites([41]),
            "attack": load_sprites([45, 46]),
            "attack_heavy": load_sprites([94, 95]),
            "attack_heavy_air": load_sprites([81, 83, 84]),
            "attack_teleport": load_sprites([37, 38, 39, 40]),  # Essayer quand même
            "attack_combo": load_sprites([45, 46, 47]),
            "attack_special": load_sprites([133, 134, 135, 136, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147]),
            "block": load_sprites([43]),
            "hit_light": load_sprites([44, 45]),
            "hit_heavy": load_sprites([13]),
            "hit_knockdown": load_sprites([13])
        }
    
    # Charger les sprites de l'orbe de chakra (176-180)
    print("Chargement des sprites de l'orbe de chakra...")
    try:
        orb_sprites = load_sprites([176, 177, 178, 179, 180])
    except Exception as e:
        print(f"Erreur chargement orbe: {e}")
        orb_sprites = []

    # Charger les sprites du rayon Kyubi
    print("Chargement des sprites Rayon Kyubi...")
    try:
        kyubi_beam = load_sprites([258, 259, 260])
    except Exception as e:
        print(f"Erreur chargement rayon: {e}")
        kyubi_beam = []
    
    # Charger les sprites Sasuke (vrais sprites depuis sasuke_frames)
    print("Chargement des sprites Sasuke...")
    try:
        sasuke_sprites = {
            "idle": load_sprites_sasuke([32]),  # Sprites idle Sasuke
            "run": load_sprites_sasuke([33, 34, 35, 36, 37, 38]),  # Course - animation de déplacement
            "jump": load_sprites_sasuke([42]),  # Saut
            "attack": load_sprites_sasuke([62, 63]),  # Attaque normale
            "attack_heavy": load_sprites_sasuke([62, 63]),  # Même que attaque normale
            "attack_teleport": load_sprites_sasuke([31, 32, 33, 34]),  # Téléportation
            "attack_combo": load_sprites_sasuke([50, 51, 52, 53]),  # Combo
            "block": load_sprites_sasuke([43]),  # Bouclier
            "hit_light": load_sprites_sasuke([45, 46]),  # Coup léger (modif: 0 -> 45, 46)
            "hit_heavy": load_sprites_sasuke([54, 55]),  # Coup lourd
            "hit_kyubi": load_sprites_sasuke([55, 54, 53, 52]), # Animation spécifique mort par rayon
            "hit_knockdown": load_sprites_sasuke([56])  # Projeter au sol (modif: 56, 57 -> 56)
        }
    except Exception as e:
        print(f"Erreur Sasuke: {e}")
        # Utiliser des sprites de base de Sasuke
        sasuke_sprites = {
            "idle": load_sprites_sasuke([5]),
            "run": load_sprites_sasuke([33, 34, 35, 36, 37, 38]),
            "jump": load_sprites_sasuke([42]),
            "attack": load_sprites_sasuke([62, 63]),
            "attack_heavy": load_sprites_sasuke([45, 46]),
            "attack_teleport": load_sprites_sasuke([31, 32, 33, 34]),
            "attack_combo": load_sprites_sasuke([50, 51, 52]),
            "block": load_sprites_sasuke([43]),
            "hit_light": load_sprites_sasuke([5]),
            "hit_heavy": load_sprites_sasuke([5]),
            "hit_knockdown": load_sprites_sasuke([5])
        }
    
    # Créer les combattants (sur le terrain visible)
    naruto = Fighter(150, GROUND_Y, "Naruto", naruto_sprites, facing_right=True)
    sasuke = Fighter(1000, GROUND_Y, "Sasuke", sasuke_sprites, facing_right=False)
    
    # Stocker les sprites d'orbe dans Naruto
    naruto.orb_sprites = orb_sprites
    naruto.kyubi_beam_sprites = kyubi_beam
    
    # Charger les sprites du sol qui se casse (122-124)
    try:
        ground_crack_sprites = load_sprites([122, 123, 124])
        naruto.ground_crack_sprites = ground_crack_sprites
    except Exception as e:
        print(f"Erreur chargement sol cassé: {e}")
        naruto.ground_crack_sprites = []
    
    # Liste des projectiles d'orbe de chakra
    chakra_orbs = []
    
    # IA de Sasuke
    sasuke_ai = EnemyAI(sasuke)
    
    # Interface
    font = pygame.font.SysFont("Arial", 24, bold=True)
    small_font = pygame.font.SysFont("Arial", 14, bold=True)
    big_font = pygame.font.SysFont("Arial", 48, bold=True)
    
    game_over = False
    paused = False # État de pause
    winner = None
    debug_hitboxes = False  # Mode debug pour visualiser les hitbox
    
    print("Jeu pret !")
    print("\nCONTROLES:")
    print("  <- -> : Deplacement")
    print("  ESPACE : Sauter")
    print("  A : Attaque legere (10 degats)")
    print("  Z : Attaque lourde (25 degats)")
    print("  E : Attaque teleportation (30 degats)")
    print("  C : Attaque combo (15 degats)")
    print("  Q : Attaque speciale chakra (40 degats - 50 chakra)")
    print("  D : Attaque sous-sol (27 degats - 30 chakra)")
    print("  R : Attaque ULTIME KYUBI (Mode Rage Requis)")
    print("  S (maintenir) : Bouclier (bloque 80% degats)")
    print("  H : Toggle debug hitboxes")
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        
        # Événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Clic souris
                mouse_pos = pygame.mouse.get_pos()
                
                # Clic sur le bouton pause (coin bas droit)
                # pause_rect est défini plus bas dans la boucle draw mais est constant
                pause_btn_rect = pygame.Rect(WIN_W - 60, WIN_H - 60, 40, 40)
                if pause_btn_rect.collidepoint(mouse_pos):
                    paused = not paused
                
                # Clic sur Reprendre (si en pause)
                if paused:
                    resume_btn_rect = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 20, 200, 50)
                    if resume_btn_rect.collidepoint(mouse_pos):
                        paused = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
                    paused = not paused
                
                # Si en pause, ne pas traiter les autres touches
                if paused:
                    continue

                if event.key == pygame.K_SPACE and not game_over:
                    naruto.jump()
                elif event.key == pygame.K_a and not game_over:
                    naruto.attack("light")
                elif event.key == pygame.K_z and not game_over:
                    naruto.attack("heavy")
                elif event.key == pygame.K_e and not game_over:
                    naruto.attack("teleport")
                elif event.key == pygame.K_c and not game_over:
                    naruto.attack("combo")
                elif event.key == pygame.K_q and not game_over:
                    result = naruto.attack("special")
                    if result is None:
                        print("Pas assez de chakra! (besoin: 50)")
                elif event.key == pygame.K_r and not game_over:
                    result = naruto.attack("kyubi")
                    if result is None:
                        print("Jauge Kyubi pas pleine!")
                elif event.key == pygame.K_d and not game_over:
                    result = naruto.attack("underground")
                    if result is None:
                        print("Pas assez de chakra pour l'attaque sous-sol! (besoin: 30)")
                elif event.key == pygame.K_h:
                    debug_hitboxes = not debug_hitboxes
                    print(f"Debug hitboxes: {'ON' if debug_hitboxes else 'OFF'}")
                elif event.key == pygame.K_r and game_over:
                    # Recommencer
                    main()
                    return
        
        if not game_over and not paused:
            # Contrôles du joueur
            keys = pygame.key.get_pressed()
            
            # Blocage (maintenir S)
            if keys[pygame.K_s]:
                naruto.start_block()
            else:
                naruto.stop_block()
            
            direction = 0
            if keys[pygame.K_LEFT]:
                direction = -1
            elif keys[pygame.K_RIGHT]:
                direction = 1
            
            # Ne pas bouger si on bloque
            if not naruto.is_blocking:
                naruto.move(direction)
            if direction == 0:
                naruto.vx = 0
            
            # Mettre à jour les combattants (passer la cible pour la téléportation)
            naruto.update(dt, target=sasuke)
            sasuke.update(dt, target=naruto)
                        # Spawner l'orbe de chakra si nécessaire
            if naruto.should_spawn_orb and len(naruto.orb_sprites) > 0:
                # Créer l'orbe à partir de la position de Naruto
                orb_x = naruto.x + (80 if naruto.facing_right else -40)
                orb_y = naruto.y + 30
                direction = 1 if naruto.facing_right else -1
                chakra_orbs.append(ChakraOrb(orb_x, orb_y, direction, naruto, naruto.orb_sprites))
                naruto.should_spawn_orb = False
            
            # Mettre à jour les orbes de chakra
            for orb in chakra_orbs[:]:
                orb.update(dt)
                if not orb.active:
                    chakra_orbs.remove(orb)
                elif not orb.has_hit:
                    orb_hitbox = orb.get_hitbox()
                    if orb_hitbox and orb_hitbox.colliderect(sasuke.get_hitbox()):
                        if sasuke.take_damage(orb.damage, naruto.facing_right, "special"):
                            orb.has_hit = True
                            orb.active = False
                            print(f"Orbe de chakra touche Sasuke! (-{orb.damage} HP) Sasuke HP: {sasuke.health}")
                        # Mettre à jour l'IA de Sasuke
            # Mettre à jour l'IA de Sasuke
            sasuke_ai.update(dt, naruto)
            
            # Vérifier les attaques de Naruto
            if naruto.is_attacking and not naruto.attack_hit:
                attack_box = naruto.get_attack_box()
                if attack_box and attack_box.colliderect(sasuke.get_hitbox()):
                    # Si c'est le rayon de Kyubi, on déclenche la mort immédiate
                    if naruto.state == "attack_kyubi":
                        if sasuke.health > 0: # Ne pas spammer si déjà mort
                             sasuke.take_damage(9999, naruto.facing_right, "kyubi_beam")
                             if pygame.time.get_ticks() % 10 == 0: 
                                print(f"RAYON KYUBI TOUCHÉ! Sasuke HP: {sasuke.health}")
                             # On laisse le rayon continuer visuellement
                    else:
                        if sasuke.take_damage(naruto.attack_damage, naruto.facing_right, naruto.attack_type):
                            naruto.attack_hit = True
                            print(f"Naruto touche Sasuke avec {naruto.attack_type}! (-{naruto.attack_damage} HP) Sasuke HP: {sasuke.health}")
                            
                            # Chargement de la barre Kyubi (si c'est par le rayon)
                            if naruto.kyubi_energy < naruto.kyubi_max:
                                naruto.kyubi_energy += 10 # +10 points par coup réussi
                                if naruto.kyubi_energy > naruto.kyubi_max: naruto.kyubi_energy = naruto.kyubi_max
            
            # Vérifier les attaques de Sasuke
            if sasuke.is_attacking and not sasuke.attack_hit:
                attack_box = sasuke.get_attack_box()
                if attack_box and attack_box.colliderect(naruto.get_hitbox()):
                    if naruto.take_damage(sasuke.attack_damage, sasuke.facing_right, sasuke.attack_type):
                        sasuke.attack_hit = True
                        print(f"Sasuke touche Naruto avec {sasuke.attack_type}! (-{sasuke.attack_damage} HP) Naruto HP: {naruto.health}")
            
            # Vérifier fin de partie
            if naruto.health <= 0:
                game_over = True
                winner = "Sasuke"
            elif sasuke.health <= 0:
                # Si Sasuke est en train de mourir par le rayon, on attend la fin de l'anim
                if sasuke.state == "hit_kyubi":
                    # Il tourne en boucle pendant 3s grâce au hit_timer
                    # On le laisse faire, le game over viendra quand hit_timer = 0 et state = idle
                    pass
                else:
                    game_over = True
                    winner = "Naruto"
        
        # Dessiner
        screen.blit(background, (0, 0))
        
        # Dessiner les combattants
        naruto.draw(screen, debug_hitboxes)
        sasuke.draw(screen, debug_hitboxes)
        
        # Dessiner les orbes de chakra
        for orb in chakra_orbs:
            orb.draw(screen)
        
        # Interface - Barres de vie
        # Naruto (gauche)
        pygame.draw.rect(screen, (50, 50, 50), (20, 20, 300, 30))
        health_width = int(300 * (naruto.health / MAX_HEALTH))
        pygame.draw.rect(screen, (255, 100, 0), (20, 20, health_width, 30))
        name_text = font.render("NARUTO", True, (255, 255, 255))
        screen.blit(name_text, (25, 25))
        
        # Barre de stamina Naruto (en dessous de la vie)
        pygame.draw.rect(screen, (30, 30, 30), (20, 55, 300, 15))
        stamina_width = int(300 * (naruto.block_stamina / naruto.block_stamina_max))
        stamina_color = (100, 200, 255) if naruto.block_stamina > 30 else (255, 50, 50)
        pygame.draw.rect(screen, stamina_color, (20, 55, stamina_width, 15))
        
        # Barre de chakra Naruto (en dessous de la stamina)
        pygame.draw.rect(screen, (30, 30, 30), (20, 75, 300, 15))
        chakra_width = int(300 * (naruto.chakra / naruto.chakra_max))
        chakra_color = (50, 150, 255) if naruto.chakra >= 50 else (150, 150, 150)
        pygame.draw.rect(screen, chakra_color, (20, 75, chakra_width, 15))
        chakra_text = small_font.render(f"Chakra: {int(naruto.chakra)}", True, (255, 255, 255))
        screen.blit(chakra_text, (25, 76))
        
        # Barre de Kyubi (NOUVEAU - Rouge vif)
        pygame.draw.rect(screen, (30, 0, 0), (20, 95, 300, 10)) # Fond
        kyubi_width = int(300 * (naruto.kyubi_energy / naruto.kyubi_max))
        # Rouge clignotant si plein
        kyubi_color = (255, 0, 0)
        if naruto.kyubi_energy >= naruto.kyubi_max:
             if int(pygame.time.get_ticks() / 100) % 2 == 0:
                 kyubi_color = (255, 100, 100)
        
        pygame.draw.rect(screen, kyubi_color, (20, 95, kyubi_width, 10))
        if naruto.kyubi_energy >= naruto.kyubi_max:
             ready_text = small_font.render("PRESS R !!!", True, (255, 255, 0))
             screen.blit(ready_text, (330, 90))
        
        # Bouton PAUSE (coin bas droite)
        pause_rect = pygame.Rect(WIN_W - 60, WIN_H - 60, 40, 40)
        pygame.draw.rect(screen, (200, 200, 200), pause_rect, border_radius=5)
        pygame.draw.rect(screen, (50, 50, 50), pause_rect, 2, border_radius=5)
        # Symbole pause "II"
        pygame.draw.rect(screen, (50, 50, 50), (WIN_W - 52, WIN_H - 52, 8, 24))
        pygame.draw.rect(screen, (50, 50, 50), (WIN_W - 36, WIN_H - 52, 8, 24))

        # MENU PAUSE
        if paused:
            overlay = pygame.Surface((WIN_W, WIN_H))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            pause_text = big_font.render("PAUSE", True, (255, 255, 255))
            pause_text_rect = pause_text.get_rect(center=(WIN_W // 2, WIN_H // 2 - 50))
            screen.blit(pause_text, pause_text_rect)
            
            # Bouton REPRENDRE
            resume_rect = pygame.Rect(WIN_W // 2 - 100, WIN_H // 2 + 20, 200, 50)
            is_hover_resume = resume_rect.collidepoint(pygame.mouse.get_pos())
            color_resume = (100, 200, 100) if is_hover_resume else (50, 150, 50)
            pygame.draw.rect(screen, color_resume, resume_rect, border_radius=5)
            pygame.draw.rect(screen, (255, 255, 255), resume_rect, 2, border_radius=5)
            
            resume_text = font.render("REPRENDRE", True, (255, 255, 255))
            resume_text_rect = resume_text.get_rect(center=resume_rect.center)
            screen.blit(resume_text, resume_text_rect)

        # Afficher les contrôles (Liste compacte à droite)
        controls_text = [
            ("A", "Attaque"),
            ("Z", "Lourd"),
            ("E", "Téléport"),
            ("C", "Combo"),
            ("Q", "Spécial"),
            ("D", "Sous-sol"),
            ("R", "Ult. Kyubi"),
            ("S", "Défense"),
            ("H", "Hitbox")
        ]
        
        # Fond semi-transparent pour les contrôles (Grille 3x3)
        panel_w = 420
        panel_h = 70
        panel_x = 600
        # Position au dessus du bas de l'écran (encore plus haut)
        panel_y = WIN_H - panel_h - 40
        
        control_bg = pygame.Surface((panel_w, panel_h))
        control_bg.set_alpha(100)
        control_bg.fill((0, 0, 0))
        screen.blit(control_bg, (panel_x, panel_y))
        
        # Affichage en grille (3 lignes : A,Z,E / C,Q,D / R,S,H)
        col_width = 140
        row_height = 20
        
        for i, (key, desc) in enumerate(controls_text):
            row = i // 3
            col = i % 3
            
            x_pos = panel_x + 10 + col * col_width
            y_pos = panel_y + 5 + row * row_height
            
            # Touche en jaune
            key_surf = small_font.render(key, True, (255, 255, 0))
            screen.blit(key_surf, (x_pos, y_pos))
            
            # Description en blanc
            key_w = key_surf.get_width()
            desc_surf = small_font.render(f": {desc}", True, (255, 255, 255))
            screen.blit(desc_surf, (x_pos + key_w, y_pos))

        # Sasuke (droite)
        pygame.draw.rect(screen, (50, 50, 50), (WIN_W - 320, 20, 300, 30))
        health_width = int(300 * (sasuke.health / MAX_HEALTH))
        pygame.draw.rect(screen, (100, 100, 255), (WIN_W - 320, 20, health_width, 30))
        name_text = font.render("SASUKE", True, (255, 255, 255))
        screen.blit(name_text, (WIN_W - 315, 25))
        
        # Barre de stamina Sasuke (en dessous de la vie)
        pygame.draw.rect(screen, (30, 30, 30), (WIN_W - 320, 55, 300, 15))
        stamina_width = int(300 * (sasuke.block_stamina / sasuke.block_stamina_max))
        stamina_color = (100, 200, 255) if sasuke.block_stamina > 30 else (255, 50, 50)
        pygame.draw.rect(screen, stamina_color, (WIN_W - 320, 55, stamina_width, 15))
        
        # Afficher game over
        if game_over:
            overlay = pygame.Surface((WIN_W, WIN_H))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            winner_text = big_font.render(f"{winner} GAGNE !", True, (255, 215, 0))
            winner_rect = winner_text.get_rect(center=(WIN_W // 2, WIN_H // 2 - 30))
            screen.blit(winner_text, winner_rect)
            
            restart_text = font.render("Appuie sur R pour recommencer", True, (255, 255, 255))
            restart_rect = restart_text.get_rect(center=(WIN_W // 2, WIN_H // 2 + 30))
            screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
