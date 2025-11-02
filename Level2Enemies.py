"""
Level 2 Enemy Classes for Red Riding Hood Adventure
Enhanced enemy classes with PNG sprite sheet animations and AI behaviors

=== ANIMATION SYSTEM ===
All Level 2 enemies now support frame-based PNG sprite sheet animations, 
just like Level 1 enemies!

HOW IT WORKS:
1. Sprite sheets are one-row PNGs with frames arranged horizontally
2. Each enemy has an ANIM manifest dictionary specifying:
- "idle", "run", "attack" animation states
- File path to the PNG sprite sheet
- frame_width: width of each frame in pixels
3. The build_state_animations_from_manifest() function automatically:
- Loads the sprite sheets
- Slices them into individual frames
- Scales them to 48x48 pixels (or 64x64 for boss)
4. Enemies automatically animate based on their state (idle/run/attack)

FALLBACK SYSTEM:
- If sprite sheets don't exist, enemies use colored placeholder graphics
- Game will work with or without sprite sheet assets

TO ADD NEW ANIMATIONS:
1. Create PNG sprite sheets (one row, frames side-by-side)
2. Place in: assets/Level2/[EnemyName]/[State].png
3. Set correct frame_width in the ANIM manifest
4. Done! Animations will load automatically

See Level1Enemies.py for working examples.
"""

import pygame
import math
import random
from entities import build_state_animations_from_manifest
import time

# ============ ANIMATION MANIFESTS ============
# REFERENCE - Level 1 Animation Frame Widths:
#   Warrior Run:    320x64px  → frame_width: 40 (8 frames)
#   Warrior Attack: 200x64px  → frame_width: 40 (5 frames)  
#   Archer Run:     512x64px  → frame_width: 64 (8 frames)
#   Archer Attack:  704x64px  → frame_width: 64 (11 frames)

# ============ LEVEL 2 ENEMY ANIMATION MANIFESTS ============
# All Level 2 enemies now support PNG sprite sheet animations with frame_width specification
# Simply place your sprite sheets in the correct directories and they'll be automatically loaded

# SKELETON - Melee bone warrior (600x150 for Idle/Walk = 4 frames, 1200x150 for Attack = 8 frames)
SKELETON_ANIM = {
    "idle":     {"file": "assets/Level2/Skeleton/Idle.png",     "frame_width": 150, "scale_to": (128, 128)},
    "run":      {"file": "assets/Level2/Skeleton/Walk.png",     "frame_width": 150, "scale_to": (128, 128)},
    "attack":   {"file": "assets/Level2/Skeleton/Attack.png",   "frame_width": 150, "scale_to": (128, 128)}
}

# MUSHROOM - Melee poison attacker (600x150 for Idle = 4 frames, 1200x150 for Run/Attack = 8 frames)
MUSHROOM_ANIM = {
    "idle":     {"file": "assets/Level2/Mushroom/Idle.png",     "frame_width": 150, "scale_to": (128, 128)},
    "run":      {"file": "assets/Level2/Mushroom/Run.png",      "frame_width": 150, "scale_to": (128, 128)},
    "attack":   {"file": "assets/Level2/Mushroom/Attack.png",   "frame_width": 150, "scale_to": (128, 128)}
}

# FLYING EYE - Aerial ranged attacker (1200x150 = 8 frames each)
FLYING_EYE_ANIM = {
    "idle":     {"file": "assets/Level2/Flying eye/Flight.png", "frame_width": 150, "scale_to": (128, 128)},
    "run":      {"file": "assets/Level2/Flying eye/Flight.png", "frame_width": 150, "scale_to": (128, 128)},
    "attack":   {"file": "assets/Level2/Flying eye/Attack.png", "frame_width": 150, "scale_to": (128, 128)}
}
class Level2Enemy:
    """Base Level 2 enemy class with enhanced AI behaviors"""
    
    def __init__(self, x, y, width=128, height=128, anim_manifest: dict = None):
        
        # Hitbox is smaller than sprite for better collision detection
        hitbox_width = 80
        hitbox_height = 80
        
        # Center the hitbox position
        hitbox_x = x + (width - hitbox_width) // 2
        hitbox_y = y + (height - hitbox_height) // 2
        
        self.rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        # IMPORTANT: Keep original spawn position for physics calculations, not centered position
        self.original_x = x
        self.original_y = y
        self.name = "Level2Enemy"
        
        # Store sprite dimensions for drawing
        self.sprite_width = width
        self.sprite_height = height
        self.sprite_offset_x = -(width - hitbox_width) // 2
        self.sprite_offset_y = -(height - hitbox_height) // 10

        self.alive = True
        self.visible = True
        self.image = pygame.Surface((width, height))
        self.image.fill((139, 69, 19))  # Brown color for Level 2 theme

        self.speed = 2.5
        self.direction = 1
        self.facing_right = (self.direction > 0)
        self.y_velocity = 0
        self.gravity = 0.5
        self.on_ground = False
        self.isIdle = False
        self.player_world_rect = None

        self.ai_state = "idle"
        self.ai_timer = 0

        self.patrol_start = hitbox_x  # Use hitbox position for patrol
        self.patrol_range = 150

        self.sight_range = 250
        self.sight_width = 80
        self.sight_color = (139, 0, 139, 100)  # Dark purple for Level 2
        self.player_spotted = False

        self.debug_mode = False  # Hide debug boxes by default

        self.max_hp = 120
        self.current_hp = self.max_hp

        self.attack_range = pygame.Vector2(50, 50)
        self.player_in_attack = False
        self.attack_cooldown = 2000  # Faster attacks in Level 2
        self.last_attack_time = 0
        self.attack_flash_time = 1000
        self.attack_flash_until = 0
        
        self.exclamation_img = pygame.image.load("assets/exclamation.png").convert_alpha()
        self.exclamation_img = pygame.transform.scale(self.exclamation_img, (16, 24))
        self.anims = build_state_animations_from_manifest(anim_manifest or {})
        self.anim_tick = 0
        self.anim_speed = 10
        self.attack_anim_timer = 0
        self.attack_anim_elapsed = 0
        self.attack_anim_duration = 0
        self.current_state = "run" if "run" in self.anims else None
        if "run" in self.anims and self.anims["run"]:
            self.image = self.anims["run"][0]
        self._last_x = self.rect.x
        if not hasattr(self, "facing_right"):
            self.facing_right = True
        
        # Visual effects
        self.hit_particles = []
        self.hit_flash_timer = 0
        
    def _anim_index(self, frames):
        if not frames:
            return 0
        return (self.anim_tick // self.anim_speed) % len(frames)

    def update_anim_timers(self, dt):
        if self.attack_anim_timer > 0:
            self.attack_anim_timer = max(0, self.attack_anim_timer - dt)
            self.attack_anim_elapsed = min(self.attack_anim_duration, self.attack_anim_elapsed + dt)

    def start_attack_anim(self, duration_ms=400):
        self.attack_anim_duration = max(1, duration_ms)
        self.attack_anim_timer = duration_ms
        self.attack_anim_elapsed = 0

    def update_animation(self):
        """Update animation frames based on current state"""
        self.anim_tick = (self.anim_tick + 1) % 10000000

        # Attack animation (non-looping)
        if self.attack_anim_timer > 0 and "attack" in self.anims and self.anims["attack"]:
            state = "attack"
            frames = self.anims["attack"]
            if frames:
                progress = self.attack_anim_elapsed / self.attack_anim_duration
                idx = min(int(progress * len(frames)), len(frames) - 1)
            else:
                idx = 0

        else:
            state = "run" if "run" in self.anims else None
            frames = self.anims.get("run", [])
            if state and frames:
                if self.rect.x == self._last_x:
                    idx = 0  
                else:
                    idx = (self.anim_tick // self.anim_speed) % len(frames)
            else:
                idx = 0

        if state and frames:
            img = frames[idx]
            self.image = img if self.facing_right else pygame.transform.flip(img, True, False)
            self.current_state = state

        self._last_x = self.rect.x

    def update_timers(self, dt):
        """Update internal timers"""
        if hasattr(self, 'ai_timer'):
            self.ai_timer += dt
        self.update_anim_timers(dt)

    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        """Main update method"""
        if not self.alive:
            return
        
        # Set scroll offset first
        self.scroll_offset = scroll_offset
        
        if player:
            self.player_world_rect = player.rect.copy()
            self.player_world_rect.x += self.scroll_offset

        self.update_timers(dt)
        if obstacles is None:
            obstacles = []
        
        if self.is_player_in_sight(player):
            if not self.player_spotted:
                self.on_player_spotted(player)
                self.player_spotted = True
        else:
            self.player_spotted = False
        
        self.update_ai(player, obstacles, dt)
        self.update_attack_detection(player)
        self.attack(player)
        self.apply_physics(obstacles)
        self.update_animation()

    def update_ai(self, player, obstacles, dt):
        """AI behavior implementation"""
        if self.isIdle:
            return
        
        # Default patrol behavior
        if player and self.is_player_in_sight(player):
            # Face player
            if player.rect.centerx + self.scroll_offset > self.rect.centerx:
                self.facing_right = True
                self.direction = 1
            else:
                self.facing_right = False
                self.direction = -1
            
            # Move towards player
            move_speed = self.speed * dt
            if abs(self.player_world_rect.centerx - self.rect.centerx) > 100:
                dx = self.direction * move_speed
                self.move_horizontal(dx, obstacles)
        else:
            # Patrol behavior
            self.ai_timer += dt
            if self.ai_timer > 60:  # Change direction every second
                self.direction *= -1
                self.facing_right = (self.direction > 0)
                self.ai_timer = 0
            
            self.move_horizontal(self.direction * self.speed * dt, obstacles)

    def is_player_in_sight(self, player):
        """Check if player is in enemy's sight range"""
        if not player:
            return False
        sight_rect = self.get_sight_rect()
        return sight_rect.colliderect(self.player_world_rect)

    def get_sight_rect(self):
        """Get enemy's line of sight rectangle"""
        if self.facing_right:
            sight_x = self.rect.centerx
            sight_y = self.rect.centery - (self.sight_width // 2)
            return pygame.Rect(sight_x, sight_y, self.sight_range, self.sight_width)
        else:
            sight_x = self.rect.centerx - self.sight_range
            sight_y = self.rect.centery - (self.sight_width // 2)
            return pygame.Rect(sight_x, sight_y, self.sight_range, self.sight_width)

    def draw_line_of_sight(self, surface):
        """Draw debug line of sight"""
        if not self.debug_mode:
            return
        sight_rect = self.get_sight_rect()
        
        screen_sight_rect = sight_rect.copy()
        screen_sight_rect.x -= self.scroll_offset
        
        temp_surface = pygame.Surface((screen_sight_rect.width, screen_sight_rect.height), pygame.SRCALPHA)
        temp_surface.fill(self.sight_color)
        surface.blit(temp_surface, (screen_sight_rect.x, screen_sight_rect.y))

    def on_player_spotted(self, player):
        """Called when player is spotted"""
        print(f"{self.name} has spotted the player!")
        pass

    def apply_physics(self, obstacles):
        """Apply gravity and collisions"""
        if not self.on_ground:
            self.y_velocity += self.gravity
        else:
            self.y_velocity = 0
        
        self.rect.y += int(self.y_velocity)  # Use int to prevent float accumulation
        self.check_vertical_collision(obstacles)
        
        if not self.check_ground_ahead(self.direction * 5, obstacles):
            if self.on_ground:
                self.y_velocity = 0.1

    def check_ground_ahead(self, dx, obstacles):
        """Check if there's ground ahead"""
        if dx > 0: 
            check_x = self.rect.right + 5
        else:
            check_x = self.rect.left - 5
            
        ground_check = pygame.Rect(check_x - 5, self.rect.bottom, 32, 20)  
        self.debug_ground_check = ground_check
        
        ground_found = False
        for obstacle in obstacles:
            world_obstacle_rect = obstacle.get_rect().copy()
            # Handle both obstacles with original_x/y and those without
            if hasattr(obstacle, 'original_x'):
                world_obstacle_rect.x = obstacle.original_x
                world_obstacle_rect.y = obstacle.original_y
            
            if ground_check.colliderect(world_obstacle_rect):
                ground_found = True
                break
        
        return ground_found

    def move_horizontal(self, dx, obstacles):
        """Move horizontally and check for collisions"""
        old_x = self.rect.x
        
        self.rect.x += dx
        
        if self.check_horizontal_collision(obstacles):
            self.rect.x = old_x
            self.handle_wall_collision()
            
    def check_horizontal_collision(self, obstacles):
        """Check for horizontal collisions"""
        for obstacle in obstacles:
            world_obstacle_rect = obstacle.get_rect().copy()
            # Handle both obstacles with original_x/y and those without
            if hasattr(obstacle, 'original_x'):
                world_obstacle_rect.x = obstacle.original_x 
                world_obstacle_rect.y = obstacle.original_y
            
            if self.rect.colliderect(world_obstacle_rect):
                return True
        return False
        
    def check_vertical_collision(self, obstacles):
        """Check for vertical collisions"""
        for obstacle in obstacles:
            world_obstacle_rect = obstacle.get_rect().copy()
            # Handle both obstacles with original_x/y and those without
            if hasattr(obstacle, 'original_x'):
                world_obstacle_rect.x = obstacle.original_x
                world_obstacle_rect.y = obstacle.original_y
            
            if self.rect.colliderect(world_obstacle_rect):
                if self.y_velocity > 0:
                    self.rect.bottom = world_obstacle_rect.top
                    self.y_velocity = 0
                    self.on_ground = True
                elif self.y_velocity < 0:
                    self.rect.top = world_obstacle_rect.bottom
                    self.y_velocity = 0
                return True
        if self.on_ground:
            ground_check = pygame.Rect(self.rect.x, self.rect.y + 1, self.rect.width, self.rect.height)
            still_on_ground = False
            for obstacle in obstacles:
                world_obstacle_rect = obstacle.get_rect().copy()
                # Handle both obstacles with original_x/y and those without
                if hasattr(obstacle, 'original_x'):
                    world_obstacle_rect.x = obstacle.original_x
                    world_obstacle_rect.y = obstacle.original_y
                
                if ground_check.colliderect(world_obstacle_rect):
                    still_on_ground = True
                    break
            if not still_on_ground:
                self.on_ground = False
        return False

    def handle_wall_collision(self):
        """Handle collision with walls"""
        self.direction *= -1
        self.facing_right = (self.direction > 0)

    def update_attack_detection(self, player):
        """Update attack range detection"""
        attack_rect = self.get_attack_rect()
        if player:
            self.player_in_attack = attack_rect.colliderect(self.player_world_rect)
        
    def get_attack_rect(self):
        """Get attack range rectangle"""
        if self.facing_right:
            x = self.rect.right
        else:
            x = self.rect.left - self.attack_range.x
        y = self.rect.centery - self.attack_range.y / 2
        return pygame.Rect(x, y, self.attack_range.x, self.attack_range.y)

    def attack(self, player):
        """Attack player if in range"""
        now = pygame.time.get_ticks()
        if now - self.last_attack_time >= self.attack_cooldown:
            if self.player_in_attack:
                self.last_attack_time = now
                self.on_attack(player)

    def on_attack(self, player):
        """Called when enemy attacks"""
        print(f"{self.name} attacks player!")
        self.start_attack_anim(400)
        
        # Damage the player
        if player and hasattr(player, 'take_damage'):
            player.take_damage(1)  # Default 1 damage

    def take_damage(self, damage):
        """Take damage from player attacks"""
        self.current_hp -= damage
        print(f"{self.name} took {damage} damage! HP: {self.current_hp}/{self.max_hp}")
        
        if self.current_hp <= 0:
            self.alive = False
            print(f"{self.name} has been defeated!")

    def draw(self, surface):
        """Draw enemy on screen"""
        if not self.alive or not self.visible:
            return
        
        # Draw sprite centered over hitbox
        screen_x = self.rect.x - self.scroll_offset + self.sprite_offset_x
        screen_y = self.rect.y + self.sprite_offset_y
        
        self.draw_line_of_sight(surface)
        surface.blit(self.image, (screen_x, screen_y))

        if self.player_spotted:
            bounce = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 3
            exclamation_x = screen_x + self.sprite_width // 2 - self.exclamation_img.get_width() // 2
            exclamation_y = screen_y - self.exclamation_img.get_height() - 5 - bounce
            surface.blit(self.exclamation_img, (exclamation_x, exclamation_y))

        if self.debug_mode and hasattr(self, 'debug_ground_check'):
            screen_ground_check = self.debug_ground_check.copy()
            screen_ground_check.x -= self.scroll_offset
            pygame.draw.rect(surface, (0, 255, 0), screen_ground_check, 2)
        
        if self.debug_mode:
            self.draw_debug_ranges(surface, self.scroll_offset)
            # Draw hitbox in debug mode
            hitbox_rect = self.rect.copy()
            hitbox_rect.x -= self.scroll_offset
            pygame.draw.rect(surface, (255, 0, 0), hitbox_rect, 2)
            
    def draw_debug_ranges(self, surface, scroll_offset=0):
        """Draw debug attack range"""
        attack_rect = self.get_attack_rect().move(-scroll_offset, 0)
        pygame.draw.rect(surface, (255, 100, 0), attack_rect, 1)

    def get_rect(self):
        """Get enemy's collision rect"""
        return self.rect


# ============ PARTICLE EFFECTS FOR LEVEL 2 ENEMIES ============

class BoneParticle:
    """Bone projectile particle for Skeleton attacks"""
    def __init__(self, x, y, target_x, target_y):
        self.x = x
        self.y = y
        # Calculate direction
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 0:
            self.speed_x = (dx / distance) * 5
            self.speed_y = (dy / distance) * 5
        else:
            self.speed_x = 5
            self.speed_y = 0
        self.lifespan = 60
        self.rotation = random.randint(0, 360)
        self.rotation_speed = random.uniform(-10, 10)
        
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.rotation += self.rotation_speed
        self.lifespan -= 1
        
    def draw(self, surface, scroll_offset):
        if self.lifespan > 0:
            screen_x = int(self.x - scroll_offset)
            screen_y = int(self.y)
            # Draw bone as elongated white rectangle
            bone_surface = pygame.Surface((16, 4), pygame.SRCALPHA)
            pygame.draw.rect(bone_surface, (230, 230, 230), (0, 0, 16, 4))
            pygame.draw.circle(bone_surface, (240, 240, 240), (2, 2), 3)
            pygame.draw.circle(bone_surface, (240, 240, 240), (14, 2), 3)
            rotated = pygame.transform.rotate(bone_surface, self.rotation)
            rect = rotated.get_rect(center=(screen_x, screen_y))
            surface.blit(rotated, rect)
    
    def is_dead(self):
        return self.lifespan <= 0


class PoisonCloudParticle:
    """Poison cloud effect for Mushroom attacks"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 5
        self.max_radius = 40
        self.lifespan = 90
        self.max_lifespan = 90
        self.alpha = 180
        
    def update(self):
        self.lifespan -= 1
        # Expand
        growth = (self.max_lifespan - self.lifespan) / self.max_lifespan
        self.radius = int(self.max_radius * min(growth * 2, 1.0))
        # Fade
        self.alpha = int(180 * (self.lifespan / self.max_lifespan))
        
    def draw(self, surface, scroll_offset):
        if self.lifespan > 0 and self.radius > 0:
            screen_x = int(self.x - scroll_offset)
            screen_y = int(self.y)
            # Draw multiple layers for cloud effect
            for i in range(3):
                offset_radius = self.radius - i * 8
                if offset_radius > 0:
                    cloud_surface = pygame.Surface((offset_radius * 2, offset_radius * 2), pygame.SRCALPHA)
                    color = (100, 200 + i * 20, 50, self.alpha // (i + 1))
                    pygame.draw.circle(cloud_surface, color, (offset_radius, offset_radius), offset_radius)
                    surface.blit(cloud_surface, (screen_x - offset_radius, screen_y - offset_radius))
    
    def is_dead(self):
        return self.lifespan <= 0


class TeleportParticle:
    """Swirling particle effect for Flying Eye teleport"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.offset_x = random.uniform(-20, 20)
        self.offset_y = random.uniform(-20, 20)
        self.angle = random.uniform(0, 360)
        self.speed = random.uniform(2, 5)
        self.lifespan = random.randint(15, 30)
        self.max_lifespan = self.lifespan
        self.size = random.randint(3, 6)
        self.color = random.choice([
            (200, 50, 200),   # Purple
            (150, 50, 255),   # Blue-purple
            (255, 100, 255),  # Pink
        ])
        
    def update(self):
        self.angle += self.speed
        self.offset_x = math.cos(math.radians(self.angle)) * 20
        self.offset_y = math.sin(math.radians(self.angle)) * 20
        self.lifespan -= 1
        
    def draw(self, surface, scroll_offset, center_x, center_y):
        if self.lifespan > 0:
            screen_x = int(center_x + self.offset_x - scroll_offset)
            screen_y = int(center_y + self.offset_y)
            alpha = int(255 * (self.lifespan / self.max_lifespan))
            particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, alpha)
            pygame.draw.circle(particle_surface, color_with_alpha, (self.size, self.size), self.size)
            surface.blit(particle_surface, (screen_x - self.size, screen_y - self.size))
    
    def is_dead(self):
        return self.lifespan <= 0


# ============ SPECIFIC ENEMY TYPES ============


# ============ ORIGINAL LEVEL 2 ENEMIES (FROM entities.py) ============

class MutatedMushroom(Level2Enemy):
    """Level 2 - Mutated Mushroom melee enemy with poison attacks"""
    
    def __init__(self, x, y, width=128, height=128):
        # Pass dimensions to parent - parent will create centered hitbox
        super().__init__(x, y, width, height, anim_manifest=MUSHROOM_ANIM)
        self.name = "Mushroom"
        
        # Stats - Melee with poison
        self.max_hp = 40
        self.current_hp = self.max_hp
        self.speed = 1.8
        self.attack_damage = 1  # Reduced to 1 for player with 3 hearts
        
        # Melee combat settings
        self.sight_range = 220
        self.sight_width = 65
        self.attack_range = pygame.Vector2(60, 60)
        self.attack_cooldown = 2000
        
        # Special ability - Poison cloud
        self.poison_particles = []
        self.poison_cooldown = 0
        
    def on_attack(self, player):
        """Poison slash attack with cloud effect"""
        self.start_attack_anim(450)
        print(f"{self.name} releases poison spores!")
        
        # Damage the player
        if player and hasattr(player, 'take_damage'):
            player.take_damage(self.attack_damage)
        
        # Create poison cloud on attack
        if self.poison_cooldown <= 0:
            particle = PoisonCloudParticle(self.rect.centerx, self.rect.centery)
            self.poison_particles.append(particle)
            self.poison_cooldown = 120  # Cooldown frames
    
    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        super().update(player, dt, obstacles, scroll_offset)
        
        # Update poison cooldown
        if self.poison_cooldown > 0:
            self.poison_cooldown -= dt
        
        # Update poison particles
        for particle in self.poison_particles[:]:
            particle.update()
            if particle.is_dead():
                self.poison_particles.remove(particle)
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw poison particles
        for particle in self.poison_particles:
            particle.draw(surface, self.scroll_offset)


class Skeleton(Level2Enemy):
    """Level 2 - Skeleton melee warrior with bone slash attacks"""
    
    def __init__(self, x, y, width=128, height=128):
        # Pass dimensions to parent - parent will create centered hitbox
        super().__init__(x, y, width, height, anim_manifest=SKELETON_ANIM)
        self.name = "Skeleton"
        
        # Stats - Melee warrior
        self.max_hp = 50
        self.current_hp = self.max_hp
        self.speed = 2.2
        self.attack_damage = 1  # Reduced to 1 for player with 3 hearts
        
        # Melee combat settings
        self.sight_range = 250
        self.sight_width = 70
        self.attack_range = pygame.Vector2(55, 55)
        self.attack_cooldown = 1800
        
        # Attack effects
        self.slash_particles = []
        
    def on_attack(self, player):
        """Bone slash melee attack with visual effects"""
        self.start_attack_anim(400)
        print(f"{self.name} slashes with bone sword!")
        
        # Damage the player
        if player and hasattr(player, 'take_damage'):
            player.take_damage(self.attack_damage)
        
        # Create slash effect particles
        for i in range(5):
            particle = BoneParticle(
                self.rect.centerx + (20 if self.facing_right else -20),
                self.rect.centery + random.randint(-10, 10),
                player.rect.centerx,
                player.rect.centery
            )
            self.slash_particles.append(particle)
    
    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        super().update(player, dt, obstacles, scroll_offset)
        
        # Update slash particles
        for particle in self.slash_particles[:]:
            particle.update()
            if particle.is_dead():
                self.slash_particles.remove(particle)
    
    def draw(self, surface):
        super().draw(surface)
        
        # Draw slash particles
        for particle in self.slash_particles:
            particle.draw(surface, self.scroll_offset)


class FlyingEye(Level2Enemy):
    """Level 2 - Flying Eye monster with aerial ranged attacks"""
    
    def __init__(self, x, y, width=128, height=128):
        # Pass dimensions to parent - parent will create centered hitbox
        super().__init__(x, y, width, height, anim_manifest=FLYING_EYE_ANIM)
        self.name = "Flying Eye"
        
        # Stats - Flying ranged enemy
        self.max_hp = 30
        self.current_hp = self.max_hp
        self.speed = 2.5
        self.attack_damage = 1  # Reduced to 1 for player with 3 hearts
        
        # Flying properties
        self.can_fly = True
        self.fly_height = y - 60  # Float above ground
        self.hover_offset = 0
        self.hover_speed = 0.05
        
        # Ranged combat settings
        self.sight_range = 300
        self.sight_width = 90
        self.attack_range = pygame.Vector2(200, 200)
        self.attack_cooldown = 2200
        
        # Special abilities
        self.teleport_particles = []
        self.is_teleporting = False
        self.teleport_cooldown = 0
        self.energy_beams = []
        
    def apply_physics(self, obstacles):
        """Override physics - flying enemies don't use gravity"""
        # Maintain flight with hovering effect
        self.hover_offset += self.hover_speed
        self.rect.y = int(self.fly_height + math.sin(self.hover_offset) * 8)
        self.on_ground = False
        
    def on_attack(self, player):
        """Ranged eye beam attack with teleport effect"""
        self.start_attack_anim(500)
        print(f"{self.name} fires energy beam!")
        
        # Damage the player
        if player and hasattr(player, 'take_damage'):
            player.take_damage(self.attack_damage)
        
        # Create energy beam particle
        beam = BoneParticle(
            self.rect.centerx,
            self.rect.centery,
            player.rect.centerx + self.scroll_offset,
            player.rect.centery
        )
        self.energy_beams.append(beam)
        
        # Chance to teleport after attack
        if random.random() < 0.3 and self.teleport_cooldown <= 0:
            self.start_teleport()
    
    def start_teleport(self):
        """Initiate teleport with particle effect"""
        self.is_teleporting = True
        self.teleport_cooldown = 180
        
        # Create teleport particles
        for i in range(12):
            particle = TeleportParticle(self.rect.centerx, self.rect.centery)
            self.teleport_particles.append(particle)
        
        # Teleport to random nearby position
        new_x = self.original_x + random.randint(-150, 150)
        self.rect.x = new_x
        self.fly_height = self.original_y - random.randint(40, 80)
    
    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        super().update(player, dt, obstacles, scroll_offset)
        
        # Update teleport cooldown
        if self.teleport_cooldown > 0:
            self.teleport_cooldown -= dt
        
        if self.is_teleporting and self.teleport_cooldown <= 150:
            self.is_teleporting = False
        
        # Update energy beams
        for beam in self.energy_beams[:]:
            beam.update()
            if beam.is_dead():
                self.energy_beams.remove(beam)
        
        # Update teleport particles
        for particle in self.teleport_particles[:]:
            particle.update()
            if particle.is_dead():
                self.teleport_particles.remove(particle)
    
    def draw(self, surface):
        # Draw teleport particles first (behind enemy)
        for particle in self.teleport_particles:
            particle.draw(surface, self.scroll_offset, self.rect.centerx, self.rect.centery)
        
        # Draw enemy
        if not self.is_teleporting or (pygame.time.get_ticks() // 100) % 2:
            super().draw(surface)
        
        # Draw energy beams
        for beam in self.energy_beams:
            beam.draw(surface, self.scroll_offset)


# ============ USAGE EXAMPLE ============
if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1))  # Hidden window for loading images
    
    print("\n" + "=" * 60)
    print("LEVEL 2 ENEMY SYSTEM - LOADED")
    print("=" * 60)
    print("\n✅ Three Level 2 Enemies:")
    print("  1. Skeleton - Melee warrior with bone slash attacks")
    print("  2. Mushroom - Melee with poison cloud effects")
    print("  3. Flying Eye - Ranged aerial attacker with teleport")
    print("\n✅ Attack Effects:")
    print("  - Bone particles for Skeleton slashes")
    print("  - Poison cloud particles for Mushroom attacks")
    print("  - Teleport particles and energy beams for Flying Eye")
    print("\n✅ Animation Support:")
    print("  - All enemies use sprite sheet animations")
    print("  - Proper attack animations with timing")
    print("  - Smooth transitions between states")
    print("=" * 60)


# ============ COLLECTIBLE ITEMS ============

class MushroomPickup:
    """Level 2 mushroom pickup - collectible item (NOT an enemy)"""
    
    def __init__(self, x, y, image):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.original_x = x
        self.original_y = y
        self.name = "MushroomPickup"
        self.image = image
        
        self.alive = True
        self.visible = True
        
        # Pickup properties - marks this as collectible
        self.is_collectible = True
        self.solid = False
        
        # No physics needed for pickups
        self.gravity = 0
        self.y_velocity = 0
        self.on_ground = True
        self.isIdle = True
        
    def get_rect(self):
        """Return empty rect so it doesn't collide as an obstacle"""
        return pygame.Rect(self.rect.x, self.rect.y, 0, 0)
        
    def check_player_collision(self, player, scroll_offset):
        """Check if player touches the mushroom pickup"""
        if not self.alive:
            return False
            
        player_world_rect = player.rect.copy()
        player_world_rect.x += scroll_offset
        
        if self.rect.colliderect(player_world_rect):
            return True
        return False
        
    def collect(self):
        """Collect the mushroom - increases mushroom counter"""
        self.alive = False
        print("Mushroom collected!")
        
    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        """Pickups don't need to update"""
        pass
        
    def draw(self, surface, scroll_offset=0):
        """Draw the mushroom pickup"""
        if not self.alive or not self.visible:
            return
        
        screen_x = self.rect.x - scroll_offset
        screen_y = self.rect.y
        surface.blit(self.image, (screen_x, screen_y))
    
    def on_attack(self, player):
        """Pickups don't attack"""
        pass
