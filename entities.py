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

        # Weapon controls (updated bindings: A-melee, W-straight, D-aimed)
        if keys[pygame.K_a]:  # Melee attack
            hit_enemies = self.melee_attack(self.enemies, obstacles)
            if hit_enemies:
                print(f"Hit {len(hit_enemies)} enemies!")
        
        if keys[pygame.K_w]:  # Straight projectile
            projectile = self.shoot_projectile()
            if projectile:
                self.projectile_manager.add_projectile(projectile)
        
        if keys[pygame.K_c]:  # Aimed projectile
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


# ===== ENEMY CLASSES =====

class Enemy:
    """Base enemy class with different AI behaviors"""
    
    def __init__(self, x, y, ai_type="idle"):
        self.rect = pygame.Rect(x, y, 48, 48)
        self.x = x
        self.y = y
        self.health = 100
        self.max_health = 100
        self.speed = 2
        self.ai_type = ai_type
        self.alive = True
        self.direction = 1
        self.ai_timer = 0
        self.target = None
        self.patrol_start = x
        self.patrol_range = 200
        self.attack_range = 150
        self.attack_cooldown = 0
        self.melee_range = 60
        self.color = (255, 100, 100)  # Red color for now
        
        # Enemy projectiles
        self.projectiles = []
        
        # Create a simple colored surface as placeholder
        self.image = pygame.Surface((48, 48))
        self.image.fill(self.color)
        
    def update(self, player, dt=1.0):
        """Update enemy based on AI type"""
        if not self.alive:
            return
            
        self.ai_timer += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        # Different AI behaviors
        if self.ai_type == "idle":
            self._ai_idle(player, dt)
        elif self.ai_type == "patrol":
            self._ai_patrol(player, dt)
        elif self.ai_type == "chase":
            self._ai_chase(player, dt)
        elif self.ai_type == "ranged":
            self._ai_ranged(player, dt)
        elif self.ai_type == "boss":
            self._ai_boss(player, dt)
        
        # Update enemy projectiles
        for projectile in self.projectiles[:]:
            projectile['x'] += projectile['dx'] * dt
            projectile['y'] += projectile['dy'] * dt
            
            # Remove projectiles that go off screen
            if (projectile['x'] < -50 or projectile['x'] > 1010 or 
                projectile['y'] < -50 or projectile['y'] > 700):
                self.projectiles.remove(projectile)
                continue
            
            # Check collision with player
            proj_rect = pygame.Rect(projectile['x'], projectile['y'], 8, 8)
            if proj_rect.colliderect(player.rect):
                self.damage_player(player)
                self.projectiles.remove(projectile)
    
    def _ai_idle(self, player, dt):
        """Enemy stays in place, occasionally looks around"""
        if self.ai_timer > 120:  # Every 2 seconds at 60fps
            self.direction *= -1
            self.ai_timer = 0
    
    def _ai_patrol(self, player, dt):
        """Enemy patrols back and forth"""
        self.rect.x += self.speed * self.direction * dt
        
        # Turn around at patrol boundaries
        if self.rect.x <= self.patrol_start - self.patrol_range or \
           self.rect.x >= self.patrol_start + self.patrol_range:
            self.direction *= -1
    
    def _ai_chase(self, player, dt):
        """Enemy chases the player"""
        distance = abs(player.rect.centerx - self.rect.centerx)
        
        if distance < 300:  # Chase range
            if player.rect.centerx < self.rect.centerx:
                self.direction = -1
                self.rect.x -= self.speed * dt
            else:
                self.direction = 1
                self.rect.x += self.speed * dt
            
            # Melee attack if close enough
            if distance < self.melee_range and self.attack_cooldown <= 0:
                self._attack_melee(player)
                self.attack_cooldown = 90  # 1.5 second cooldown
    
    def _ai_ranged(self, player, dt):
        """Enemy keeps distance and attacks from range"""
        distance = abs(player.rect.centerx - self.rect.centerx)
        
        if distance < 100:  # Too close, back away
            if player.rect.centerx < self.rect.centerx:
                self.direction = 1
                self.rect.x += self.speed * dt
            else:
                self.direction = -1
                self.rect.x -= self.speed * dt
        elif distance > 200:  # Too far, move closer
            if player.rect.centerx < self.rect.centerx:
                self.direction = -1
                self.rect.x -= self.speed * dt
            else:
                self.direction = 1
                self.rect.x += self.speed * dt
        
        # Attack if in range
        if self.attack_range < distance < 250 and self.attack_cooldown <= 0:
            self._attack_ranged(player)
            self.attack_cooldown = 120  # 2 second cooldown
    
    def _ai_boss(self, player, dt):
        """Advanced boss AI with multiple phases"""
        distance = abs(player.rect.centerx - self.rect.centerx)
        
        # Phase based on health
        if self.health > self.max_health * 0.7:
            # Phase 1: Slow chase
            self._ai_chase(player, dt * 0.5)
        elif self.health > self.max_health * 0.3:
            # Phase 2: Fast ranged attacks
            self._ai_ranged(player, dt * 1.5)
            if self.attack_cooldown <= 0:
                self._attack_ranged(player)
                self.attack_cooldown = 60  # Faster attacks
        else:
            # Phase 3: Desperate rush
            self._ai_chase(player, dt * 2.0)
    
    def _attack_ranged(self, player):
        """Fire projectile at player"""
        # Calculate direction to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = (dx**2 + dy**2)**0.5
        
        if distance > 0:
            # Normalize direction
            dx /= distance
            dy /= distance
            
            # Create projectile
            projectile = {
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'dx': dx * 4,  # Projectile speed
                'dy': dy * 4
            }
            self.projectiles.append(projectile)
            print(f"Enemy fired projectile at player!")
    
    def _attack_melee(self, player):
        """Melee attack against player"""
        self.damage_player(player)
        print(f"Enemy melee attack!")
    
    def damage_player(self, player):
        """Deal damage to player"""
        if not hasattr(player, 'invulnerable') or not player.invulnerable:
            player.lives -= 1
            if hasattr(player, 'iFrame'):
                player.iFrame()
            print(f"Player hit by enemy! Lives remaining: {player.lives}")
            if player.lives <= 0:
                print("Player defeated!")
    
    def set_ai_type(self, ai_type):
        """Change enemy AI behavior"""
        self.ai_type = ai_type
        self.ai_timer = 0
        print(f"Enemy AI changed to: {ai_type}")
    
    def take_damage(self, damage):
        """Handle taking damage"""
        self.health -= damage
        if self.health <= 0:
            self.alive = False
            print(f"Enemy defeated!")
    
    def draw(self, surface, debug_mode=False):
        """Draw enemy with optional debug info"""
        if not self.alive:
            return
            
        # Draw enemy
        surface.blit(self.image, self.rect)
        
        # Draw enemy projectiles
        for projectile in self.projectiles:
            pygame.draw.circle(surface, (255, 0, 0), 
                             (int(projectile['x']), int(projectile['y'])), 4)
        
        # Draw health bar
        if self.health < self.max_health:
            bar_width = 48
            bar_height = 4
            bar_x = self.rect.x
            bar_y = self.rect.y - 10
            
            # Background (red)
            pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            # Foreground (green)
            health_width = int((self.health / self.max_health) * bar_width)
            pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))
        
        # Debug info
        if debug_mode:
            # Draw AI type
            font = pygame.font.Font(None, 24)
            text = font.render(self.ai_type, True, (255, 255, 255))
            surface.blit(text, (self.rect.x, self.rect.y - 30))
            
            # Draw direction indicator
            pygame.draw.line(surface, (255, 255, 0), 
                           self.rect.center, 
                           (self.rect.centerx + self.direction * 30, self.rect.centery), 3)
            
            # Draw attack ranges
            if self.ai_type in ["chase", "ranged", "boss"]:
                pygame.draw.circle(surface, (255, 255, 0), self.rect.center, self.melee_range, 1)
                pygame.draw.circle(surface, (255, 100, 100), self.rect.center, self.attack_range, 1)

class Powerup:
    """Base powerup class"""
    
    def __init__(self, x, y, powerup_type="health"):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.powerup_type = powerup_type
        self.collected = False
        self.bob_timer = 0
        self.original_y = y
        
        # Different colors for different powerup types
        colors = {
            "health": (255, 0, 0),      # Red
            "speed": (0, 255, 0),       # Green
            "damage": (255, 255, 0),    # Yellow
            "shield": (0, 0, 255),      # Blue
            "ammo": (255, 0, 255)       # Magenta
        }
        
        self.color = colors.get(powerup_type, (255, 255, 255))
        self.image = pygame.Surface((32, 32))
        self.image.fill(self.color)
    
    def update(self, player, dt=1.0):
        """Update powerup (bobbing animation, collision detection)"""
        if self.collected:
            return
            
        # Bobbing animation
        self.bob_timer += dt * 0.1
        self.rect.y = self.original_y + int(pygame.math.sin(self.bob_timer) * 5)
        
        # Check collision with player
        if self.rect.colliderect(player.rect):
            self.apply_effect(player)
            self.collected = True
    
    def apply_effect(self, player):
        """Apply powerup effect to player"""
        print(f"Player collected {self.powerup_type} powerup!")
        
        if self.powerup_type == "health":
            player.lives = min(player.lives + 1, 10)  # Max 10 lives
        elif self.powerup_type == "speed":
            # Apply speed boost effect
            pass
        elif self.powerup_type == "damage":
            # Apply damage boost effect
            pass
        elif self.powerup_type == "shield":
            # Apply shield effect
            pass
        elif self.powerup_type == "ammo":
            # Restore ammo
            pass
    
    def draw(self, surface):
        """Draw powerup"""
        if not self.collected:
            surface.blit(self.image, self.rect)
