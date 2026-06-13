import os
from xml.etree import ElementTree as ET

import pygame
import pytmx
import pyscroll

from player import Player


class Game:

    def _point_in_polygon(self, point, polygon):
        x, y = point
        inside = False
        n = len(polygon)
        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]
            if ((y1 > y) != (y2 > y)) and (x < (x2 - x1) * (y - y1) / (y2 - y1) + x1):
                inside = not inside
        return inside

    def _rect_fully_inside_polygon(self, rect, polygon):
        points = [
            rect.topleft,
            (rect.right, rect.top),
            rect.bottomright,
            (rect.left, rect.bottom),
        ]
        return all(self._point_in_polygon(point, polygon) for point in points)

    def _build_walls(self, tmx_data):
        walls = []

        try:
            house_layer = tmx_data.get_layer_by_name("houses")
            if isinstance(house_layer, pytmx.TiledTileLayer):
                for x, y, gid in house_layer:
                    if gid:
                        walls.append(
                            ("rect", pygame.Rect(
                                x * tmx_data.tilewidth,
                                y * tmx_data.tileheight,
                                tmx_data.tilewidth,
                                tmx_data.tileheight,
                            ))
                        )
        except (KeyError, AttributeError, TypeError, ValueError):
            pass

        map_path = getattr(tmx_data, "filename", "map.tmx")
        try:
            root = ET.parse(map_path).getroot()
            for obj in root.findall(".//object"):
                if obj.get("name") != "collision":
                    continue

                x = float(obj.get("x", 0))
                y = float(obj.get("y", 0))
                width = float(obj.get("width", 0))
                height = float(obj.get("height", 0))

                template_path = obj.get("template")
                polygon_points = None
                if template_path:
                    template_file = os.path.join(os.path.dirname(map_path), template_path)
                    try:
                        template_root = ET.parse(template_file).getroot()
                        template_obj = template_root.find("object")
                        if template_obj is not None:
                            template_polygon = template_obj.find("polygon")
                            if template_polygon is not None:
                                points = template_polygon.get("points", "")
                                if points:
                                    polygon_points = []
                                    for raw in points.split():
                                        px, py = raw.split(",")
                                        polygon_points.append((x + float(px), y + float(py)))
                    except (ET.ParseError, FileNotFoundError, OSError, ValueError, TypeError):
                        polygon_points = None

                if polygon_points:
                    walls.append(("polygon", polygon_points))
                    continue

                polygon = obj.find("polygon")
                if polygon is not None:
                    points = polygon.get("points", "")
                    if points:
                        pts = []
                        for raw in points.split():
                            px, py = raw.split(",")
                            pts.append((x + float(px), y + float(py)))
                        walls.append(("polygon", pts))
                        continue

                if width or height:
                    walls.append(("rect", pygame.Rect(x, y, width, height)))
        except (ET.ParseError, FileNotFoundError, OSError, ValueError, TypeError):
            pass

        for obj in getattr(tmx_data, "objects", []):
            if getattr(obj, "name", "") == "collision" and (getattr(obj, "width", 0) or getattr(obj, "height", 0)):
                walls.append(("rect", pygame.Rect(obj.x, obj.y, obj.width, obj.height)))

        return walls

    def _get_object(self, tmx_data, name):
        try:
            return tmx_data.get_object_by_name(name)
        except KeyError:
            return None

    def __init__(self):
        # Démarrage
        self.running = True
        self.map = "world"

        # Affichage de la fenêtre
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("BasiqueGame")

        # Charger la carte clasique
        tmx_data = pytmx.util_pygame.load_pygame("map.tmx")
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        # Générer le joeur
        player_position = self._get_object(tmx_data, "player")
        start_x = player_position.x if player_position else 100
        start_y = player_position.y if player_position else 100
        self.player = Player(start_x, start_y)

        # Définir le logo du jeu
        pygame.display.set_icon(self.player.get())

        # Les collisions
        self.walls = self._build_walls(tmx_data)

        # Dessiner les différents calques
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # Porte de la maison
        enter_house = self._get_object(tmx_data, "enter_house")
        if enter_house is not None:
            self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)
        else:
            self.enter_house_rect = pygame.Rect(0, 0, 0, 0)

    def handle_input(self):
        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_ESCAPE]:
            self.running = False
            return

        if pressed[pygame.K_SPACE]:
            self.player.attack()

        moved = False
        if pressed[pygame.K_UP] or pressed[pygame.K_z]:
            self.player.move_player("up")
            moved = True
        elif pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
            self.player.move_player("down")
            moved = True
        elif pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
            self.player.move_player("right")
            moved = True
        elif pressed[pygame.K_LEFT] or pressed[pygame.K_q]:
            self.player.move_player("left")
            moved = True

        if not moved:
            self.player.moving = False

    def switch_house(self):
        if not os.path.exists("house.tmx"):
            return

        self.map = "house"

        # Charger la carte clasique
        tmx_data = pytmx.util_pygame.load_pygame("house.tmx")
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        # Les collisions
        self.walls = self._build_walls(tmx_data)

        # Dessiner les différents calques
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # Porte de la maison
        enter_house = self._get_object(tmx_data, "exit_house")
        if enter_house is not None:
            self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)
        else:
            self.enter_house_rect = pygame.Rect(0, 0, 0, 0)

        # Intérieur
        spawn_house_point = self._get_object(tmx_data, "spawn_house_point")
        if spawn_house_point is not None:
            self.player.position[0] = spawn_house_point.x
            self.player.position[1] = spawn_house_point.y - 20
            self.player.rect.topleft = self.player.position
            self.player.feet.midbottom = self.player.rect.midbottom

    def switch_world(self):
        self.map = "world"

        # Charger la carte clasique
        tmx_data = pytmx.util_pygame.load_pygame("map.tmx")
        map_data = pyscroll.data.TiledMapData(tmx_data)
        map_layer = pyscroll.orthographic.BufferedRenderer(map_data, self.screen.get_size())
        map_layer.zoom = 2

        # Les collisions
        self.walls = self._build_walls(tmx_data)

        # Dessiner les différents calques
        self.group = pyscroll.PyscrollGroup(map_layer=map_layer, default_layer=5)
        self.group.add(self.player)

        # Porte de la maison
        enter_house = self._get_object(tmx_data, "enter_house")
        if enter_house is not None:
            self.enter_house_rect = pygame.Rect(enter_house.x, enter_house.y, enter_house.width, enter_house.height)
        else:
            self.enter_house_rect = pygame.Rect(0, 0, 0, 0)

        # Retour sur la carte monde au bon point de sortie
        spawn_world_point = self._get_object(tmx_data, "enter_house_exit")
        if spawn_world_point is None:
            spawn_world_point = self._get_object(tmx_data, "player")

        if spawn_world_point is not None:
            self.player.position[0] = spawn_world_point.x
            self.player.position[1] = spawn_world_point.y
            self.player.rect.topleft = self.player.position
            self.player.feet.midbottom = self.player.rect.midbottom

    def update(self, dt):
        self.group.update(dt)

        # Vérifier l'entrer de la maison
        if self.map == "world" and self.enter_house_rect and self.player.feet.colliderect(self.enter_house_rect):
            self.switch_house()
            return

        if self.map == "house" and self.enter_house_rect and self.player.feet.colliderect(self.enter_house_rect):
            self.switch_world()
            return
           
        # Vérification des collisions
        for sprite in self.group.sprites():
            feet = sprite.feet
            blocked = False

            for wall_type, wall in self.walls:
                if wall_type == "rect" and feet.colliderect(wall):
                    blocked = True
                    break
                if wall_type == "polygon" and not self._rect_fully_inside_polygon(feet, wall):
                    blocked = True
                    break

            if blocked:
                sprite.move_back()

    def run(self):
        clock = pygame.time.Clock()

        # Clock
        while self.running:
            dt = clock.tick(60) / 1000.0

            self.player.save_location()
            self.handle_input()
            self.update(dt)
            self.group.center(self.player.rect.center)
            self.group.draw(self.screen)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

        pygame.quit()