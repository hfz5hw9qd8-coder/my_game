import os

import pygame


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

        self.frame_width = self.sprite_sheet.get_width() // 8 if self.sprite_sheet is not None else 96
        self.frame_height = self.sprite_sheet.get_height() if self.sprite_sheet is not None else 64
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

        self.base_rect_size = (16, 16)
        self.base_rect_size_attack = (32, 32)
        self.image = self.get_image(self.frame_index, target_size=self.base_rect_size)
        self.image.set_colorkey([0, 0, 0])
        self.rect = pygame.Rect(x, y, *self.base_rect_size)
        self.position = [x, y]
        self.images = {
            "up": self.get_image(0, target_size=self.rect.size),
            "down": self.get_image(0, target_size=self.rect.size),
            "right": self.get_image(0, target_size=self.rect.size),
            "left": self.get_image(0, target_size=self.rect.size),
        }
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 12)
        self.old_position = self.position.copy()
        self.speed = 3

    def _load_sprite_sheet(self, path):
        try:
            return pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None

    def get(self):
        self.image = self.images["down"]
        self.image.set_colorkey([0, 0, 0])
        return self.image

    def attack(self):
        if self.attacking:
            return
        self.attacking = True
        self.attack_frame_index = 0
        self.attack_timer = 0.0

    def save_location(self): self.old_position = self.position.copy()

    def move_player(self, type):
        self.moving = True
        if type == "up":
            self.position[1] -= self.speed
        elif type == "down":
            self.position[1] += self.speed
        elif type == "right":
            self.position[0] += self.speed
        elif type == "left":
            self.position[0] -= self.speed

        self.rect = pygame.Rect(self.position[0], self.position[1], *self.base_rect_size)
        self.feet.midbottom = self.rect.midbottom
        self.image = self.get_image(self.frame_index, target_size=self.base_rect_size)
        self.image.set_colorkey([0, 0, 0])


    def update(self, dt=0.016):
        if self.attacking:
            self.attack_timer += dt
            if self.attack_timer >= self.attack_delay:
                self.attack_timer = 0.0
                self.attack_frame_index += 1
                if self.attack_frame_index >= self.attack_frames:
                    self.attacking = False
                    self.attack_frame_index = 0

            if self.attacking:
                frame_image = self.get_image(
                    self.attack_frame_index,
                    sprite_sheet=self.attack_sheet,
                    frame_count=self.attack_frames,
                    target_size_attack=self.base_rect_size_attack,
                )
                canvas = pygame.Surface(self.base_rect_size_attack, pygame.SRCALPHA)
                canvas.blit(frame_image, ((self.base_rect_size_attack[0] - frame_image.get_width()) // 2,
                                          (self.base_rect_size_attack[1] - frame_image.get_height()) // 2))
                self.image = canvas
                self.image.set_colorkey([0, 0, 0])
                self.rect = pygame.Rect(self.position[0], self.position[1], *self.base_rect_size_attack)
            else:
                self.image = self.get_image(0, target_size_attack=self.base_rect_size_attack)
                self.image.set_colorkey([0, 0, 0])
        elif self.moving:
            self.frame_timer += dt
            if self.frame_timer >= self.frame_delay:
                self.frame_timer = 0.0
                self.frame_index = (self.frame_index + 1) % self.animation_frames
            self.image = self.get_image(self.frame_index, target_size=self.rect.size)
            self.image.set_colorkey([0, 0, 0])
        else:
            self.frame_timer = 0.0
            self.image = self.get_image(0, target_size=self.rect.size)
            self.image.set_colorkey([0, 0, 0])

        self.rect = pygame.Rect(self.position[0], self.position[1], *self.base_rect_size)
        self.feet.midbottom = self.rect.midbottom

    def move_back(self):
        self.position = self.old_position
        self.rect.topleft = self.position
        self.feet.midbottom = self.rect.midbottom
        self.update()

    def _has_visible_pixels(self, image):
        return any(image.get_at((x, y))[3] > 0 for x in range(image.get_width()) for y in range(image.get_height()))

    def get_image(self, frame_index, sprite_sheet=None, frame_count=None, target_size=None, target_size_attack=None):
        image = pygame.Surface((96, 64), pygame.SRCALPHA)
        sprite_sheet = sprite_sheet if sprite_sheet is not None else self.sprite_sheet
        frame_count = frame_count if frame_count is not None else self.animation_frames
        frame_width = self.frame_width if sprite_sheet is self.sprite_sheet else (sprite_sheet.get_width() // frame_count)
        frame_height = self.frame_height if sprite_sheet is self.sprite_sheet else sprite_sheet.get_height()
        default_target_size = (16, 16)
        target_size = target_size or default_target_size

        if sprite_sheet is not None:
            try:
                x = frame_index * frame_width
                frame = sprite_sheet.subsurface((x, 0, frame_width, frame_height)).copy()
                bounds = frame.get_bounding_rect()
                if bounds.width and bounds.height:
                    cropped = pygame.Surface((bounds.width, bounds.height), pygame.SRCALPHA)
                    cropped.blit(frame, (0, 0), bounds)
                    scale = min(target_size[0] / max(1, bounds.width), target_size[1] / max(1, bounds.height))
                    scaled_size = (
                        max(1, int(bounds.width * scale)),
                        max(1, int(bounds.height * scale)),
                    )
                    image = pygame.transform.smoothscale(cropped, scaled_size)
                else:
                    image = pygame.Surface((16, 16), pygame.SRCALPHA)
            except (pygame.error, ValueError, TypeError):
                image = pygame.Surface((32, 32), pygame.SRCALPHA)

        if not self._has_visible_pixels(image):
            image = pygame.Surface((16, 16), pygame.SRCALPHA)

        return image