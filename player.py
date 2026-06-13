import os

import pygame


# Facteur d'échelle : la map est en zoom x2, les tiles font 16px → 32px affichés.
# On applique le même facteur au sprite pour qu'il soit cohérent visuellement.
DISPLAY_SCALE = 2


class Player(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super().__init__()
        base_dir = os.path.dirname(__file__)

        walk_path = os.path.join(
            base_dir,
            "Sunnyside_World_ASSET_PACK_V2.1",
            "Sunnyside_World_Assets",
            "Characters",
            "Human",
            "WALKING",
            "base_walk_strip8.png",
        )
        axe_path = os.path.join(
            base_dir,
            "Sunnyside_World_ASSET_PACK_V2.1",
            "Sunnyside_World_Assets",
            "Characters",
            "Human",
            "AXE",
            "base_axe_strip10.png",
        )

        self.sprite_sheet = self._load_sprite_sheet(walk_path)
        self.attack_sheet = self._load_sprite_sheet(axe_path)

        self.walk_frame_w = self.sprite_sheet.get_width() // 8 if self.sprite_sheet else 96
        self.walk_frame_h = self.sprite_sheet.get_height() if self.sprite_sheet else 64
        self.attack_frame_w = self.attack_sheet.get_width() // 10 if self.attack_sheet else 96
        self.attack_frame_h = self.attack_sheet.get_height() if self.attack_sheet else 64

        self.frame_index = 0
        self.frame_timer = 0.0
        self.frame_delay = 0.10
        self.moving = False
        self.attacking = False
        self.attack_frame_index = 0
        self.attack_timer = 0.0
        self.attack_delay = 0.06
        self.attack_frames = 10
        self.animation_frames = 8

        # Rect de collision : toujours 16x16 (taille d'une tile)
        self.collision_size = (16, 16)
        self.position = [float(x), float(y)]
        self.rect = pygame.Rect(x, y, *self.collision_size)

        # feet : collision au sol
        self.feet = pygame.Rect(0, 0, self.collision_size[0] * 0.5, 8)
        self.feet.midbottom = self.rect.midbottom

        self.old_position = self.position.copy()
        self.speed = 3

        # Image initiale
        self.image = self._get_walk_frame(0)

    # ------------------------------------------------------------------
    # Chargement
    # ------------------------------------------------------------------

    def _load_sprite_sheet(self, path):
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

    # ------------------------------------------------------------------
    # Extraction de frames
    # ------------------------------------------------------------------

    def _extract_frame(self, sheet, frame_index, frame_w, frame_h):
        """Extrait une frame brute du sprite sheet."""
        if sheet is None:
            return pygame.Surface((16, 16), pygame.SRCALPHA)
        try:
            frame = sheet.subsurface((frame_index * frame_w, 0, frame_w, frame_h)).copy()
            # Supprime le fond noir (colorkey)
            frame.set_colorkey((0, 0, 0))
            # Crop sur le bounding rect réel
            bounds = frame.get_bounding_rect()
            if bounds.width > 0 and bounds.height > 0:
                cropped = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
                cropped.blit(frame, (0, 0), bounds)
                return cropped
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        except (pygame.error, ValueError):
            return pygame.Surface((16, 16), pygame.SRCALPHA)

    def _scale(self, surface):
        """Applique le facteur d'échelle display."""
        w = max(1, surface.get_width() * DISPLAY_SCALE)
        h = max(1, surface.get_height() * DISPLAY_SCALE)
        return pygame.transform.scale(surface, (w, h))

    def _get_walk_frame(self, index):
        frame = self._extract_frame(self.sprite_sheet, index, self.walk_frame_w, self.walk_frame_h)
        return self._scale(frame)

    def _get_attack_frame(self, index):
        frame = self._extract_frame(self.attack_sheet, index, self.attack_frame_w, self.attack_frame_h)
        return self._scale(frame)

    # ------------------------------------------------------------------
    # Interface publique
    # ------------------------------------------------------------------

    def get(self):
        """Retourne l'image courante (pour l'icône de fenêtre, etc.)"""
        return self._get_walk_frame(0)

    def attack(self):
        if self.attacking:
            return
        self.attacking = True
        self.attack_frame_index = 0
        self.attack_timer = 0.0

    def save_location(self):
        self.old_position = self.position.copy()

    def move_player(self, direction):
        self.moving = True
        if direction == "up":
            self.position[1] -= self.speed
        elif direction == "down":
            self.position[1] += self.speed
        elif direction == "right":
            self.position[0] += self.speed
        elif direction == "left":
            self.position[0] -= self.speed

        self.rect.topleft = (int(self.position[0]), int(self.position[1]))
        self.feet.midbottom = self.rect.midbottom

    def move_back(self):
        self.position = self.old_position.copy()
        self.rect.topleft = (int(self.position[0]), int(self.position[1]))
        self.feet.midbottom = self.rect.midbottom
        self.update()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt=0.016):
        # --- Attaque ---
        if self.attacking:
            self.attack_timer += dt
            if self.attack_timer >= self.attack_delay:
                self.attack_timer = 0.0
                self.attack_frame_index += 1
                if self.attack_frame_index >= self.attack_frames:
                    self.attacking = False
                    self.attack_frame_index = 0

            if self.attacking:
                self.image = self._get_attack_frame(self.attack_frame_index)
            else:
                self.image = self._get_walk_frame(0)

        # --- Marche ---
        elif self.moving:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_delay:
                self.frame_timer = 0.0
                self.frame_index = (self.frame_index + 1) % self.animation_frames
            self.image = self._get_walk_frame(self.frame_index)

        # --- Idle ---
        else:
            self.frame_timer = 0.0
            self.image = self._get_walk_frame(0)

        # Le rect de collision reste TOUJOURS 16x16, ancré sur position
        self.rect = pygame.Rect(int(self.position[0]), int(self.position[1]), *self.collision_size)
        self.feet.midbottom = self.rect.midbottom
