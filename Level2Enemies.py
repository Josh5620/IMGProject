"""
Level 2 Enemy Classes for Red Riding Hood Adventure
Enhanced enemy classes with animations and AI behaviors
"""

import pygame
import math
import random
from entities import build_state_animations_from_manifest, Enemy
import time

# ============ ANIMATION MANIFESTS ============
# REFERENCE - Level 1 Animation Frame Widths:
#   Warrior Run:    320x64px  → frame_width: 40 (8 frames)
#   Warrior Attack: 200x64px  → frame_width: 40 (5 frames)  
#   Archer Run:     512x64px  → frame_width: 64 (8 frames)
#   Archer Attack:  704x64px  → frame_width: 64 (11 frames)

# MUSHROOM ENEMY ANIMATIONS (from MushroomLevel2Enemies.tsx)
# Sprite sheet: 128x80 pixels (8 columns × 5 rows = 40 tiles of 16x16)
# Using only 6 frames per state to match the 6 Level 2 powerup types
# Layout:
#   Row 1 (frames 0-5):   Idle animation (6 frames)
#   Row 2 (frames 0-5):   Run animation (6 frames)
#   Row 3 (frames 0-5):   Attack animation (6 frames)
# Note: Mushroom animations are loaded dynamically via build_mushroom_animations_from_sprite_sheet()
# This dict is just for reference and not actually used
MUSHROOM_ENEMY_ANIM = {
    "idle":     {"file": "assets/mushroom level 2.png", "frame_width": 16, "frames_used": 6},
    "run":      {"file": "assets/mushroom level 2.png", "frame_width": 16, "frames_used": 6},
    "attack":   {"file": "assets/mushroom level 2.png", "frame_width": 16, "frames_used": 6}
}

# Other Level 2 enemy animations (placeholder for now)
WOLF_ENEMY_ANIM = {
    "idle":     {"file": "assets/Level2/Wolf/Idle.png",     "frame_width": 48},
    "run":      {"file": "assets/Level2/Wolf/Run.png",      "frame_width": 48},
    "attack":   {"file": "assets/Level2/Wolf/Attack.png",   "frame_width": 48}
}

SHADOW_CREATURE_ANIM = {
    "idle":     {"file": "assets/Level2/ShadowCreature/Idle.png",     "frame_width": 48},
    "run":      {"file": "assets/Level2/ShadowCreature/Run.png",      "frame_width": 48},
    "attack":   {"file": "assets/Level2/ShadowCreature/Attack.png",   "frame_width": 48}
}

DARK_ENCHANTER_ANIM = {
    "idle":     {"file": "assets/Level2/DarkEnchanter/Idle.png",     "frame_width": 64},
    "run":      {"file": "assets/Level2/DarkEnchanter/Run.png",      "frame_width": 64},
    "attack":   {"file": "assets/Level2/DarkEnchanter/Attack.png",   "frame_width": 64}
}


def build_mushroom_animations_from_sprite_sheet(file_path, tile_size=16, frames_per_state=6):
    """
    Build animations from grid-based sprite sheet for mushroom enemy.
    Uses 6 frames per state to match the 6 Level 2 powerup types.
    
    Args:
        file_path: Path to sprite sheet image
        tile_size: Size of each tile in pixels
        frames_per_state: Number of frames per animation state (default: 6)
        
    Returns:
        dict of animation states with lists of frames
    """
    try:
        sheet = pygame.image.load(file_path).convert_alpha()
        anims = {}
        
        # Extract frames from grid layout (8 columns, 5 rows)
        # Using only first 6 frames of each row for the 6 powerup types
        # Row 1 (y=0): Idle frames 0-5
        # Row 2 (y=1): Run frames 0-5
        # Row 3 (y=2): Attack frames 0-5
        
        idle_frames = []
        run_frames = []
        attack_frames = []
        
        # Extract Idle frames (row 1, frames 0-5, matching 6 powerups)
        for i in range(frames_per_state):
            x = i * tile_size
            y = 0 * tile_size
            rect = pygame.Rect(x, y, tile_size, tile_size)
            frame = sheet.subsurface(rect).copy()
            # Scale up to 48x48 for consistency with other enemies
            frame = pygame.transform.scale(frame, (48, 48))
            idle_frames.append(frame)
        
        # Extract Run frames (row 2, frames 0-5)
        for i in range(frames_per_state):
            x = i * tile_size
            y = 1 * tile_size
            rect = pygame.Rect(x, y, tile_size, tile_size)
            frame = sheet.subsurface(rect).copy()
            frame = pygame.transform.scale(frame, (48, 48))
            run_frames.append(frame)
        
        # Extract Attack frames (row 3, frames 0-5)
        for i in range(frames_per_state):
            x = i * tile_size
            y = 2 * tile_size
            rect = pygame.Rect(x, y, tile_size, tile_size)
            frame = sheet.subsurface(rect).copy()
            frame = pygame.transform.scale(frame, (48, 48))
            attack_frames.append(frame)
        
        anims["idle"] = idle_frames
        anims["run"] = run_frames
        anims["attack"] = attack_frames
        
        return anims
    except Exception as e:
        print(f"Error loading mushroom sprite sheet: {e}")
        return {"idle": [], "run": [], "attack": []}


class Level2Enemy:
    """Base Level 2 enemy class with enhanced AI behaviors"""
    
    def __init__(self, x, y, width=48, height=48, anim_manifest: dict = None):
        
        self.rect = pygame.Rect(x, y, width, height)
        self.original_x = x
        self.original_y = y
        self.name = "Level2Enemy"

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

        self.patrol_start = x
        self.patrol_range = 150

        self.sight_range = 250
        self.sight_width = 80
        self.sight_color = (139, 0, 139, 100)  # Dark purple for Level 2
        self.player_spotted = False

        self.debug_mode = True

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
        
        self.rect.y += self.y_velocity
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
            world_obstacle_rect.x = obstacle.original_x 
            world_obstacle_rect.y = obstacle.original_y
            
            if self.rect.colliderect(world_obstacle_rect):
                return True
        return False
        
    def check_vertical_collision(self, obstacles):
        """Check for vertical collisions"""
        for obstacle in obstacles:
            world_obstacle_rect = obstacle.get_rect().copy()
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
        pass

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
        
        screen_x = self.rect.x - self.scroll_offset
        screen_y = self.rect.y
        
        self.draw_line_of_sight(surface)
        surface.blit(self.image, (screen_x, screen_y))

        if self.player_spotted:
            bounce = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 3
            exclamation_x = screen_x + self.rect.width // 2 - self.exclamation_img.get_width() // 2
            exclamation_y = screen_y - self.exclamation_img.get_height() - 5 - bounce
            surface.blit(self.exclamation_img, (exclamation_x, exclamation_y))

        if self.debug_mode and hasattr(self, 'debug_ground_check'):
            screen_ground_check = self.debug_ground_check.copy()
            screen_ground_check.x -= self.scroll_offset
            pygame.draw.rect(surface, (0, 255, 0), screen_ground_check, 2)
        
        if self.debug_mode:
            self.draw_debug_ranges(surface, self.scroll_offset)
             
    def draw_debug_ranges(self, surface, scroll_offset=0):
        """Draw debug attack range"""
        attack_rect = self.get_attack_rect().move(-scroll_offset, 0)
        pygame.draw.rect(surface, (255, 100, 0), attack_rect, 1)

    def get_rect(self):
        """Get enemy's collision rect"""
        return self.rect


# ============ SPECIFIC ENEMY TYPES ============

class WolfEnemy(Level2Enemy):
    """Ferocious wolf enemies for Level 2"""
    
    def __init__(self, x, y, width=48, height=48):
        super().__init__(x, y, width, height, anim_manifest=WOLF_ENEMY_ANIM)
        
        self.sight_range = 220
        self.sight_width = 70
        self.patrol_range = 180
        self.speed = 2.8
        self.name = "Wolf"
        
        self.max_hp = 150
        self.current_hp = self.max_hp
        
        self.attack_cooldown = 1500
        self.attack_damage = 15
        
    def on_attack(self, player):
        """Wolf bite attack"""
        self.start_attack_anim(300)
        print(f"{self.name} bites at the player!")
        if player:
            # Deal damage to player
            pass


class ShadowCreature(Level2Enemy):
    """Dark shadow enemies that phase through walls"""
    
    def __init__(self, x, y, width=48, height=48):
        super().__init__(x, y, width, height, anim_manifest=SHADOW_CREATURE_ANIM)
        
        self.sight_range = 280
        self.sight_width = 60
        self.patrol_range = 200
        self.speed = 3.0
        self.name = "Shadow Creature"
        
        self.max_hp = 100
        self.current_hp = self.max_hp
        
        self.attack_cooldown = 1800
        self.attack_damage = 12
        self.can_phase = True
        
    def update_ai(self, player, obstacles, dt):
        """Enhanced AI with phase ability"""
        if self.can_phase and self.player_spotted:
            # Shadow creatures can move through some obstacles
            pass
        super().update_ai(player, obstacles, dt)
        
    def on_attack(self, player):
        """Shadow touch attack"""
        self.start_attack_anim(350)
        print(f"{self.name} attacks with dark energy!")


class DarkEnchanter(Level2Enemy):
    """Ranged magical enemy for Level 2"""
    
    def __init__(self, x, y, width=64, height=64):
        super().__init__(x, y, width, height, anim_manifest=DARK_ENCHANTER_ANIM)
        
        self.sight_range = 300
        self.sight_width = 80
        self.patrol_range = 150
        self.speed = 1.5
        self.name = "Dark Enchanter"
        
        self.max_hp = 80
        self.current_hp = self.max_hp
        
        self.attack_cooldown = 2500
        self.attack_damage = 20
        
        # Spell casting
        self.spell_range = 250
        self.projectiles = []
        
    def can_cast(self):
        """Check if enchanter can cast spell"""
        return pygame.time.get_ticks() - self.last_attack_time >= self.attack_cooldown
    
    def on_attack(self, player):
        """Cast dark magic spell"""
        self.start_attack_anim(500)
        print(f"{self.name} casts a dark spell!")
        # TODO: Implement spell projectile spawning
        pass


# ============ ORIGINAL LEVEL 2 ENEMIES (FROM entities.py) ============

class MutatedMushroom(Enemy):
    """Level 2 - Mutated Mushroom enemy with poison attacks"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ai_type="chase")
        self.name = "MutatedMushroom"
        
        # Load sprite sheet animations
        self.anims = build_mushroom_animations_from_sprite_sheet("assets/mushroom level 2.png")
        self.image = self.anims.get("idle", [])[0] if self.anims.get("idle") else pygame.Surface((48, 48))
        
        # Animation system
        self.anim_tick = 0
        self.anim_speed = 10
        self.current_state = "idle"
        self.last_state = "idle"
        self._last_x = self.rect.x
        
        # Stats
        self.health = 150
        self.max_health = 150
        self.speed = 1.5  # Slower than player for escape ability
        self.attack_damage = 3
        self.melee_range = 70
        self.attack_range = 180
        self.color = (220, 20, 60)
        
        # Special ability - Poison cloud
        self.poison_clouds = []
        self.poison_cooldown = 0
        self.player_in_attack = False  # Initialize attack range tracking
    
    def special_attack(self, player):
        """Create poison cloud attack"""
        if self.poison_cooldown <= 0:
            cloud = {
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'radius': 40,
                'life': 120,
                'max_life': 120
            }
            self.poison_clouds.append(cloud)
            self.poison_cooldown = 240
            print("POISON CLOUD!")
    
    def update_animation(self):
        """Update animation based on current state"""
        self.anim_tick = (self.anim_tick + 1) % 10000000
        
        # Determine current state
        if self.ai_type == "chase" and self.player_in_attack:
            state = "attack"
        elif abs(self.rect.x - self._last_x) > 0.1:
            state = "run"
        else:
            state = "idle"
        
        # Update animation
        frames = self.anims.get(state, self.anims.get("idle", []))
        if frames:
            idx = (self.anim_tick // self.anim_speed) % len(frames)
            self.image = frames[idx]
        
        self.current_state = state
        self._last_x = self.rect.x
    
    def update(self, player, dt=1.0, obstacles=None):
        super().update(player, dt, obstacles)
        self.poison_cooldown = max(0, self.poison_cooldown - dt)
        
        # Random poison cloud attacks
        if self.alive and self.ai_type == "chase" and random.random() < 0.01:
            self.special_attack(player)
        
        # Update poison clouds
        for cloud in self.poison_clouds[:]:
            cloud['life'] -= dt
            cloud['radius'] = int(40 * (cloud['life'] / cloud['max_life']))
            
            if cloud['life'] <= 0:
                self.poison_clouds.remove(cloud)
        
        # Update animations
        self.update_animation()
    
    def draw(self, surface, debug_mode=False):
        if not self.alive:
            return
        
        # Draw mushroom sprite with proper facing direction
        img = self.image if self.direction > 0 else pygame.transform.flip(self.image, True, False)
        surface.blit(img, self.rect)
        
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
        
        # Draw poison clouds
        for cloud in self.poison_clouds:
            alpha = int(150 * (cloud['life'] / cloud['max_life']))
            # Semi-transparent poison cloud
            for i in range(3):
                radius = cloud['radius'] - i * 5
                if radius > 0:
                    pygame.draw.circle(surface, (0, 200, 0, alpha), 
                                    (int(cloud['x']), int(cloud['y'])), radius, 2)


class Skeleton(Enemy):
    """Level 2 - Skeleton enemy with ranged attacks"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ai_type="ranged")
        self.name = "Skeleton"
        
        # Visual - Skeleton appearance
        self.image = pygame.Surface((48, 48))
        self.image.fill((150, 150, 150))  # Gray body
        pygame.draw.circle(self.image, (200, 200, 200), (24, 12), 10)  # Skull
        pygame.draw.rect(self.image, (100, 100, 100), (20, 25, 8, 15))  # Spine
        pygame.draw.rect(self.image, (100, 100, 100), (10, 38, 20, 6))  # Pelvis
        
        # Stats
        self.health = 120
        self.max_health = 120
        self.speed = 1.6  # Slower than player for escape ability
        self.attack_damage = 2
        self.melee_range = 60
        self.attack_range = 250
        self.color = (150, 150, 150)
        
        # Special ability - Bone throwing
        self.bone_projectiles = []
        self.bone_cooldown = 0
        self.player_in_attack = False  # Initialize attack range tracking
    
    def special_attack(self, player):
        """Throw bone projectile"""
        if self.bone_cooldown <= 0 and self.alive:
            # Calculate direction to player
            dx = player.rect.centerx - self.rect.centerx
            dy = player.rect.centery - self.rect.centery
            distance = (dx**2 + dy**2)**0.5
            
            if distance > 0:
                dx /= distance
                dy /= distance
                
                bone = {
                    'x': self.rect.centerx,
                    'y': self.rect.centery,
                    'dx': dx * 5,
                    'dy': dy * 5,
                    'life': 180
                }
                self.bone_projectiles.append(bone)
                self.bone_cooldown = 180
                print("BONE THROW!")
    
    def update(self, player, dt=1.0, obstacles=None):
        super().update(player, dt, obstacles)
        self.bone_cooldown = max(0, self.bone_cooldown - dt)
        
        # Check if player is in attack range
        if player:
            distance = abs(player.rect.centerx - self.rect.centerx)
            self.player_in_attack = (distance < self.attack_range)
        
        # Throw bones when in ranged mode
        if self.alive and self.ai_type == "ranged" and self.player_in_attack and self.bone_cooldown <= 0:
            self.special_attack(player)
        
        # Update bone projectiles
        for bone in self.bone_projectiles[:]:
            bone['x'] += bone['dx'] * dt
            bone['y'] += bone['dy'] * dt
            bone['life'] -= dt
            
            if bone['life'] <= 0:
                self.bone_projectiles.remove(bone)
    
    def draw(self, surface, debug_mode=False):
        super().draw(surface, debug_mode)
        
        # Draw bone projectiles
        for bone in self.bone_projectiles:
            pygame.draw.line(surface, (200, 200, 200), 
                        (int(bone['x']), int(bone['y'])), 
                           (int(bone['x'] - bone['dx'] * 10), int(bone['y'] - bone['dy'] * 10)), 4)


class FlyingMonster(Enemy):
    """Level 2 - Flying Monster with aerial attacks"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ai_type="chase")
        self.name = "FlyingMonster"
        
        # Visual - Flying bat-like creature
        self.image = pygame.Surface((48, 48))
        self.image.fill((50, 20, 80))  # Purple body
        # Wings
        pygame.draw.ellipse(self.image, (80, 40, 120), (5, 10, 18, 12))
        pygame.draw.ellipse(self.image, (80, 40, 120), (25, 10, 18, 12))
        # Head
        pygame.draw.circle(self.image, (100, 50, 150), (24, 8), 6)
        # Eyes
        pygame.draw.circle(self.image, (255, 0, 0), (22, 7), 2)
        pygame.draw.circle(self.image, (255, 0, 0), (26, 7), 2)
        
        # Stats - Flying enemy
        self.health = 100
        self.max_health = 100
        self.speed = 1.7  # Slower than player for escape ability
        self.attack_damage = 2
        self.melee_range = 80
        self.attack_range = 200
        self.color = (80, 40, 120)
        self.can_fly = True
        self.fly_height = y - 50  # Fly above ground
        
        # Special ability - Dive attack
        self.diving = False
        self.dive_cooldown = 0
        self.player_in_attack = False  # Initialize attack range tracking
    
    def special_attack(self, player):
        """Dive attack on player"""
        if self.dive_cooldown <= 0 and not self.diving:
            self.diving = True
            self.dive_cooldown = 300
            print("DIVE ATTACK!")
            self.speed *= 1.3  # Slight speed boost during dive (reduced from 2x)
    
    def update(self, player, dt=1.0, obstacles=None):
        # Maintain flight height
        if self.can_fly:
            self.rect.y = self.fly_height
            self.on_ground = False  # Never on ground
        
        super().update(player, dt, obstacles)
        self.dive_cooldown = max(0, self.dive_cooldown - dt)
        
        # Auto dive attack when close
        distance = abs(player.rect.centerx - self.rect.centerx)
        if distance < 100 and self.dive_cooldown <= 0:
            self.special_attack(player)
        
        # Reset dive after cooldown
        if self.diving and self.dive_cooldown <= 180:
            self.diving = False
            self.speed = 1.8  # Match the base BOSS speed
    
    def draw(self, surface, debug_mode=False):
        super().draw(surface, debug_mode)
        
        # Draw wings flapping animation
        if self.ai_type == "chase":
            # Wing flapping indicator
            pygame.draw.line(surface, (150, 80, 200), 
                        (self.rect.left, self.rect.top), 
                        (self.rect.left - 10, self.rect.top), 2)
            pygame.draw.line(surface, (150, 80, 200), 
                        (self.rect.right, self.rect.top), 
                        (self.rect.right + 10, self.rect.top), 2)


class Level2Boss(Enemy):
    """Level 2 - Ultimate BOSS enemy with devastating attacks"""
    
    def __init__(self, x, y):
        super().__init__(x, y, ai_type="boss")
        self.name = "Level2Boss"
        
        # Visual - Massive intimidating BOSS
        self.image = pygame.Surface((64, 64))  # Bigger sprite
        self.image.fill((80, 0, 0))  # Dark red base
        
        # BOSS features
        pygame.draw.circle(self.image, (150, 0, 0), (32, 20), 25)  # Large head
        pygame.draw.circle(self.image, (255, 0, 0), (28, 18), 5)  # Evil eyes
        pygame.draw.circle(self.image, (255, 0, 0), (36, 18), 5)
        pygame.draw.rect(self.image, (200, 100, 0), (24, 32, 16, 24))  # Torso
        
        # Stats - ULTIMATE BOSS
        self.health = 500
        self.max_health = 500
        self.speed = 1.8  # Slower than player for escape ability
        self.attack_damage = 8
        self.melee_range = 80
        self.attack_range = 300
        self.color = (200, 0, 0)
        
        # BOSS special abilities
        self.shockwave_cooldown = 0
        self.rage_mode = False
        self.phase = 1  # 5 phases based on health
        self.boss_particles = []
        self.player_in_attack = False  # Initialize attack range tracking
        
        # Update rect size
        self.rect = pygame.Rect(x, y, 64, 64)
    
    def enter_rage_mode(self):
        """Enter rage mode when health is low"""
        if not self.rage_mode and self.health < self.max_health * 0.3:
            self.rage_mode = True
            self.speed *= 1.2  # Reduced rage boost
            self.attack_damage *= 2
            print("BOSS RAGE MODE ACTIVATED!")
    
    def shockwave_attack(self, surface):
        """Massive shockwave attack"""
        if self.shockwave_cooldown <= 0:
            # Create shockwave effect
            self.shockwave_cooldown = 420
            self.boss_particles = []  # Will be drawn as screen shake
            
            # Damage all nearby
            print("MASSIVE SHOCKWAVE!")
            return 15  # Screen shake intensity
        return 0
    
    def check_boss_phase(self):
        """Check and update boss phase"""
        health_percent = self.health / self.max_health
        new_phase = 1
        
        if health_percent <= 0.2:
            new_phase = 5
        elif health_percent <= 0.4:
            new_phase = 4
        elif health_percent <= 0.6:
            new_phase = 3
        elif health_percent <= 0.8:
            new_phase = 2
        else:
            new_phase = 1
        
        if new_phase != self.phase:
            print(f"BOSS PHASE {self.phase} -> PHASE {new_phase}!")
            self.phase = new_phase
    
    def take_damage(self, damage):
        """Enhanced damage with phase transitions"""
        self.health -= damage
        self.check_boss_phase()
        self.enter_rage_mode()
        
        if self.health <= 0:
            self.alive = False
            print("BOSS DEFEATED!")
    
    def update(self, player, dt=1.0, obstacles=None):
        super().update(player, dt, obstacles)
        self.shockwave_cooldown = max(0, self.shockwave_cooldown - dt)
        
        # BOSS special attack pattern
        if self.alive and random.random() < 0.003:  # Occasional shockwave
            self.shockwave_attack(None)
    
    def draw(self, surface, debug_mode=False):
        # Draw boss with special effects
        surface.blit(self.image, self.rect)
        
        # Draw phase indicator
        font = pygame.font.Font(None, 24)
        phase_text = f"BOSS - PHASE {self.phase}"
        text = font.render(phase_text, True, (255, 0, 0))
        surface.blit(text, (self.rect.x, self.rect.y - 20))
        
        if self.rage_mode:
            rage_text = font.render("RAGE MODE!", True, (255, 200, 0))
            surface.blit(rage_text, (self.rect.x, self.rect.y - 40))
        
        # Draw health bar (larger for boss)
        bar_width = 64
        bar_height = 6
        bar_x = self.rect.x
        bar_y = self.rect.y - 15
        
        # Background
        pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Health
        health_width = int((self.health / self.max_health) * bar_width)
        if self.rage_mode:
            color = (255, 200, 0)  # Gold when enraged
        elif self.phase >= 4:
            color = (200, 0, 255)  # Purple in phase 4-5
        elif self.phase >= 2:
            color = (255, 100, 0)  # Orange in phase 2-3
        else:
            color = (0, 255, 0)  # Green in phase 1
        
        pygame.draw.rect(surface, color, (bar_x, bar_y, health_width, bar_height))
        
        if debug_mode:
            font = pygame.font.Font(None, 20)
            health_text = font.render(f"HP: {self.health}/{self.max_health}", True, (255, 255, 255))
            surface.blit(health_text, (self.rect.x, self.rect.y - 55))


# Helper function to count animation frames
def check_animation_frames(image_path, frame_width):
    """
    Check how many frames are in a sprite sheet
    
    Args:
        image_path: Path to sprite sheet image
        frame_width: Width of each frame in pixels
        
    Returns:
        tuple: (num_frames, total_width, frame_height) or None if error
    """
    try:
        sprite_sheet = pygame.image.load(image_path).convert_alpha()
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()
        num_frames = sheet_width // frame_width
        print(f"✓ {image_path}")
        print(f"  Frames: {num_frames}")
        print(f"  Dimensions: {sheet_width}x{sheet_height}px")
        print(f"  Frame size: {frame_width}x{sheet_height}px")
        return (num_frames, sheet_width, sheet_height)
    except FileNotFoundError:
        print(f"✗ {image_path} - FILE NOT FOUND")
        return None
    except Exception as e:
        print(f"✗ Error loading {image_path}: {e}")
        return None


def analyze_sprite_sheet(image_path, frame_width=None):
    """
    Analyze a sprite sheet to determine frame count and dimensions
    
    Args:
        image_path: Path to sprite sheet image
        frame_width: Optional width of each frame. If None, will try to detect.
        
    Returns:
        dict with analysis results
    """
    try:
        sprite_sheet = pygame.image.load(image_path).convert_alpha()
        total_width = sprite_sheet.get_width()
        total_height = sprite_sheet.get_height()
        
        # If frame_width not provided, try to detect common frame sizes
        if frame_width is None:
            possible_widths = [32, 40, 48, 64]
            suggested = []
            for width in possible_widths:
                if total_width % width == 0:
                    suggested.append((width, total_width // width))
            
            result = {
                'file': image_path,
                'total_size': (total_width, total_height),
                'possible_frame_widths': suggested,
                'detected': len(suggested) > 0
            }
            
            if suggested:
                print(f"\n✓ {image_path}")
                print(f"  Size: {total_width}x{total_height}px")
                print(f"  Possible frame sizes:")
                for width, count in suggested:
                    print(f"    {width}px wide: {count} frames")
            else:
                print(f"\n? {image_path}")
                print(f"  Size: {total_width}x{total_height}px")
                print(f"  No standard frame widths detected")
            
            return result
        else:
            num_frames = total_width // frame_width
            result = {
                'file': image_path,
                'total_size': (total_width, total_height),
                'frame_width': frame_width,
                'num_frames': num_frames,
                'frame_height': total_height
            }
            print(f"\n✓ {image_path}")
            print(f"  Frames: {num_frames} at {frame_width}px width")
            print(f"  Frame size: {frame_width}x{total_height}px")
            return result
            
    except FileNotFoundError:
        print(f"\n✗ {image_path} - FILE NOT FOUND")
        return {'file': image_path, 'error': 'not_found'}
    except Exception as e:
        print(f"\n✗ {image_path} - Error: {e}")
        return {'file': image_path, 'error': str(e)}


# ============ USAGE EXAMPLE ============
if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((1, 1))  # Hidden window for loading images
    
    print("\n" + "=" * 60)
    print("LEVEL 2 ENEMY ANIMATION FRAME ANALYZER")
    print("=" * 60)
    
    # First, check existing Level 1 animations for reference
    print("\n📊 CHECKING LEVEL 1 ENEMY ANIMATIONS (for reference)")
    print("-" * 60)
    
    analyze_sprite_sheet("assets/Level1/Warrior/Run.png")
    analyze_sprite_sheet("assets/Level1/Warrior/Attack.png")
    analyze_sprite_sheet("assets/Level1/Archer/Run.png")
    analyze_sprite_sheet("assets/Level1/Archer/Attack.png")
    
    # Now check Level 2 animations (if they exist)
    print("\n\n📊 CHECKING LEVEL 2 ENEMY ANIMATIONS")
    print("-" * 60)
    
    # When animation assets are ready, uncomment these:
    analyze_sprite_sheet("assets/Level2/Wolf/Idle.png")
    analyze_sprite_sheet("assets/Level2/Wolf/Run.png")
    analyze_sprite_sheet("assets/Level2/Wolf/Attack.png")
    
    analyze_sprite_sheet("assets/Level2/ShadowCreature/Idle.png")
    analyze_sprite_sheet("assets/Level2/ShadowCreature/Run.png")
    analyze_sprite_sheet("assets/Level2/ShadowCreature/Attack.png")
    
    analyze_sprite_sheet("assets/Level2/DarkEnchanter/Idle.png")
    analyze_sprite_sheet("assets/Level2/DarkEnchanter/Run.png")
    analyze_sprite_sheet("assets/Level2/DarkEnchanter/Attack.png")
    
    print("\n" + "=" * 60)
    print("\n📝 TODO: Add Level 2 enemy animation sprite sheets")
    print("\nExpected structure:")
    print("  assets/Level2/")
    print("    Wolf/")
    print("      Idle.png")
    print("      Run.png")
    print("      Attack.png")
    print("    ShadowCreature/")
    print("      Idle.png")
    print("      Run.png")
    print("      Attack.png")
    print("    DarkEnchanter/")
    print("      Idle.png")
    print("      Run.png")
    print("      Attack.png")
    print("\nOnce sprites are added, update the ANIM dictionaries at the top")
    print("of this file with the correct frame_width values.")
    print("=" * 60)

