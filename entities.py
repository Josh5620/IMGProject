import pygame
import random
import glob
import os
import math
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
        self.lives = 5
        self.won = False
        
        # Ammo and shooting system
        self.max_ammo = 20
        self.current_ammo = 20
        self.shooting_cooldown = 0
        self.cooldown_time = 30  # 0.5 seconds at 60 FPS
        
        # Powerup effects
        self.speed_boost = 1.0
        self.damage_boost = 1.0
        self.shield_active = False
        self.powerup_timers = {
            "speed": 0,
            "damage": 0,
            "shield": 0
        }
        


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
        
    def update(self, keys, obstacles, enemies):
        # Update weapon system before movement
        self.update_weapon_system()
        self.enemies = enemies  # Update current enemies
        
        # Apply speed boost to movement
        base_speed = 3.5 * self.speed_boost
        if keys[pygame.K_LEFT]:
            self.move(-base_speed, 0, obstacles)
            self.scroll_speed = -0.5
        if keys[pygame.K_RIGHT]:
            self.move(base_speed, 0, obstacles)
            self.scroll_speed = 0.5
        if keys[pygame.K_UP]:
            self.jump()
        if keys[pygame.K_DOWN]:
            self.move(0, 3.5, obstacles)

        # Update shooting cooldown and powerup timers
        if self.shooting_cooldown > 0:
            self.shooting_cooldown -= 1
        
        # Update powerup effects
        self.update_powerup_effects()
        
        # Weapon controls (updated bindings: A-melee, W-straight, C-aimed)
        if keys[pygame.K_a]:  # Melee attack
            hit_enemies = self.melee_attack(self.enemies, obstacles)
            if hit_enemies:
                print(f"Hit {len(hit_enemies)} enemies!")
        
        if keys[pygame.K_s]:  # Straight projectile
            if self.can_shoot():
                projectile = self.shoot_projectile()
                if projectile:
                    self.projectile_manager.add_projectile(projectile)
                    self.consume_ammo()
        
        if keys[pygame.K_c]:  # Aimed projectile
            if not self.is_charging and self.can_shoot():
                self.start_charging()
        else:
            if self.is_charging:
                # Get mouse position for aiming
                try:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    projectile = self.stop_charging_and_shoot(mouse_x, mouse_y)
                    if projectile:
                        self.projectile_manager.add_projectile(projectile)
                        self.consume_ammo()
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
    
    def can_shoot(self):
        """Check if player can shoot (has ammo and not on cooldown)"""
        return self.current_ammo > 0 and self.shooting_cooldown <= 0
    
    def consume_ammo(self):
        """Consume one ammo and set cooldown"""
        if self.current_ammo > 0:
            self.current_ammo -= 1
            self.shooting_cooldown = self.cooldown_time
            print(f"Ammo: {self.current_ammo}/{self.max_ammo}")
    
    def reload_ammo(self, amount=None):
        """Reload ammo (used by ammo powerups)"""
        if amount is None:
            amount = self.max_ammo
        self.current_ammo = min(self.current_ammo + amount, self.max_ammo)
        print(f"Ammo reloaded! {self.current_ammo}/{self.max_ammo}")
    
    def update_powerup_effects(self):
        """Update active powerup effects"""
        for effect, timer in self.powerup_timers.items():
            if timer > 0:
                self.powerup_timers[effect] -= 1
                if self.powerup_timers[effect] <= 0:
                    # Effect expired
                    if effect == "speed":
                        self.speed_boost = 1.0
                        print("Speed boost expired!")
                    elif effect == "damage":
                        self.damage_boost = 1.0
                        print("Damage boost expired!")
                    elif effect == "shield":
                        self.shield_active = False
                        print("Shield expired!")
    
    def apply_powerup(self, powerup_type):
        """Apply powerup effect to player with enhanced feedback"""
        if powerup_type == "health":
            old_lives = self.lives
            self.lives = min(self.lives + 2, 10)  # Restore 2 lives, max 10
            print(f"💖 Health restored! Lives: {old_lives} → {self.lives}")
            # TODO: Play healing sound effect
        
        elif powerup_type == "speed":
            self.speed_boost = 1.5
            self.powerup_timers["speed"] = 600  # 10 seconds at 60 FPS
            print("⚡ Speed boost activated for 10 seconds!")
            # TODO: Play speed boost sound effect
        
        elif powerup_type == "damage":
            self.damage_boost = 2.0
            self.powerup_timers["damage"] = 600  # 10 seconds at 60 FPS
            print("🔥 Damage boost activated for 10 seconds!")
            # TODO: Play power up sound effect
        
        elif powerup_type == "shield":
            self.shield_active = True
            self.powerup_timers["shield"] = 300  # 5 seconds at 60 FPS
            print("🛡️ Shield activated for 5 seconds!")
            # TODO: Play shield activation sound effect
        
        elif powerup_type == "ammo":
            self.reload_ammo(10)  # Restore 10 ammo
            print("📦 Ammo powerup collected!")
            # TODO: Play ammo reload sound effect
    
    def take_damage(self, damage_amount=1):
        """Take damage, with shield protection"""
        if self.invulnerable:
            return False
            
        if self.shield_active:
            print("Shield blocked damage!")
            return False
        
        self.lives -= damage_amount
        if self.lives <= 0:
            self.lives = 0
            print("Player defeated!")
        else:
            # Brief invulnerability after taking damage
            self.iFrame()
            # You might want to add a timer to reset invulnerability
        
        return True
    
    def draw_powerup_effects(self, surface):
        """Draw visual effects for active powerups"""
        player_center = self.rect.center
        current_time = pygame.time.get_ticks()
        
        # Shield effect - pulsing blue protective aura
        if hasattr(self, 'shield_active') and self.shield_active:
            shield_pulse = math.sin(current_time * 0.01) * 0.3 + 0.7
            shield_radius = int(40 * shield_pulse)
            
            # Outer shield glow
            for i in range(3):
                alpha = 60 - i * 15
                radius = shield_radius + i * 3
                shield_color = (0, 150, 255)
                pygame.draw.circle(surface, shield_color, player_center, radius, 2)
            
            # Inner shield core
            pygame.draw.circle(surface, (150, 200, 255), player_center, shield_radius - 8, 1)
        
        # Speed effect - motion blur and energy trails
        if hasattr(self, 'speed_boost') and self.speed_boost > 1.0:
            speed_intensity = min((self.speed_boost - 1.0) * 2, 1.0)
            
            # Energy trails behind player
            for i in range(4):
                trail_x = player_center[0] - (i + 1) * 10 * speed_intensity
                trail_alpha = int(150 * speed_intensity) - i * 30
                if trail_alpha > 0:
                    trail_size = 8 - i * 2
                    pygame.draw.circle(surface, (0, 255, 100), 
                                     (trail_x, player_center[1]), trail_size, 1)
            
            # Speed lines effect
            for i in range(6):
                line_length = 15 + i * 3
                line_y = player_center[1] + (i - 3) * 5
                line_start = (player_center[0] - line_length, line_y)
                line_end = (player_center[0] - 5, line_y)
                pygame.draw.line(surface, (100, 255, 150), line_start, line_end, 2)
        
        # Damage effect - fiery aura and sparks
        if hasattr(self, 'damage_boost') and self.damage_boost > 1.0:
            damage_intensity = min((self.damage_boost - 1.0), 1.0)
            damage_pulse = math.sin(current_time * 0.015) * 0.3 + 0.7
            
            # Fiery aura
            aura_radius = int(35 * damage_pulse * damage_intensity)
            for i in range(3):
                alpha = int(80 * damage_intensity) - i * 20
                if alpha > 0:
                    radius = aura_radius - i * 5
                    color_intensity = int(255 * damage_intensity)
                    aura_color = (color_intensity, max(50, color_intensity - 100), 0)
                    pygame.draw.circle(surface, aura_color, player_center, radius, 1)
            
            # Floating spark particles
            for i in range(8):
                angle = (current_time * 0.02 + i * 45) % 360
                spark_distance = 25 + math.sin(current_time * 0.03 + i) * 8
                spark_x = player_center[0] + int(spark_distance * math.cos(math.radians(angle)))
                spark_y = player_center[1] + int(spark_distance * math.sin(math.radians(angle))) - 5
                
                # Animated spark color
                spark_alpha = int(200 * damage_intensity * (math.sin(current_time * 0.05 + i) * 0.5 + 0.5))
                if spark_alpha > 50:
                    spark_colors = [(255, 200, 0), (255, 100, 0), (255, 50, 0)]
                    spark_color = spark_colors[i % 3]
                    pygame.draw.circle(surface, spark_color, (spark_x, spark_y), 3)
                    pygame.draw.circle(surface, (255, 255, 100), (spark_x, spark_y), 1)
    
    def draw_with_effects(self, surface):
        """Draw player with all visual effects"""
        # Draw powerup effects behind player
        self.draw_powerup_effects(surface)
        
        # Draw the player sprite
        surface.blit(self.image, self.rect)
        

        
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
    """Enhanced powerup class with visual effects"""
    
    def __init__(self, x, y, powerup_type="health"):
        self.rect = pygame.Rect(x, y, 40, 40)  # Slightly bigger
        self.powerup_type = powerup_type
        self.collected = False
        self.bob_timer = 0
        self.original_y = y
        self.rotation = 0
        self.pulse_timer = 0
        self.collection_particles = []
        
        # Enhanced colors with glow effects
        self.colors = {
            "health": {"main": (255, 50, 50), "glow": (255, 100, 100), "bright": (255, 200, 200)},
            "speed": {"main": (50, 255, 50), "glow": (100, 255, 100), "bright": (200, 255, 200)},
            "damage": {"main": (255, 255, 50), "glow": (255, 255, 100), "bright": (255, 255, 200)},
            "shield": {"main": (50, 50, 255), "glow": (100, 100, 255), "bright": (200, 200, 255)},
            "ammo": {"main": (255, 50, 255), "glow": (255, 100, 255), "bright": (255, 200, 255)}
        }
        
        self.color_set = self.colors.get(powerup_type, {
            "main": (255, 255, 255), 
            "glow": (200, 200, 200), 
            "bright": (255, 255, 255)
        })
    
    def update(self, player, dt=1.0):
        """Update powerup with enhanced animations and effects"""
        if self.collected:
            # Update collection particles
            self.update_collection_particles(dt)
            return
            
        # Enhanced bobbing animation
        self.bob_timer += dt * 0.15
        self.rect.y = self.original_y + int(math.sin(self.bob_timer) * 8)
        
        # Rotation animation
        self.rotation += dt * 2
        if self.rotation >= 360:
            self.rotation = 0
        
        # Pulsing effect
        self.pulse_timer += dt * 0.2
        
        # Check collision with player
        if self.rect.colliderect(player.rect):
            self.create_collection_particles()
            self.apply_effect(player)
            self.collected = True
    
    def apply_effect(self, player):
        """Apply powerup effect to player"""
        print(f"✨ Player collected {self.powerup_type} powerup!")
        player.apply_powerup(self.powerup_type)
    
    def create_collection_particles(self):
        """Create particles when powerup is collected"""
        for i in range(15):  # Create 15 particles
            import random
            particle = {
                'x': self.rect.centerx + random.randint(-10, 10),
                'y': self.rect.centery + random.randint(-10, 10),
                'dx': random.uniform(-3, 3),
                'dy': random.uniform(-4, 1),
                'life': 30,  # Frames to live
                'max_life': 30,
                'color': self.color_set["bright"]
            }
            self.collection_particles.append(particle)
    
    def update_collection_particles(self, dt):
        """Update collection particle effects"""
        for particle in self.collection_particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['dy'] += 0.2 * dt  # Gravity
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.collection_particles.remove(particle)
    
    def draw_icon(self, surface, center_x, center_y, size, alpha=255):
        """Draw powerup-specific icon"""
        if self.powerup_type == "health":
            # Draw heart/cross
            cross_size = size // 3
            pygame.draw.rect(surface, (*self.color_set["main"], alpha), 
                           (center_x - cross_size//2, center_y - cross_size, cross_size, cross_size*2))
            pygame.draw.rect(surface, (*self.color_set["main"], alpha), 
                           (center_x - cross_size, center_y - cross_size//2, cross_size*2, cross_size))
        
        elif self.powerup_type == "speed":
            # Draw lightning bolt
            points = [
                (center_x - size//3, center_y - size//2),
                (center_x + size//6, center_y - size//6),
                (center_x - size//6, center_y),
                (center_x + size//3, center_y + size//2),
                (center_x - size//6, center_y + size//6),
                (center_x + size//6, center_y)
            ]
            pygame.draw.polygon(surface, (*self.color_set["main"], alpha), points)
        
        elif self.powerup_type == "damage":
            # Draw sword/star
            for i in range(8):
                angle = i * 45
                x1 = center_x + int((size//4) * math.cos(math.radians(angle)))
                y1 = center_y + int((size//4) * math.sin(math.radians(angle)))
                x2 = center_x + int((size//2) * math.cos(math.radians(angle)))
                y2 = center_y + int((size//2) * math.sin(math.radians(angle)))
                pygame.draw.line(surface, (*self.color_set["main"], alpha), (x1, y1), (x2, y2), 2)
        
        elif self.powerup_type == "shield":
            # Draw shield
            pygame.draw.circle(surface, (*self.color_set["main"], alpha), 
                             (center_x, center_y), size//2, 3)
            pygame.draw.circle(surface, (*self.color_set["glow"], alpha//2), 
                             (center_x, center_y), size//3)
        
        elif self.powerup_type == "ammo":
            # Draw bullet/arrow
            pygame.draw.circle(surface, (*self.color_set["main"], alpha), 
                             (center_x - size//3, center_y), size//4)
            pygame.draw.polygon(surface, (*self.color_set["main"], alpha), [
                (center_x - size//3, center_y - size//6),
                (center_x + size//3, center_y),
                (center_x - size//3, center_y + size//6)
            ])
    
    def draw(self, surface):
        """Draw powerup with enhanced visual effects"""
        if self.collected:
            # Draw collection particles
            for particle in self.collection_particles:
                alpha = int(255 * (particle['life'] / particle['max_life']))
                if alpha > 0:
                    color = (*particle['color'], min(alpha, 255))
                    pygame.draw.circle(surface, color[:3], 
                                     (int(particle['x']), int(particle['y'])), 2)
            return
        
        center_x = self.rect.centerx
        center_y = self.rect.centery
        
        # Calculate pulsing effect
        pulse_scale = 1.0 + math.sin(self.pulse_timer) * 0.2
        glow_radius = int(25 * pulse_scale)
        
        # Draw outer glow (largest)
        glow_color = (*self.color_set["glow"], 30)
        for i in range(3):
            radius = glow_radius - i * 3
            if radius > 0:
                pygame.draw.circle(surface, glow_color[:3], 
                                 (center_x, center_y), radius)
        
        # Draw rotating background circle
        main_radius = int(18 * pulse_scale)
        pygame.draw.circle(surface, self.color_set["main"], 
                         (center_x, center_y), main_radius)
        
        # Draw inner bright circle
        inner_radius = int(12 * pulse_scale)
        pygame.draw.circle(surface, self.color_set["bright"], 
                         (center_x, center_y), inner_radius)
        
        # Draw rotating icon
        icon_size = int(20 * pulse_scale)
        self.draw_icon(surface, center_x, center_y, icon_size)
        
        # Draw sparkle effects around the powerup
        sparkle_count = 4
        for i in range(sparkle_count):
            angle = (self.rotation + i * 90) % 360
            sparkle_distance = 30 + math.sin(self.pulse_timer + i) * 5
            sparkle_x = center_x + int(sparkle_distance * math.cos(math.radians(angle)))
            sparkle_y = center_y + int(sparkle_distance * math.sin(math.radians(angle)))
            
            sparkle_alpha = int(128 + 127 * math.sin(self.pulse_timer * 2 + i))
            sparkle_size = 2 + int(math.sin(self.pulse_timer * 3 + i))
            pygame.draw.circle(surface, (*self.color_set["bright"], sparkle_alpha), 
                             (sparkle_x, sparkle_y), sparkle_size)
