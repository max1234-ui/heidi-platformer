import pygame
import sys
import os
import math

pygame.init()
pygame.mixer.init()

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 60
TILE_SIZE = 50

def load_and_clean_image(file_path, size=None, remove_white=True):
    if os.path.exists(file_path):
        img = pygame.image.load(file_path).convert_alpha()
        if remove_white:
            width, height = img.get_size()
            for x in range(width):
                for y in range(height):
                    color = img.get_at((x, y))
                    if color.r > 230 and color.g > 230 and color.b > 230:
                        img.set_at((x, y), (255, 255, 255, 0))
        if size:
            img = pygame.transform.scale(img, size)
        return img
    return None

def load_sound(filename):
    path = os.path.join("assets", filename)
    if os.path.exists(path):
        return pygame.mixer.Sound(path)
    return None

class Prize:
    def __init__(self, x, y, filename, name):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 50
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.collected = False
        self.name = name

        path = os.path.join("assets", filename)
        self.image = load_and_clean_image(path, (self.width, self.height), remove_white=True)

    def draw(self, surface, camera_x):
        if not self.collected and self.image:
            surface.blit(self.image, (self.rect.x - camera_x, self.rect.y))

class CatHeidi:
    def __init__(self, x, y):
        self.width = 75
        self.height = 75
        self.rect = pygame.Rect(x, y, self.width, self.height)

        self.x_velocity = 0
        self.y_velocity = 0
        self.speed = 7
        self.jump_force = -16
        self.gravity = 0.75
        self.is_grounded = False
        self.grounded_plat = None

        self.facing_right = False

        self.frames = []
        for filename in ["heidi.png", "heidi1.png"]:
            path = os.path.join("assets", filename)
            frame = load_and_clean_image(path, (self.width, self.height), remove_white=True)
            if frame:
                self.frames.append(frame)

        self.current_frame = 0
        self.animation_timer = 0
        self.animation_speed = 8

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self.x_velocity = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x_velocity = -self.speed
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x_velocity = self.speed
            self.facing_right = True

    def jump(self):
        if self.is_grounded:
            self.y_velocity = self.jump_force
            self.is_grounded = False
            self.grounded_plat = None
            return True
        return False

    def update(self, current_room, ground_level, platforms, max_world_x):
        plat_dx = 0
        plat_dy = 0
        if self.is_grounded and self.grounded_plat and self.grounded_plat in platforms:
            plat_dx = self.grounded_plat.get("dx", 0)
            plat_dy = self.grounded_plat.get("dy", 0)

        self.rect.x += self.x_velocity + plat_dx

        if self.rect.left < 0:
            self.rect.left = 0
        elif self.rect.right > max_world_x:
            self.rect.right = max_world_x

        if current_room == 2:
            for plat in platforms:
                if plat["type"] == "dirt" and self.rect.colliderect(plat["rect"]):
                    if self.x_velocity + plat_dx > 0:  
                        self.rect.right = plat["rect"].left
                    elif self.x_velocity + plat_dx < 0:  
                        self.rect.left = plat["rect"].right

        self.y_velocity += self.gravity
        self.rect.y += self.y_velocity + plat_dy
        
        self.is_grounded = False
        self.grounded_plat = None

        if current_room == 1:
            if self.rect.bottom >= ground_level:
                self.rect.bottom = ground_level
                self.y_velocity = 0
                self.is_grounded = True
        else:
            for plat in platforms:
                if self.rect.colliderect(plat["rect"]):
                    if plat["type"] == "dirt":
                        if self.y_velocity + plat_dy >= 0:  
                            self.rect.bottom = plat["rect"].top
                            self.y_velocity = 0
                            self.is_grounded = True
                            self.grounded_plat = plat
                        elif self.y_velocity + plat_dy < 0:  
                            self.rect.top = plat["rect"].bottom
                            self.y_velocity = 0  
                            
                    elif plat["type"] == "platform":
                        if self.y_velocity + plat_dy >= 0: 
                            if self.rect.bottom - (self.y_velocity + plat_dy) <= plat["rect"].top + 30:
                                self.rect.bottom = plat["rect"].top
                                self.y_velocity = 0
                                self.is_grounded = True
                                self.grounded_plat = plat

        if self.x_velocity != 0 and self.is_grounded and len(self.frames) >= 2:
            self.animation_timer += 1
            if self.animation_timer >= self.animation_speed:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.frames)
        else:
            self.current_frame = 0
            self.animation_timer = 0

    def draw(self, surface, camera_x):
        if self.frames:
            image_to_draw = self.frames[self.current_frame]
            if self.facing_right:
                image_to_draw = pygame.transform.flip(image_to_draw, True, False)

            surface.blit(image_to_draw, (self.rect.x - camera_x, self.rect.y))

def draw_platform(surface, plat, camera_x, tile_img, dirt_img, corner_img, platform_img):
    plat_rect = plat["rect"]
    cols = plat_rect.width // TILE_SIZE
    rows = plat_rect.height // TILE_SIZE

    for r in range(rows):
        for c in range(cols):
            tile_x = plat_rect.x + (c * TILE_SIZE)
            tile_y = plat_rect.y + (r * TILE_SIZE)
            draw_pos = (tile_x - camera_x, tile_y)

            if plat["type"] == "platform":
                if platform_img:
                    surface.blit(platform_img, draw_pos)
            else:
                is_top = (r == 0)
                is_left = (c == 0)

                if is_top and is_left and corner_img:
                    surface.blit(corner_img, draw_pos)
                elif is_top and tile_img:
                    surface.blit(tile_img, draw_pos)
                elif dirt_img:
                    surface.blit(dirt_img, draw_pos)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Heidi's Platformer")
    clock = pygame.time.Clock()

    jump_sound = load_sound("jump.wav")
    collect_sound = load_sound("collect.wav")
    death_sound = load_sound("death.wav")
    
    bgm_path = os.path.join("assets", "bgm.wav") 
    if os.path.exists(bgm_path):
        try:
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"Error loading background music: {e}")

    bg_path = os.path.join("assets", "bg.png")
    bg_image = pygame.image.load(bg_path).convert()
    bg_image = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    bg2_path = os.path.join("assets", "bg2.png")
    bg2_image = pygame.image.load(bg2_path).convert()
    bg2_image = pygame.transform.scale(bg2_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    BG2_MULTIPLIER = 12
    BG2_WIDTH = SCREEN_WIDTH * BG2_MULTIPLIER

    backpack_path = os.path.join("assets", "backpack.png")
    backpack_image = load_and_clean_image(backpack_path, (60, 60), remove_white=True)
    backpack_rect = pygame.Rect(SCREEN_WIDTH - 80, 20, 60, 60)

    backpackhud_path = os.path.join("assets", "backpackhud.png")
    backpackhud_image = load_and_clean_image(backpackhud_path, (700, 600), remove_white=True)
    backpackhud_x = (SCREEN_WIDTH - 700) // 2
    backpackhud_y = (SCREEN_HEIGHT - 600) // 2

    death_path = os.path.join("assets", "death.png")
    death_image = None
    if os.path.exists(death_path):
        death_image = pygame.image.load(death_path).convert()
        death_image = pygame.transform.scale(death_image, (SCREEN_WIDTH, SCREEN_HEIGHT))

    dirttop_image = load_and_clean_image(os.path.join("assets", "dirttop.png"), (TILE_SIZE, TILE_SIZE), remove_white=True)
    dirt_image = load_and_clean_image(os.path.join("assets", "dirt.png"), (TILE_SIZE, TILE_SIZE), remove_white=True)
    dirtcorner_image = load_and_clean_image(os.path.join("assets", "dirtcorner.png"), (TILE_SIZE, TILE_SIZE), remove_white=True)
    platform_image = load_and_clean_image(os.path.join("assets", "platform.png"), (TILE_SIZE, TILE_SIZE), remove_white=True)

    parkour_platforms = [
        {"rect": pygame.Rect(0, 700, 400, 200), "type": "dirt"},
        {"rect": pygame.Rect(550, 650, 150, 50), "type": "platform"},
        {"rect": pygame.Rect(800, 550, 100, 50), "type": "platform"},

        {"rect": pygame.Rect(1000, 450, 200, 450), "type": "dirt"},
        {"rect": pygame.Rect(1300, 400, 150, 50), "type": "platform", "movement": "curve", "center_x": 1500, "center_y": 380, "radius_x": 220, "radius_y": 140, "speed": 0.025, "angle": 0},
        {"rect": pygame.Rect(1850, 400, 200, 500), "type": "dirt"},

        {"rect": pygame.Rect(2150, 300, 150, 50), "type": "platform"},
        {"rect": pygame.Rect(2400, 200, 150, 50), "type": "platform"},
        {"rect": pygame.Rect(2700, 100, 100, 50), "type": "platform"},

        {"rect": pygame.Rect(3000, 400, 250, 500), "type": "dirt"},
        {"rect": pygame.Rect(3350, 550, 100, 50), "type": "platform"},
        {"rect": pygame.Rect(3600, 550, 150, 50), "type": "platform", "movement": "curve", "center_x": 3950, "center_y": 500, "radius_x": 250, "radius_y": 120, "speed": 0.03, "angle": 0},
        {"rect": pygame.Rect(4300, 600, 300, 300), "type": "dirt"},

        {"rect": pygame.Rect(4700, 500, 100, 50), "type": "platform"},
        {"rect": pygame.Rect(4950, 400, 100, 50), "type": "platform"},
        {"rect": pygame.Rect(5200, 300, 100, 50), "type": "platform"},
        {"rect": pygame.Rect(5450, 200, 100, 50), "type": "platform"},
        {"rect": pygame.Rect(5700, 150, 150, 50), "type": "platform", "movement": "linear", "vx": 5, "bounds_x": (5700, 6200)},

        {"rect": pygame.Rect(6400, 150, 300, 750), "type": "dirt"},
        {"rect": pygame.Rect(6800, 300, 150, 50), "type": "platform"},
        {"rect": pygame.Rect(7000, 450, 200, 450), "type": "dirt"},
        
        {"rect": pygame.Rect(7200, 0, 1500, 350), "type": "dirt"},   
        {"rect": pygame.Rect(7200, 650, 1500, 250), "type": "dirt"}, 
        {"rect": pygame.Rect(7600, 550, 100, 100), "type": "dirt"},  
        {"rect": pygame.Rect(7950, 350, 100, 150), "type": "dirt"},  
        {"rect": pygame.Rect(8300, 500, 100, 150), "type": "dirt"},  
        
        {"rect": pygame.Rect(8800, 600, 100, 50), "type": "platform"}, 
        {"rect": pygame.Rect(9000, 500, 150, 50), "type": "platform", "movement": "linear", "vx": 6, "bounds_x": (9000, 9700)}, 

        {"rect": pygame.Rect(9900, 0, 150, 450), "type": "dirt"},    
        {"rect": pygame.Rect(9900, 750, 150, 150), "type": "dirt"},  
        {"rect": pygame.Rect(10450, 0, 150, 150), "type": "dirt"},   
        {"rect": pygame.Rect(10450, 400, 150, 500), "type": "dirt"}, 
        
        {"rect": pygame.Rect(10050, 750, 150, 50), "type": "platform"},
        {"rect": pygame.Rect(10300, 600, 150, 50), "type": "platform"},
        {"rect": pygame.Rect(10050, 450, 150, 50), "type": "platform"},
        {"rect": pygame.Rect(10300, 300, 150, 50), "type": "platform"},

        {"rect": pygame.Rect(10600, 300, 200, 50), "type": "platform"}, 
        {"rect": pygame.Rect(10900, 350, 150, 50), "type": "platform", "movement": "curve", "center_x": 11100, "center_y": 500, "radius_x": 250, "radius_y": 150, "speed": 0.035, "angle": 0},
        {"rect": pygame.Rect(11400, 550, 150, 50), "type": "platform", "movement": "curve", "center_x": 11650, "center_y": 450, "radius_x": 250, "radius_y": 150, "speed": -0.035, "angle": 3.14},
        
        {"rect": pygame.Rect(12000, 600, 100, 300), "type": "dirt"},
        {"rect": pygame.Rect(12250, 500, 100, 400), "type": "dirt"},
        {"rect": pygame.Rect(12500, 400, 100, 500), "type": "dirt"},
        {"rect": pygame.Rect(12750, 300, 100, 600), "type": "dirt"},

        {"rect": pygame.Rect(13050, 450, 1200, 450), "type": "dirt"}
    ]

    prizes = [
        Prize(1100, 300, "prize1.png", "PLA Filament"),
        Prize(1500, 180, "prize2.png", "Electronic Caliper"),
        Prize(2725, 25,  "prize3.png", "Brass Nozzle"), 
        Prize(3950, 320, "prize4.png", "Glue Stick"), 
        Prize(5450, 50,  "prize1.png", "PLA Filament"),
        Prize(6500, 50,  "prize2.png", "Electronic Caliper"),
        Prize(7050, 350, "prize1.png", "PLA Filament"),
        
        Prize(7700, 500, "prize5.png", "PETG Filament"),     
        Prize(9350, 420, "prize3.png", "Brass Nozzle"),      
        Prize(10175, 150, "prize4.png", "Glue Stick"),       
        Prize(11100, 300, "prize1.png", "PLA Filament"),     
        Prize(12750, 200, "prize2.png", "Electronic Caliper"),
        Prize(13800, 350, "prize6.png", "Raspberry Pi")      
    ]

    current_room = 1
    ground_level = 804
    heidi = CatHeidi(150, ground_level - 75)

    fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    fade_surface.fill((0, 0, 0))
    fade_alpha = 0
    transition_state = "NORMAL"
    target_room = 1

    is_dead = False
    inventory_open = False
    font = pygame.font.SysFont(None, 36)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not is_dead:
                if backpack_rect.collidepoint(event.pos):
                    inventory_open = not inventory_open
            elif event.type == pygame.KEYDOWN:
                if is_dead:
                    if event.key == pygame.K_r:
                        current_room = 1
                        heidi.rect.left = 50
                        heidi.rect.bottom = ground_level
                        heidi.y_velocity = 0
                        heidi.x_velocity = 0
                        heidi.grounded_plat = None
                        
                        # Check if Raspberry Pi is in inventory
                        has_raspberry_pi = any(prize.collected and prize.name == "Raspberry Pi" for prize in prizes)
                        
                        # Reset prizes only if Raspberry Pi is NOT in inventory
                        if not has_raspberry_pi:
                            for prize in prizes:
                                prize.collected = False

                        is_dead = False
                elif transition_state == "NORMAL" and not inventory_open:
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        if heidi.jump():
                            if jump_sound:
                                jump_sound.play()

        room_width = SCREEN_WIDTH if current_room == 1 else BG2_WIDTH
        active_platforms = parkour_platforms if current_room == 2 else []

        if not is_dead and transition_state == "NORMAL" and not inventory_open:

            if current_room == 2:
                for plat in active_platforms:
                    plat["dx"] = 0
                    plat["dy"] = 0
                    m_type = plat.get("movement")

                    if m_type == "linear":
                        old_x = plat["rect"].x
                        plat["rect"].x += plat["vx"]
                        if plat["rect"].left <= plat["bounds_x"][0] or plat["rect"].right >= plat["bounds_x"][1]:
                            plat["vx"] *= -1
                        plat["dx"] = plat["rect"].x - old_x

                    elif m_type == "curve":
                        plat["angle"] += plat["speed"]
                        old_x = plat["rect"].x
                        old_y = plat["rect"].y

                        new_x = plat["center_x"] + int(math.cos(plat["angle"]) * plat["radius_x"])
                        new_y = plat["center_y"] + int(math.sin(plat["angle"]) * plat["radius_y"])

                        plat["rect"].x = new_x
                        plat["rect"].y = new_y
                        plat["dx"] = new_x - old_x
                        plat["dy"] = new_y - old_y

            heidi.handle_input()
            heidi.update(current_room, ground_level, active_platforms, room_width)

            if current_room == 2 and heidi.rect.top > SCREEN_HEIGHT and not is_dead:
                is_dead = True
                if death_sound:
                    death_sound.play()

            if current_room == 2:
                for prize in prizes:
                    if not prize.collected and heidi.rect.colliderect(prize.rect):
                        prize.collected = True
                        if collect_sound:
                            collect_sound.play()

            if current_room == 1 and heidi.rect.right >= SCREEN_WIDTH:
                target_room = 2
                transition_state = "FADE_OUT"
            elif current_room == 2 and heidi.rect.left <= 0 and heidi.x_velocity < 0:
                target_room = 1
                transition_state = "FADE_OUT"

        if transition_state == "FADE_OUT":
            fade_alpha += 20
            if fade_alpha >= 255:
                fade_alpha = 255
                current_room = target_room
                if current_room == 2:
                    heidi.rect.left = 50
                    heidi.rect.bottom = 700
                else:
                    heidi.rect.left = SCREEN_WIDTH - heidi.width
                    heidi.rect.bottom = ground_level
                transition_state = "FADE_IN"
        elif transition_state == "FADE_IN":
            fade_alpha -= 20
            if fade_alpha <= 0:
                fade_alpha = 0
                transition_state = "NORMAL"

        camera_x = 0
        if current_room == 2:
            camera_x = heidi.rect.centerx - SCREEN_WIDTH // 2
            camera_x = max(0, min(camera_x, BG2_WIDTH - SCREEN_WIDTH))

        if current_room == 1:
            screen.blit(bg_image, (0, 0))
        else:
            for i in range(BG2_MULTIPLIER):
                tile_bg_x = (i * SCREEN_WIDTH) - camera_x
                screen.blit(bg2_image, (tile_bg_x, 0))

            for plat in parkour_platforms:
                draw_platform(screen, plat, camera_x, dirttop_image, dirt_image, dirtcorner_image, platform_image)

            for prize in prizes:
                prize.draw(screen, camera_x)

        heidi.draw(screen, camera_x)

        if backpack_image:
            screen.blit(backpack_image, backpack_rect.topleft)

        if inventory_open:
            if backpackhud_image:
                screen.blit(backpackhud_image, (backpackhud_x, backpackhud_y))

            item_counts = {}
            item_images = {}
            for prize in prizes:
                if prize.collected:
                    item_counts[prize.name] = item_counts.get(prize.name, 0) + 1
                    if prize.name not in item_images:
                        item_images[prize.name] = prize.image

            start_x = backpackhud_x + 80
            start_y = backpackhud_y + 120
            if item_counts:
                for item_name, count in item_counts.items():
                    img = item_images[item_name]
                    if img:
                        screen.blit(img, (start_x, start_y))
                    item_txt = font.render(f"x{count} {item_name}", True, (255, 255, 255))
                    screen.blit(item_txt, (start_x + 70, start_y + 12))
                    start_y += 70

        if is_dead:
            if death_image:
                screen.blit(death_image, (0, 0))

        if fade_alpha > 0:
            fade_surface.set_alpha(fade_alpha)
            screen.blit(fade_surface, (0, 0))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()