from main import TMX_DATA
import pygame
import pytmx


def clamp(value, lower, upper):
    return max(lower, min(value, upper))


def load_map(map_path="map.tmx"):
    tmx_data = pytmx.load_pygame(map_path)
    world_width = tmx_data.tilewidth * tmx_data.width
    world_height = tmx_data.tileheight * tmx_data.height
    world_surface = pygame.Surface((world_width, world_height), pygame.SRCALPHA)
    return tmx_data, world_surface, world_width, world_height


def render_map(tmx_data, world_surface):
    world_surface.fill((0, 0, 0))
    for layer in tmx_data.visible_layers:
        if isinstance(layer, pytmx.TiledTileLayer):
            for x, y, gid in layer:
                tile = tmx_data.get_tile_image_by_gid(gid)
                if tile:
                    world_surface.blit(tile, (x * tmx_data.tilewidth, y * tmx_data.tileheight))


def get_camera_rect(player_rect, screen_width, screen_height, zoom_factor, world_width, world_height):
    camera_width = int(screen_width / zoom_factor)
    camera_height = int(screen_height / zoom_factor)
    camera_x = clamp(player_rect.centerx - camera_width // 2, 0, max(0, world_width - camera_width))
    camera_y = clamp(player_rect.centery - camera_height // 2, 0, max(0, world_height - camera_height))
    return pygame.Rect(camera_x, camera_y, camera_width, camera_height)

# definir une liste qui va stocker les rectangles de collision
walls = []

for obj in TMX_DATA.objects:
    if obj.name == "collision":
        walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
