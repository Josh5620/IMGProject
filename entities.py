"""
entities.py - Refactored Entity System with Time-Based Animation and Movement

Main improvements:
- Delta time (dt) based movement and animations
- Cached image loading with convert_alpha()
- Centralized constants
- Fixed bugs (level.ground_scroll, memory leaks, alpha rendering)
- Improved naming and documentation
- Removed dead code and commented junk
"""

import pygame
import math
from typing import List, Dict, Tuple, Optional
from blocks import Ice, Spikes, block, end
from weapons.weapons import WeaponSystem, handle_projectile_collisions
from weapons.projectiles import ProjectileManager
from particles import ScreenDropletParticle


# =====================================================================
# CONSTANTS - Centralized configuration
# =====================================================================

class GameConstants:
    """Centralized game constants for entities."""
    
    # Player rendering
    FRAME_TARGET_SIZE: Tuple[int, int] = (64, 64)
    
    # Player physics
    GRAVITY: float = 0.7
    JUMP_VELOCITY: float = -12.0
    DOUBLE_JUMP_MULTIPLIER: float = 0.8
    BASE_SPEED: float = 3.5
    FAST_FALL_SPEED: float = 3.5
    
    # Player animation timings (in frames, will be converted to time-based)
    ATTACK_DURATION_FRAMES: int = 18
    HURT_DURATION_FRAMES: int = 12
    INVULNERABILITY_DURATION_MS: int = 2000
    BLINK_INTERVAL_MS: int = 100
    
    # Player combat
    MAX_AMMO: int = 20
    SHOOTING_COOLDOWN_FRAMES: int = 30
    MAX_LIVES: int = 10
    
    # Powerup timings (in frames at 60 FPS)
    SPEED_BOOST_DURATION: int = 600  # 10 seconds
    DAMAGE_BOOST_DURATION: int = 600  # 10 seconds
    SHIELD_DURATION: int = 300  # 5 seconds
    
    # Powerup values
    SPEED_BOOST_MULTIPLIER: float = 1.5
    DAMAGE_BOOST_MULTIPLIER: float = 2.0
    HEALTH_RESTORE_AMOUNT: int = 2
    AMMO_RESTORE_AMOUNT: int = 10
    
    # Enemy defaults
    ENEMY_SIZE: Tuple[int, int] = (48, 48)
    ENEMY_MAX_HEALTH: int = 100
    ENEMY_SPEED: float = 2.0
    ENEMY_PATROL_RANGE: int = 200
    ENEMY_ATTACK_RANGE: int = 150
    ENEMY_MELEE_RANGE: int = 60
    ENEMY_PROJECTILE_SPEED: float = 4.0
    
    # Powerup rendering
    POWERUP_SIZE: Tuple[int, int] = (40, 40)
    POWERUP_BOB_AMPLITUDE: int = 8
    POWERUP_PULSE_SCALE: float = 0.2
    POWERUP_PARTICLE_COUNT: int = 15
    POWERUP_PARTICLE_LIFETIME: int = 30
    
    # Visual effects
    MAX_SLOWDOWN_PARTICLES: int = 40
    SCREEN_BOUNDS_MARGIN: int = 50


# =====================================================================
# SPRITE ANIMATION SYSTEM
# =====================================================================

# Animation manifest - maps state names to sprite sheet files
ANIM_MANIFEST: Dict[str, Dict] = {
    "idle":      {"file": "assets/redhood/idle.png",      "frame_count": 18},
    "run":       {"file": "assets/redhood/run.png",       "frame_width": 32},
    "jump":      {"file": "assets/redhood/jump.png",      "frame_width": 32},
    "fall":      {"alias": "jump"},
    "light_atk": {"alias": "idle"},  # Use idle animation for attack - looks more natural
    "hurt":      {"file": "assets/redhood/hurt.png",      "frame_count": 6},
    # Compatibility aliases
    "attack":        {"alias": "idle"},  # Use idle animation
    "charge":        {"alias": "idle"},  # Use idle animation
    "jump_start":    {"alias": "jump"},
    "jump_to_fall":  {"alias": "jump"},
    "wall_jump":     {"alias": "jump"},
}


def _slice_one_row(
    sheet: pygame.Surface,
    *,
    frame_width: Optional[int] = None,
    frame_count: Optional[int] = None,
    scale_to: Optional[Tuple[int, int]] = GameConstants.FRAME_TARGET_SIZE
) -> List[pygame.Surface]:
    """
    Slice a horizontal sprite sheet into individual frames.
    
    Args:
        sheet: The sprite sheet surface
        frame_width: Width of each frame (auto-calculated if None)
        frame_count: Number of frames (auto-calculated if None)
        scale_to: Target size for scaled frames
        
    Returns:
        List of frame surfaces with convert_alpha() applied
    """
    height = sheet.get_height()
    width = sheet.get_width()
    
    if frame_width is None and frame_count is None:
        frame_width = height  # Square frames fallback
    
    if frame_width is not None:
        num_frames = max(1, width // frame_width)
    else:
        num_frames = max(1, frame_count)
        frame_width = width // num_frames
    
    frames = []
    for i in range(num_frames):
        rect = pygame.Rect(i * frame_width, 0, frame_width, height)
        frame = sheet.subsurface(rect).copy()
        
        if scale_to:
            frame = pygame.transform.scale(frame, scale_to)
        
        # OPTIMIZATION: Cache with convert_alpha()
        frame = frame.convert_alpha()
        frames.append(frame)
    
    return frames


def build_state_animations_from_manifest(
    manifest: Dict[str, Dict]
) -> Dict[str, List[pygame.Surface]]:
    """
    Build animation dictionary from manifest with image caching.
    
    Args:
        manifest: Animation specification dictionary
        
    Returns:
        Dictionary mapping state names to frame lists
        
    Raises:
        FileNotFoundError: If sprite sheet file not found
        RuntimeError: If sprite sheet fails to load
    """
    cache: Dict[str, List[pygame.Surface]] = {}
    anims: Dict[str, List[pygame.Surface]] = {}

    def resolve(state: str) -> List[pygame.Surface]:
        """Recursively resolve animation state (handles aliases)."""
        if state in anims:
            return anims[state]
        
        spec = manifest.get(state)
        if not spec:
            anims[state] = []
            return anims[state]
        
        if "alias" in spec:
            anims[state] = resolve(spec["alias"])
            return anims[state]
        
        file = spec["file"]
        frame_width = spec.get("frame_width")
        frame_count = spec.get("frame_count")
        
        if file not in cache:
            try:
                # OPTIMIZATION: Load and convert_alpha() immediately
                sheet = pygame.image.load(file).convert_alpha()
            except FileNotFoundError as exc:
                raise FileNotFoundError(f"Sprite sheet not found: {file}") from exc
            except pygame.error as exc:
                raise RuntimeError(f"Failed to load sprite sheet '{file}': {exc}") from exc
            
            cache[file] = _slice_one_row(sheet, frame_width=frame_width, frame_count=frame_count)
        
        anims[state] = cache[file]
        return anims[state]

    for key in manifest.keys():
        resolve(key)
    
    return anims


# =====================================================================
# SOUND EFFECTS
# =====================================================================

pygame.mixer.init()

# Load and configure global sounds
FISH_THROW_SOUND = pygame.mixer.Sound("assets/SFX/FishThrow.mp3")
FISH_THROW_SOUND.set_volume(0.3)

SCRATCH_SOUND = pygame.mixer.Sound("assets/SFX/ScratchAttack.mp3")
SCRATCH_SOUND.set_volume(0.3)

CAT_HURT_SOUND = pygame.mixer.Sound("assets/SFX/CatDamaged.mp3")
CAT_HURT_SOUND.set_volume(0.3)


# =====================================================================
# MAIN CHARACTER CLASS
# =====================================================================

class MainCharacter(WeaponSystem):
    """
    Player character with animation, physics, combat, and powerup systems.
    
    Features:
    - Time-based animation and movement (dt support)
    - Double jump mechanics
    - Weapon system integration (melee + projectiles)
    - Powerup effects (health, speed, damage, shield, ammo)
    - Invulnerability frames
    - Visual particle effects
    """

    def __init__(self, x: float, y: float):
        """
        Initialize the main character.
        
        Args:
            x: Initial x position
            y: Initial y position
        """
        self.x = x
        self.y = y
        
        # Initialize weapon system
        self.init_weapon_system()
        
        # Initialize projectile manager
        self.projectile_manager = ProjectileManager()
        self.enemies: List['Enemy'] = []
        
        # Load and cache sprite animations
        self.anims = build_state_animations_from_manifest(ANIM_MANIFEST)
        self.image = self._get_initial_image()
        self.rect = self.image.get_rect(topleft=(x, y))
        
        # Animation state
        self.anim_tick = 0
        self.anim_speed = 3  # Frames per animation frame
        self.facing_right = True
        self.scroll_speed = 0
        
        # Timed animation states
        self.attack_timer = 0
        self.hurt_timer = 0
        
        # Physics
        self.y_gravity = GameConstants.GRAVITY
        self.jump_height = abs(GameConstants.JUMP_VELOCITY)
        self.y_velocity = 0.0
        self.jumping = False
        self.on_ground = True
        self.double_jump_available = True
        self.double_jump_used = False
        
        # Game state
        self.visible = True
        self.invulnerable = False
        self.invulnerable_start = 0
        self.lives = 5
        self.won = False
        
        # Ammo system
        self.max_ammo = GameConstants.MAX_AMMO
        self.current_ammo = GameConstants.MAX_AMMO
        self.shooting_cooldown = 0
        self.cooldown_time = GameConstants.SHOOTING_COOLDOWN_FRAMES
        
        # Powerup effects
        self.speed_boost = 1.0
        self.damage_boost = 1.0
        self.shield_active = False
        self.powerup_timers: Dict[str, int] = {
            "speed": 0,
            "damage": 0,
            "shield": 0
        }
        
        # Movement
        self.base_speed = GameConstants.BASE_SPEED
        self.slow_until = 0
        self.slowdown_particles: List[ScreenDropletParticle] = []

    def _get_initial_image(self) -> pygame.Surface:
        """
        Get the first available animation frame.
        
        Returns:
            Initial sprite surface
            
        Raises:
            RuntimeError: If no animations are available
        """
        if not self.anims:
            raise RuntimeError(
                "Failed to load MainCharacter animations; ensure assets/redhood spritesheets are available."
            )

        idle_frames = self.anims.get("idle", [])
        if idle_frames:
            return idle_frames[0]

        for frames in self.anims.values():
            if frames:
                return frames[0]

        raise RuntimeError("No animation frames available for MainCharacter.")

    @staticmethod
    def _resolve_rect(obj) -> pygame.Rect:
        """
        Extract pygame.Rect from object or rect-like tuple.
        
        Args:
            obj: Object with get_rect() method or rect-like data
            
        Returns:
            pygame.Rect instance
        """
        if hasattr(obj, "get_rect"):
            rect = obj.get_rect()
        else:
            rect = obj

        return rect if isinstance(rect, pygame.Rect) else pygame.Rect(rect)
      
    def _anim_index(self, state: str) -> int:
        """
        Calculate current animation frame index for given state.
        
        Args:
            state: Animation state name
            
        Returns:
            Frame index (0 if state not found)
        """
        if not self.anims or state not in self.anims:
            return 0
        
        frames = self.anims[state]
        if not frames:
            return 0
        
        return (self.anim_tick // self.anim_speed) % len(frames)

    def update_animation(self, keys: pygame.key.ScancodeWrapper):
        """
        Update sprite animation based on current state and input.
        
        Args:
            keys: Pygame key state array
        """
        self.anim_tick = (self.anim_tick + 1) % 10_000_000

        # Priority 1: Timed non-looping states
        if self.hurt_timer > 0 and self.anims.get("hurt"):
            state = "hurt"
        elif self.attack_timer > 0 and self.anims.get("light_atk"):
            state = "light_atk"
        else:
            # Priority 2: Weapon system override
            weapon_anim = self.get_current_weapon_animation_state()
            if weapon_anim:
                if weapon_anim in ("attack", "charge", "light_atk"):
                    state = "light_atk"
                else:
                    state = weapon_anim if weapon_anim in self.anims else "idle"
            else:
                # Priority 3: Movement-based animation
                if not self.on_ground:
                    state = "jump" if self.y_velocity < 0 else "fall"
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
        if self.anims.get(state):
            img = self.anims[state][idx]
            self.image = img if self.facing_right else pygame.transform.flip(img, True, False)
    
    def move(self, dx: float, dy: float, obstacles: Optional[List] = None):
        """
        Move character with collision detection.
        
        Args:
            dx: Delta x movement
            dy: Delta y movement
            obstacles: List of obstacles to check collision against
        """
        old_x, old_y = self.rect.x, self.rect.y
        
        # Horizontal movement
        if dx != 0:
            self.rect.x += dx
            if obstacles and self.check_collision_with_obstacles(obstacles):
                self.rect.x = old_x

        # Vertical movement
        if dy != 0:
            self.rect.y += dy
            if obstacles and self.check_collision_with_obstacles(obstacles):
                self.rect.y = old_y

    def check_collision_with_obstacles(self, obstacles: List) -> bool:
        """
        Check collision with obstacles and trigger special block effects.
        
        Args:
            obstacles: List of obstacle objects
            
        Returns:
            True if colliding with solid obstacle
        """
        for obstacle in obstacles:
            obstacle_rect = self._resolve_rect(obstacle)

            if self.rect.colliderect(obstacle_rect):
                if isinstance(obstacle, (Spikes, end, Ice)):
                    obstacle.collideHurt(self)

                if getattr(obstacle, 'solid', True):
                    return True

        return False

    def jump(self):
        """Initiate first jump."""
        if self.on_ground:
            self.on_ground = False
            self.jumping = True
            self.y_velocity = GameConstants.JUMP_VELOCITY
            self.double_jump_used = False
            
            if self.anims and self.anims.get("jump_start"):
                self.image = self.anims["jump_start"][0]
    
    def double_jump(self):
        """Perform double jump if available."""
        if not self.on_ground and self.double_jump_available and not self.double_jump_used:
            self.y_velocity = GameConstants.JUMP_VELOCITY * GameConstants.DOUBLE_JUMP_MULTIPLIER
            self.double_jump_used = True
            
            if self.anims and self.anims.get("jump"):
                self.image = self.anims["jump"][0]
        
    def update(self, keys: pygame.key.ScancodeWrapper, obstacles: List, enemies: List['Enemy'], dt: float = 1.0):
        """
        Main update loop with delta time support.
        
        Args:
            keys: Pygame key state array
            obstacles: List of collidable obstacles
            enemies: List of enemy entities
            dt: Delta time multiplier (1.0 = 60 FPS)
        """
        self.update_weapon_system()
        self.enemies = enemies
        
        # Build collidable list (without level.ground_scroll - BUG FIX)
        all_collidables = obstacles.copy()
        for enemy in enemies:
            all_collidables.append(enemy.rect)
        
        # Update speed boost timing
        if pygame.time.get_ticks() > self.slow_until:
            self.speed_boost = 1.0

        actual_speed = self.base_speed * self.speed_boost * dt

        # Input handling with time-based movement
        if keys[pygame.K_LEFT]:
            self.move(-actual_speed, 0, all_collidables)
            self.scroll_speed = -0.5
        if keys[pygame.K_RIGHT]:
            self.move(actual_speed, 0, all_collidables)
            self.scroll_speed = 0.5
        if keys[pygame.K_UP]:
            self.jump()
        if keys[pygame.K_SPACE]:
            self.double_jump()
        if keys[pygame.K_DOWN]:
            self.move(0, GameConstants.FAST_FALL_SPEED * dt, all_collidables)

        # Update cooldowns with dt
        if self.shooting_cooldown > 0:
            self.shooting_cooldown -= dt

        self.update_powerup_effects(dt)

        # Melee attack
        if keys[pygame.K_a]:
            if self.attack_timer <= 0:
                hit_enemies = self.melee_attack(self.enemies, obstacles)
                SCRATCH_SOUND.play()
                self.attack_timer = GameConstants.ATTACK_DURATION_FRAMES
                
        # Decrement timers with dt
        if self.attack_timer > 0:
            self.attack_timer -= dt
        if self.hurt_timer > 0:
            self.hurt_timer -= dt

        # Straight projectile
        if keys[pygame.K_s]:
            if self.can_shoot():
                projectile = self.shoot_projectile()
                if projectile:
                    self.projectile_manager.add_projectile(projectile)
                    self.consume_ammo()
                    FISH_THROW_SOUND.play()
        
        # Charged projectile
        if keys[pygame.K_c]:
            if not self.is_charging and self.can_shoot():
                self.start_charging()
        else:
            if self.is_charging:
                try:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    projectile = self.stop_charging_and_shoot(mouse_x, mouse_y)
                    if projectile:
                        self.projectile_manager.add_projectile(projectile)
                        self.consume_ammo()
                    FISH_THROW_SOUND.play()
                except:
                    self.stop_charging()

        # Update animation and physics
        self.update_animation(keys)
        self.apply_gravity(all_collidables, dt)
        
        # Update projectiles
        self.projectile_manager.update()
        
        # Handle projectile collisions
        handle_projectile_collisions(
            self.projectile_manager,
            self,
            self.enemies,
            obstacles
        )
    
    def can_shoot(self) -> bool:
        """Check if player can shoot."""
        return self.current_ammo > 0 and self.shooting_cooldown <= 0
    
    def consume_ammo(self):
        """Consume one ammo and set cooldown."""
        if self.current_ammo > 0:
            self.current_ammo -= 1
            self.shooting_cooldown = self.cooldown_time
    
    def reload_ammo(self, amount: Optional[int] = None):
        """Reload ammo (used by powerups)."""
        if amount is None:
            amount = self.max_ammo
        self.current_ammo = min(self.current_ammo + amount, self.max_ammo)
    
    def update_powerup_effects(self, dt: float = 1.0):
        """
        Update active powerup effects with delta time.
        
        Args:
            dt: Delta time multiplier
        """
        for effect, timer in list(self.powerup_timers.items()):
            if timer > 0:
                self.powerup_timers[effect] -= dt
                if self.powerup_timers[effect] <= 0:
                    if effect == "speed":
                        self.speed_boost = 1.0
                    elif effect == "damage":
                        self.damage_boost = 1.0
                    elif effect == "shield":
                        self.shield_active = False
    
    def apply_powerup(self, powerup_type: str):
        """
        Apply powerup effect to player.
        
        Args:
            powerup_type: Type of powerup (health, speed, damage, shield, ammo)
        """
        if powerup_type == "health":
            self.lives = min(self.lives + GameConstants.HEALTH_RESTORE_AMOUNT, GameConstants.MAX_LIVES)
        
        elif powerup_type == "speed":
            self.speed_boost = GameConstants.SPEED_BOOST_MULTIPLIER
            self.powerup_timers["speed"] = GameConstants.SPEED_BOOST_DURATION
        
        elif powerup_type == "damage":
            self.damage_boost = GameConstants.DAMAGE_BOOST_MULTIPLIER
            self.powerup_timers["damage"] = GameConstants.DAMAGE_BOOST_DURATION
        
        elif powerup_type == "shield":
            self.shield_active = True
            self.powerup_timers["shield"] = GameConstants.SHIELD_DURATION
        
        elif powerup_type == "ammo":
            self.reload_ammo(GameConstants.AMMO_RESTORE_AMOUNT)
    
    def take_damage(self, damage_amount: int = 1) -> bool:
        """
        Take damage with shield protection.
        
        Args:
            damage_amount: Amount of damage to take
            
        Returns:
            True if damage was taken, False if blocked
        """
        if self.invulnerable or self.shield_active:
            return False
        
        self.lives -= damage_amount
        if self.lives <= 0:
            self.lives = 0
        else:
            CAT_HURT_SOUND.play()
            self.start_invulnerability()
            self.hurt_timer = GameConstants.HURT_DURATION_FRAMES

        return True
    
    def draw_powerup_effects(self, surface: pygame.Surface):
        """
        Draw visual effects for active powerups.
        
        Args:
            surface: Surface to draw on
        """
        player_center = self.rect.center
        current_time = pygame.time.get_ticks()
        
        # Shield effect
        if self.shield_active:
            shield_pulse = math.sin(current_time * 0.01) * 0.3 + 0.7
            shield_radius = int(60 * shield_pulse)
            
            for i in range(3):
                radius = shield_radius + i * 3
                pygame.draw.circle(surface, (0, 150, 255), player_center, radius, 2)
            
            pygame.draw.circle(surface, (150, 200, 255), player_center, shield_radius - 8, 1)
        
        # Speed effect
        if self.speed_boost > 1.0:
            speed_intensity = min((self.speed_boost - 1.0) * 2, 1.0)
            
            for i in range(4):
                trail_x = player_center[0] - (i + 1) * 10 * speed_intensity
                trail_size = 8 - i * 2
                pygame.draw.circle(surface, (0, 255, 100), (trail_x, player_center[1]), trail_size, 1)
            
            for i in range(6):
                line_length = 15 + i * 3
                line_y = player_center[1] + (i - 3) * 5
                line_start = (player_center[0] - line_length, line_y)
                line_end = (player_center[0] - 5, line_y)
                pygame.draw.line(surface, (100, 255, 150), line_start, line_end, 2)
        
        # Damage boost effect
        if self.damage_boost > 1.0:
            damage_intensity = min(self.damage_boost - 1.0, 1.0)
            damage_pulse = math.sin(current_time * 0.008) * 0.3 + 0.7
            aura_radius = int(55 * damage_pulse * damage_intensity)
            
            for i in range(3):
                radius = aura_radius - i * 5
                if radius > 0:
                    color_intensity = int(255 * damage_intensity)
                    aura_color = (color_intensity, max(50, color_intensity - 100), 0)
                    pygame.draw.circle(surface, aura_color, player_center, radius, 1)
            
            for i in range(8):
                angle = (current_time * 0.008 + i * 45) % 360
                spark_distance = 25 + math.sin(current_time * 0.03 + i) * 8
                spark_x = player_center[0] + int(spark_distance * math.cos(math.radians(angle)))
                spark_y = player_center[1] + int(spark_distance * math.sin(math.radians(angle))) - 5
                
                spark_colors = [(255, 200, 0), (255, 100, 0), (255, 50, 0)]
                spark_color = spark_colors[i % 3]
                pygame.draw.circle(surface, spark_color, (spark_x, spark_y), 3)
                pygame.draw.circle(surface, (255, 255, 100), (spark_x, spark_y), 1)
    
    def draw_with_effects(self, surface: pygame.Surface):
        """
        Draw player with all visual effects.
        
        Args:
            surface: Surface to draw on
        """
        self.draw_powerup_effects(surface)
        surface.blit(self.image, self.rect)

    def check_collision(self, all_collidables: List) -> bool:
        """
        Check collision for physics (landing on platforms).
        
        Args:
            all_collidables: List of collidable objects
            
        Returns:
            True if collision occurred
        """
        for entity in all_collidables:
            entity_rect = self._resolve_rect(entity)

            if self.rect.colliderect(entity_rect):
                if isinstance(entity, (Spikes, Ice, end)):
                    entity.collideHurt(self)
                
                if getattr(entity, 'solid', True):
                    if self.y_velocity > 0:
                        self.rect.bottom = entity_rect.top
                        self.jumping = False
                        self.on_ground = True
                        self.y_velocity = 0
                        return True 

                    elif self.y_velocity < 0:
                        self.rect.top = entity_rect.bottom
                        self.y_velocity = 0
                        return True 

        # Check if still on ground
        if self.on_ground:
            ground_check_rect = pygame.Rect(self.rect.x, self.rect.y + 1, self.rect.width, 1)
            still_on_ground = False
            
            for block_obj in all_collidables:
                block_rect = self._resolve_rect(block_obj)

                if getattr(block_obj, 'solid', True) and ground_check_rect.colliderect(block_rect):
                    still_on_ground = True
                    if isinstance(block_obj, Ice):
                        block_obj.collideHurt(self)
                    break 
            
            if not still_on_ground:
                self.on_ground = False
        
        return False

    def apply_gravity(self, obstacles: List, dt: float = 1.0):
        """
        Apply gravity and update vertical position.
        
        Args:
            obstacles: List of collidable obstacles
            dt: Delta time multiplier
        """
        if not self.check_collision_with_obstacles(obstacles):
            self.on_ground = False
        
        if not self.on_ground:
            self.y_velocity += self.y_gravity * dt
        
        if self.y_velocity != 0:
            self.rect.y += self.y_velocity * dt
            self.check_collision(obstacles)
        
        if self.on_ground:
            self.double_jump_used = False
            
    def start_invulnerability(self):
        """Activate invulnerability frames."""
        self.invulnerable = True
        self.invulnerable_start = pygame.time.get_ticks()

    def draw(self, surface: pygame.Surface):
        """
        Draw character with invulnerability blinking and effects.
        
        Args:
            surface: Surface to draw on
        """
        if self.invulnerable:
            now = pygame.time.get_ticks()
            if now - self.invulnerable_start >= GameConstants.INVULNERABILITY_DURATION_MS:
                self.invulnerable = False
            
            time_since_start = now - self.invulnerable_start
            should_show = (time_since_start // GameConstants.BLINK_INTERVAL_MS) % 2 == 0
            
            if should_show and self.visible:
                surface.blit(self.image, self.rect)
        else:
            if self.visible:
                on_screen_pos = (self.rect.x, self.rect.y)
                surface.blit(self.image, self.rect)
                self.draw_slowdown_effect(surface, on_screen_pos)
        
        # Draw weapon effects
        camera_offset = (0, 0)
        self.draw_weapon_effects(surface, camera_offset)
        
        # Draw projectiles
        self.projectile_manager.draw(surface)
            
    def get_position(self) -> Tuple[float, float]:
        """Get character position."""
        return self.rect.topleft

    def draw_slowdown_effect(self, surface: pygame.Surface, on_screen_pos: Tuple[float, float]):
        """
        Draw slowdown particle effect.
        
        Args:
            surface: Surface to draw on
            on_screen_pos: Screen position for particles
        """
        # Spawn particles when slowed
        if self.speed_boost < 1.0 and len(self.slowdown_particles) < GameConstants.MAX_SLOWDOWN_PARTICLES:
            if pygame.time.get_ticks() % 10 == 0:  # Throttle particle creation
                self.slowdown_particles.append(ScreenDropletParticle())

        anchor_x = on_screen_pos[0] + self.rect.width / 2
        anchor_y = on_screen_pos[1] + self.rect.height / 2

        active_particles = []
        for particle in self.slowdown_particles:
            particle.update()

            draw_x = anchor_x + particle.relative_x
            draw_y = anchor_y + particle.relative_y

            pygame.draw.circle(surface, particle.color, (int(draw_x), int(draw_y)), particle.size)

            if particle.lifespan > 0:
                active_particles.append(particle)

        self.slowdown_particles = active_particles


# =====================================================================
# ENEMY CLASS
# =====================================================================

class Enemy:
    """
    Enemy with AI behaviors and time-based updates.
    
    AI Types:
    - idle: Stays in place
    - patrol: Moves back and forth
    - chase: Follows player
    - ranged: Keeps distance and shoots
    - boss: Multi-phase behavior
    """
    
    def __init__(self, x: float, y: float, ai_type: str = "idle"):
        """
        Initialize enemy.
        
        Args:
            x: Initial x position
            y: Initial y position
            ai_type: AI behavior type
        """
        self.rect = pygame.Rect(x, y, *GameConstants.ENEMY_SIZE)
        self.x = x
        self.y = y
        self.health = GameConstants.ENEMY_MAX_HEALTH
        self.max_health = GameConstants.ENEMY_MAX_HEALTH
        self.speed = GameConstants.ENEMY_SPEED
        self.ai_type = ai_type
        self.alive = True
        self.direction = 1
        self.ai_timer = 0.0
        self.target = None
        self.patrol_start = x
        self.patrol_range = GameConstants.ENEMY_PATROL_RANGE
        self.attack_range = GameConstants.ENEMY_ATTACK_RANGE
        self.attack_cooldown = 0.0
        self.melee_range = GameConstants.ENEMY_MELEE_RANGE
        self.color = (255, 100, 100)
        
        self.projectiles: List[Dict] = []
        
        # Create placeholder image with convert_alpha()
        self.image = pygame.Surface(GameConstants.ENEMY_SIZE, pygame.SRCALPHA)
        self.image.fill(self.color)
        self.image = self.image.convert_alpha()
        self.image = pygame.Surface(GameConstants.ENEMY_SIZE, pygame.SRCALPHA)
        self.image.fill(self.color)
        self.image = self.image.convert_alpha()
        
    def update(self, player: MainCharacter, dt: float = 1.0):
        """
        Update enemy with delta time support.
        
        Args:
            player: Player character
            dt: Delta time multiplier
        """
        if not self.alive:
            return
            
        self.ai_timer += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        
        # AI behaviors
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
        
        # Update projectiles (MEMORY LEAK FIX)
        active_projectiles = []
        for projectile in self.projectiles:
            projectile['x'] += projectile['dx'] * dt
            projectile['y'] += projectile['dy'] * dt
            
            # Remove off-screen projectiles
            if (abs(projectile['x']) > 1300 or abs(projectile['y']) > 800):
                continue
            
            # Check player collision
            proj_rect = pygame.Rect(projectile['x'], projectile['y'], 8, 8)
            if proj_rect.colliderect(player.rect):
                self.damage_player(player)
                continue
            
            active_projectiles.append(projectile)
        
        self.projectiles = active_projectiles
    
    def _ai_idle(self, player: MainCharacter, dt: float):
        """Idle AI - stays in place."""
        if self.ai_timer > 120:
            self.direction *= -1
            self.ai_timer = 0
    
    def _ai_patrol(self, player: MainCharacter, dt: float):
        """Patrol AI - moves back and forth."""
        self.rect.x += self.speed * self.direction * dt
        
        if self.rect.x <= self.patrol_start - self.patrol_range or \
           self.rect.x >= self.patrol_start + self.patrol_range:
            self.direction *= -1
    
    def _ai_chase(self, player: MainCharacter, dt: float):
        """Chase AI - follows player."""
        distance = abs(player.rect.centerx - self.rect.centerx)
        
        if distance < 300:
            if player.rect.centerx < self.rect.centerx:
                self.direction = -1
                self.rect.x -= self.speed * dt
            else:
                self.direction = 1
                self.rect.x += self.speed * dt
            
            if distance < self.melee_range and self.attack_cooldown <= 0:
                self._attack_melee(player)
                self.attack_cooldown = 90
    
    def _ai_ranged(self, player: MainCharacter, dt: float):
        """Ranged AI - keeps distance and shoots."""
        distance = abs(player.rect.centerx - self.rect.centerx)
        
        if distance < 100:
            if player.rect.centerx < self.rect.centerx:
                self.direction = 1
                self.rect.x += self.speed * dt
            else:
                self.direction = -1
                self.rect.x -= self.speed * dt
        elif distance > 200:
            if player.rect.centerx < self.rect.centerx:
                self.direction = -1
                self.rect.x -= self.speed * dt
            else:
                self.direction = 1
                self.rect.x += self.speed * dt
        
        if self.attack_range < distance < 250 and self.attack_cooldown <= 0:
            self._attack_ranged(player)
            self.attack_cooldown = 120
    
    def _ai_boss(self, player: MainCharacter, dt: float):
        """Boss AI - multi-phase behavior."""
        if self.health > self.max_health * 0.7:
            self._ai_chase(player, dt * 0.5)
        elif self.health > self.max_health * 0.3:
            self._ai_ranged(player, dt * 1.5)
            if self.attack_cooldown <= 0:
                self._attack_ranged(player)
                self.attack_cooldown = 60
        else:
            self._ai_chase(player, dt * 2.0)
    
    def _attack_ranged(self, player: MainCharacter):
        """Fire projectile at player."""
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            dx /= distance
            dy /= distance
            
            projectile = {
                'x': float(self.rect.centerx),
                'y': float(self.rect.centery),
                'dx': dx * GameConstants.ENEMY_PROJECTILE_SPEED,
                'dy': dy * GameConstants.ENEMY_PROJECTILE_SPEED
            }
            self.projectiles.append(projectile)
    
    def _attack_melee(self, player: MainCharacter):
        """Melee attack player."""
        self.damage_player(player)
    
    def damage_player(self, player: MainCharacter):
        """Deal damage to player."""
        player.take_damage(1)
    
    def set_ai_type(self, ai_type: str):
        """Change enemy AI behavior."""
        self.ai_type = ai_type
        self.ai_timer = 0
    
    def take_damage(self, damage: int):
        """Handle taking damage."""
        self.health -= damage
        if self.health <= 0:
            self.alive = False
    
    def draw(self, surface: pygame.Surface, debug_mode: bool = False):
        """
        Draw enemy with health bar and debug info.
        
        Args:
            surface: Surface to draw on
            debug_mode: Show debug information
        """
        if not self.alive:
            return
            
        surface.blit(self.image, self.rect)
        
        # Draw projectiles
        for projectile in self.projectiles:
            pygame.draw.circle(surface, (255, 0, 0), (int(projectile['x']), int(projectile['y'])), 4)
        
        # Health bar
        if self.health < self.max_health:
            bar_width = GameConstants.ENEMY_SIZE[0]
            bar_height = 4
            bar_x = self.rect.x
            bar_y = self.rect.y - 10
            
            pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
            health_width = int((self.health / self.max_health) * bar_width)
            pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, health_width, bar_height))
        
        if debug_mode:
            font = pygame.font.Font(None, 24)
            text = font.render(self.ai_type, True, (255, 255, 255))
            surface.blit(text, (self.rect.x, self.rect.y - 30))
            
            pygame.draw.line(surface, (255, 255, 0), 
                           self.rect.center, 
                           (self.rect.centerx + self.direction * 30, self.rect.centery), 3)


# =====================================================================
# POWERUP CLASS
# =====================================================================

class Powerup:
    """
    Collectible powerup with visual effects and time-based animations.
    
    Types: health, speed, damage, shield, ammo
    """
    
    # Color schemes for each powerup type
    COLORS = {
        "health": {"main": (255, 50, 50), "glow": (255, 100, 100), "bright": (255, 200, 200)},
        "speed": {"main": (50, 255, 50), "glow": (100, 255, 100), "bright": (200, 255, 200)},
        "damage": {"main": (255, 255, 50), "glow": (255, 255, 100), "bright": (255, 255, 200)},
        "shield": {"main": (50, 50, 255), "glow": (100, 100, 255), "bright": (200, 200, 255)},
        "ammo": {"main": (255, 50, 255), "glow": (255, 100, 255), "bright": (255, 200, 255)}
    }
    
    def __init__(self, x: float, y: float, powerup_type: str = "health"):
        """
        Initialize powerup.
        
        Args:
            x: X position
            y: Y position
            powerup_type: Type of powerup
        """
        self.rect = pygame.Rect(x, y, *GameConstants.POWERUP_SIZE)
        self.powerup_type = powerup_type
        self.collected = False
        self.bob_timer = 0.0
        self.original_y = y
        self.rotation = 0.0
        self.pulse_timer = 0.0
        self.collection_particles: List[Dict] = []
        
        self.color_set = self.COLORS.get(powerup_type, {
            "main": (255, 255, 255), 
            "glow": (200, 200, 200), 
            "bright": (255, 255, 255)
        })
    
    def update(self, player: MainCharacter, dt: float = 1.0):
        """
        Update powerup with delta time.
        
        Args:
            player: Player character
            dt: Delta time multiplier
        """
        if self.collected:
            self.update_collection_particles(dt)
            return
            
        # Bobbing animation
        self.bob_timer += dt * 0.15
        self.rect.y = self.original_y + int(math.sin(self.bob_timer) * GameConstants.POWERUP_BOB_AMPLITUDE)
        
        # Rotation animation
        self.rotation += dt * 2
        if self.rotation >= 360:
            self.rotation = 0
        
        # Pulsing effect
        self.pulse_timer += dt * 0.2
        
        # Collision check
        if self.rect.colliderect(player.rect):
            self.create_collection_particles()
            self.apply_effect(player)
            self.collected = True
    
    def apply_effect(self, player: MainCharacter):
        """Apply powerup effect to player."""
        player.apply_powerup(self.powerup_type)
    
    def create_collection_particles(self):
        """Create particles when collected."""
        import random
        for _ in range(GameConstants.POWERUP_PARTICLE_COUNT):
            particle = {
                'x': float(self.rect.centerx + random.randint(-10, 10)),
                'y': float(self.rect.centery + random.randint(-10, 10)),
                'dx': random.uniform(-3, 3),
                'dy': random.uniform(-4, 1),
                'life': float(GameConstants.POWERUP_PARTICLE_LIFETIME),
                'max_life': float(GameConstants.POWERUP_PARTICLE_LIFETIME),
                'color': self.color_set["bright"]
            }
            self.collection_particles.append(particle)
    
    def update_collection_particles(self, dt: float):
        """Update collection particles."""
        for particle in self.collection_particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['dy'] += 0.2 * dt
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.collection_particles.remove(particle)
    
    def draw_icon(self, surface: pygame.Surface, center_x: int, center_y: int, size: int):
        """
        Draw powerup-specific icon.
        
        Args:
            surface: Surface to draw on
            center_x: Center x position
            center_y: Center y position
            size: Icon size
        """
        main_color = self.color_set["main"]
        glow_color = self.color_set["glow"]
        
        if self.powerup_type == "health":
            # Health cross
            cross_size = size // 3
            pygame.draw.rect(surface, main_color, 
                           (center_x - cross_size//2, center_y - cross_size, cross_size, cross_size*2))
            pygame.draw.rect(surface, main_color, 
                           (center_x - cross_size, center_y - cross_size//2, cross_size*2, cross_size))
        
        elif self.powerup_type == "speed":
            # Lightning bolt
            points = [
                (center_x - size//3, center_y - size//2),
                (center_x + size//6, center_y - size//6),
                (center_x - size//6, center_y),
                (center_x + size//3, center_y + size//2),
                (center_x - size//6, center_y + size//6),
                (center_x + size//6, center_y)
            ]
            pygame.draw.polygon(surface, main_color, points)
        
        elif self.powerup_type == "damage":
            # Star burst
            for i in range(8):
                angle = i * 45
                x1 = center_x + int((size//4) * math.cos(math.radians(angle)))
                y1 = center_y + int((size//4) * math.sin(math.radians(angle)))
                x2 = center_x + int((size//2) * math.cos(math.radians(angle)))
                y2 = center_y + int((size//2) * math.sin(math.radians(angle)))
                pygame.draw.line(surface, main_color, (x1, y1), (x2, y2), 2)
        
        elif self.powerup_type == "shield":
            # Shield circle
            pygame.draw.circle(surface, main_color, (center_x, center_y), size//2, 3)
            pygame.draw.circle(surface, glow_color, (center_x, center_y), size//3)
        
        elif self.powerup_type == "ammo":
            # Bullet/arrow
            pygame.draw.circle(surface, main_color, (center_x - size//3, center_y), size//4)
            pygame.draw.polygon(surface, main_color, [
                (center_x - size//3, center_y - size//6),
                (center_x + size//3, center_y),
                (center_x - size//3, center_y + size//6)
            ])
    
    def draw(self, surface: pygame.Surface):
        """
        Draw powerup with visual effects.
        
        Args:
            surface: Surface to draw on
        """
        if self.collected:
            # Draw collection particles
            for particle in self.collection_particles:
                alpha = int(255 * (particle['life'] / particle['max_life']))
                if alpha > 0:
                    pygame.draw.circle(surface, particle['color'], 
                                     (int(particle['x']), int(particle['y'])), 2)
            return
        
        center_x = self.rect.centerx
        center_y = self.rect.centery
        
        # Pulsing effect
        pulse_scale = 1.0 + math.sin(self.pulse_timer) * GameConstants.POWERUP_PULSE_SCALE
        glow_radius = int(25 * pulse_scale)
        
        # Outer glow
        for i in range(3):
            radius = glow_radius - i * 3
            if radius > 0:
                pygame.draw.circle(surface, self.color_set["glow"], (center_x, center_y), radius)
        
        # Main circle
        main_radius = int(18 * pulse_scale)
        pygame.draw.circle(surface, self.color_set["main"], (center_x, center_y), main_radius)
        
        # Inner bright circle
        inner_radius = int(12 * pulse_scale)
        pygame.draw.circle(surface, self.color_set["bright"], (center_x, center_y), inner_radius)
        
        # Icon
        icon_size = int(20 * pulse_scale)
        self.draw_icon(surface, center_x, center_y, icon_size)
        
        # Sparkle effects
        for i in range(4):
            angle = (self.rotation + i * 90) % 360
            sparkle_distance = 30 + math.sin(self.pulse_timer + i) * 5
            sparkle_x = center_x + int(sparkle_distance * math.cos(math.radians(angle)))
            sparkle_y = center_y + int(sparkle_distance * math.sin(math.radians(angle)))
            
            sparkle_size = 2 + int(math.sin(self.pulse_timer * 3 + i))
            pygame.draw.circle(surface, self.color_set["bright"], (sparkle_x, sparkle_y), sparkle_size)
