import pygame
import random
import glob
import os
from blocks import Spikes, block
from weapons.weapons import WeaponSystem, handle_projectile_collisions
from weapons.projectiles import ProjectileManager


def rescaleObject(object, scale_factor):
    scaledObject = pygame.transform.scale_by(object, scale_factor)
    return scaledObject

# ===== Sprite Animation System =====
COLS, ROWS = 4, 2
CELL_MAP = {
    "idle": (0, 0),
    "run": (1, 0),
    "jump_start": (2, 0),
    "jump": (3, 0),
    "jump_to_fall": (0, 1),
    "fall": (1, 1),
    "wall_jump": (2, 1),
    "attack": [(0,0), (1,0), (2,0), (3,0), (0,1), (1,1), (2,1), (3,1)],
    "charge": [(0,0), (1,0), (2,0), (3,0), (0,1), (1,1), (2,1), (3,1)]
}

def load_surface(path: str) -> pygame.Surface:
    return pygame.image.load(path).convert_alpha()

def slice_cell(sheet: pygame.Surface, col: int, row: int) -> pygame.Surface:
    w = sheet.get_width() // COLS
    h = sheet.get_height() // ROWS
    rect = pygame.Rect(col * w, row * h, w, h)
    cell = sheet.subsurface(rect).copy()
    return pygame.transform.scale(cell, (72, 72 ))

def build_state_animations(pattern: str):
    paths = glob.glob(pattern)
    if not paths:
        print(f"No sprite sheets found for: {pattern}")
        return None
    
    def num_key(p):
        name = os.path.splitext(os.path.basename(p))[0]
        try:
            return int(name)
        except ValueError:
            return name
    
    paths = sorted(paths, key=num_key)
    sheets = [load_surface(p) for p in paths]
    
    anims = {state: [] for state in CELL_MAP.keys()}
    for sh in sheets:
        for state, coords in CELL_MAP.items():
            if isinstance(coords, list):
                # Handle multi-frame animations like attack/charge
                for (c, r) in coords:
                    anims[state].append(slice_cell(sh, c, r))
            else:
                # Handle single frame animations like idle/run
                c, r = coords
                anims[state].append(slice_cell(sh, c, r))
    return anims

class mainCharacter(WeaponSystem):
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
        # Initialize weapon system
        self.init_weapon_system()
        
        # Initialize internal projectile manager
        self.projectile_manager = ProjectileManager()
        self.enemies = []  # Can be populated later
        
        # Load sprite animations
        self.anims = build_state_animations("assets/catspritesheet/*.png")
        if self.anims:
            self.image = self.anims["idle"][0]

        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        
        # Animation variables
        self.anim_tick = 0
        self.anim_speed = 10
        self.facing_right = True
        self.scroll_speed = 0
        
        # Physics variables
        self.y_gravity = 0.7
        self.jump_height = 12
        self.y_velocity = 0
        self.jumping = False
        self.on_ground = True
        
        # Game variables
        self.visible = True
        self.invulnerable = False
        self.lives = 10
        self.won = False
        


    def _anim_index(self, state: str) -> int:
        if not self.anims or state not in self.anims:
            return 0
        frames = self.anims[state]
        if not frames:
            return 0
        return (self.anim_tick // self.anim_speed) % len(frames)

    def update_animation(self, keys):
        self.anim_tick = (self.anim_tick + 1) % 10_000_000
    
        # Check if weapon should override animation
        weapon_anim = self.get_current_weapon_animation_state()
        if weapon_anim:
            # Use weapon animation instead of movement animation
            state = weapon_anim
        else:
            # Default movement-based animation logic
            if not self.on_ground:
                if self.y_velocity < 0:
                    state = "jump"
                else:
                    state = "fall"
            else:
                if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                    state = "run"
                    if keys[pygame.K_LEFT]:
                        self.facing_right = False
                    elif keys[pygame.K_RIGHT]:
                        self.facing_right = True
                else:
                    state = "idle"
                    self.scroll_speed = 0
        

        idx = self._anim_index(state)
        img = self.anims[state][idx]
        
        self.image = img if self.facing_right else pygame.transform.flip(img, True, False) 
    
    def move(self, dx, dy, obstacles=None):
        old_x, old_y = self.rect.x, self.rect.y
        
        # Handle horizontal movement
        if dx != 0:
            self.rect.x += dx
            if obstacles and self.check_horizontal_collision(obstacles):
                self.rect.x = old_x
                
        # Handle vertical movement
        if dy != 0:
            self.rect.y += dy
            if obstacles and self.check_vertical_collision(obstacles):
                self.rect.y = old_y
                

    def check_horizontal_collision(self, obstacles):
        from blocks import block, Spikes, end
        for obstacle in obstacles:
            if isinstance(obstacle, (Spikes, end)):
                obstacle.collideHurt(self)
            if self.rect.colliderect(obstacle.get_rect()):
                
                return True
        return False
    
    def check_vertical_collision(self, obstacles):
        from blocks import block, Spikes, end
        for obstacle in obstacles:
            if isinstance(obstacle, (Spikes, end)):
                obstacle.collideHurt(self)
            if self.rect.colliderect(obstacle.get_rect()):
                
                return True
        return False

    def jump(self):
        if self.on_ground:  # Only jump from ground
            self.on_ground = False
            self.jumping = True
            self.y_velocity = -self.jump_height
            if self.anims:
                self.image = self.anims["jump_start"][0]  
        
    def update(self, keys, obstacles):
        # Update weapon system before movement
        self.update_weapon_system()
        
        if keys[pygame.K_LEFT]:
            self.move(-3.5, 0, obstacles)
            self.scroll_speed = -0.5
        if keys[pygame.K_RIGHT]:
            self.move(3.5, 0, obstacles)
            self.scroll_speed = 0.5
        if keys[pygame.K_UP]:
            self.jump()
        if keys[pygame.K_DOWN]:
            self.move(0, 3.5, obstacles)

        # Weapon controls (handled internally)
        if keys[pygame.K_f]:  # Melee attack
            hit_enemies = self.melee_attack(self.enemies, obstacles)
            if hit_enemies:
                print(f"Hit {len(hit_enemies)} enemies!")
        
        if keys[pygame.K_g]:  # Shoot fish projectile
            projectile = self.shoot_projectile()
            if projectile:
                self.projectile_manager.add_projectile(projectile)
        
        if keys[pygame.K_j]:  # Charge attack
            if not self.is_charging:
                self.start_charging()
        else:
            if self.is_charging:
                # Get mouse position for aiming
                try:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    projectile = self.stop_charging_and_shoot(mouse_x, mouse_y)
                    if projectile:
                        self.projectile_manager.add_projectile(projectile)
                except:
                    # Fallback if mouse position unavailable
                    self.stop_charging()

        # Update animation based on current state
        self.update_animation(keys)
        
        # Apply physics (gravity and movement)
        self.applyGrav(obstacles)
        
        # Update weapon system
        self.projectile_manager.update()
        
        # Handle projectile collisions
        handle_projectile_collisions(
            self.projectile_manager,
            self,
            self.enemies,
            obstacles
        )
        

        
    def check_collision(self, obstacles):    
        for block in obstacles:
            if isinstance(block, Spikes):
                block.collideHurt(self)
            if self.rect.colliderect(block.get_rect()):
                # Check if falling down and hitting top of block (landing)
                if self.y_velocity > 0:
                    # print("Touched Ground")
                    self.rect.bottom = block.get_rect().top
                    self.jumping = False
                    self.on_ground = True
                    self.y_velocity = 0
                    if not self.anims:
                        self.image = pygame.image.load("mc.png")
                    return True
                
                # Check if moving up and hitting bottom of block (head bump)
                elif self.y_velocity < 0:
                    print("Hit ceiling")
                    self.rect.top = block.get_rect().bottom
                    self.y_velocity = 0
                    return True
        
        # If no collision detected and player was on ground, they're now falling
        if self.on_ground:
            # Check if player is still touching ground
            ground_check = pygame.Rect(self.rect.x, self.rect.y + 1, self.rect.width, self.rect.height)
            still_on_ground = False
            for block in obstacles:
                if ground_check.colliderect(block.get_rect()):
                    still_on_ground = True
                    break
            
            if not still_on_ground:
                print("Started falling")
                self.on_ground = False
        
        return False

    def applyGrav(self, obstacles):
        # Apply gravity to velocity
        if not self.check_vertical_collision(obstacles):
            self.on_ground = False
        if not self.on_ground:
            self.y_velocity += self.y_gravity
        
        # Apply velocity to position
        if self.y_velocity != 0:
            self.rect.y += self.y_velocity
            self.check_collision(obstacles)
            
    def iFrame(self):
        print("You've been hit!!")
        self.invulnerable = True
        self.invulnerable_start = pygame.time.get_ticks()

    def draw(self, surface):
        # Handle invulnerability timing
        if self.invulnerable:
            now = pygame.time.get_ticks()
            if now - self.invulnerable_start >= 2000:  # CHANGE INVI TIMING HERE
                self.invulnerable = False
            
            blink_interval = 100
            time_since_start = now - self.invulnerable_start
            should_show = (time_since_start // blink_interval) % 2 == 0
            
            if should_show and self.visible:
                surface.blit(self.image, self.rect)
        else:
            if self.visible:
                surface.blit(self.image, self.rect)
        
        # Draw weapon effects on top of sprite
        camera_offset = (0, 0)  # Replace with your actual camera offset if you have one
        self.draw_weapon_effects(surface, camera_offset)
        
        # Draw projectiles
        self.projectile_manager.draw(surface)
            
    def get_position(self):
        return self.rect.topleft
    
