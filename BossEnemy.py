"""
Level 2 Boss - Final Dungeon Boss with Easy and Hard modes
Two-phase boss fight with unique attack patterns
"""

import pygame
import math
import random
import os
from Level2Enemies import Level2Enemy, BoneParticle, build_state_animations_from_manifest


def build_boss_animations_from_individual_files(base_path: str, scale_to: tuple = (128, 128)) -> dict[str, list[pygame.Surface]]:
    """Load boss animations from individual PNG files instead of sprite sheets"""
    anims = {}
    
    # Animation folders and their expected naming patterns
    # Map folder names to game states and file prefixes
    animation_folders = {
        "idle": ("Idle", "Bringer-of-Death_Idle_"),
        "run": ("Walk", "Bringer-of-Death_Walk_"),  
        "attack": ("Attack", "Bringer-of-Death_Attack_"),
        "cast": ("Cast", "Bringer-of-Death_Cast_"),
        "spell": ("Spell", "Bringer-of-Death_Spell_"),
        "hurt": ("Hurt", "Bringer-of-Death_Hurt_"),
        "death": ("Death", "Bringer-of-Death_Death_")
    }
    
    for anim_state, (folder_name, file_prefix) in animation_folders.items():
        folder_path = os.path.join(base_path, folder_name)
        if not os.path.exists(folder_path):
            anims[anim_state] = []
            continue
            
        frames = []
        frame_num = 1
        
        # Load frames until we can't find any more
        while True:
            file_path = os.path.join(folder_path, f"{file_prefix}{frame_num}.png")
            if not os.path.exists(file_path):
                break
                
            try:
                frame = pygame.image.load(file_path).convert_alpha()
                # Scale the frame if needed
                if scale_to:
                    frame = pygame.transform.scale(frame, scale_to)
                frames.append(frame)
                frame_num += 1
            except pygame.error as e:
                print(f"Error loading {file_path}: {e}")
                break
        
        anims[anim_state] = frames
        if frames:
            print(f"Loaded {len(frames)} frames for {anim_state}")
    
    return anims


class BossProjectile:
    """Boss projectile for ranged attacks"""
    
    def __init__(self, x, y, target_x, target_y, speed=4, damage=1, projectile_type="shadow_bolt", can_split=False, parent_projectiles_list=None):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.speed = speed
        self.damage = damage
        self.projectile_type = projectile_type
        self.alive = True
        self.max_range = 800
        self.can_split = can_split
        self.has_split = False
        self.parent_projectiles_list = parent_projectiles_list  # Reference to boss's projectile list
        
        # Calculate direction to target
        dx = target_x - x
        dy = target_y - y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > 0:
            self.vel_x = (dx / distance) * speed
            self.vel_y = (dy / distance) * speed
        else:
            self.vel_x = speed
            self.vel_y = 0
        
        # Create collision rect
        self.rect = pygame.Rect(x - 8, y - 8, 16, 16)
        
        # Visual effects
        self.trail_particles = []
        self.life_timer = 0
        
        # Projectile appearance based on type
        if projectile_type == "shadow_bolt":
            self.color = (120, 50, 150)
            self.size = 8
        elif projectile_type == "bone_shard":
            self.color = (200, 200, 180)
            self.size = 6
        elif projectile_type == "energy_blast":
            self.color = (255, 100, 100)
            self.size = 10
        elif projectile_type == "split_bolt":
            self.color = (100, 255, 200)  # Cyan for split projectiles
            self.size = 9
    
    def update(self, dt, obstacles=None):
        """Update projectile movement and effects"""
        if not self.alive:
            return
        
        self.life_timer += dt
        
        # Split projectile at midpoint if it can split
        distance_traveled = math.sqrt((self.x - self.start_x)**2 + (self.y - self.start_y)**2)
        if self.can_split and not self.has_split and distance_traveled > self.max_range * 0.5:
            self.split_projectile()
            self.has_split = True
        
        # Move projectile
        self.x += self.vel_x * dt
        self.y += self.vel_y * dt
        self.rect.centerx = int(self.x)
        self.rect.centery = int(self.y)
        
        # Check max range
        distance_traveled = math.sqrt((self.x - self.start_x)**2 + (self.y - self.start_y)**2)
        if distance_traveled > self.max_range:
            self.alive = False
            return
        
        # Check collision with obstacles
        if obstacles:
            for obstacle in obstacles:
                if self.rect.colliderect(obstacle.rect):
                    self.alive = False
                    self.create_impact_particles()
                    return
        
        # Create trail particles
        if random.random() < 0.6:
            self.trail_particles.append({
                'x': self.x + random.uniform(-3, 3),
                'y': self.y + random.uniform(-3, 3),
                'life': 15,
                'max_life': 15,
                'color': self.color
            })
        
        # Update trail particles
        for particle in self.trail_particles[:]:
            particle['life'] -= dt
            if particle['life'] <= 0:
                self.trail_particles.remove(particle)
    
    def create_impact_particles(self):
        """Create particles when projectile hits something"""
        for i in range(8):
            angle = random.uniform(0, 360)
            speed = random.uniform(1, 3)
            self.trail_particles.append({
                'x': self.x + math.cos(math.radians(angle)) * 5,
                'y': self.y + math.sin(math.radians(angle)) * 5,
                'vel_x': math.cos(math.radians(angle)) * speed,
                'vel_y': math.sin(math.radians(angle)) * speed,
                'life': 20,
                'max_life': 20,
                'color': self.color
            })
    
    def split_projectile(self):
        """Split this projectile into 3 smaller projectiles"""
        if not self.parent_projectiles_list:
            return
        
        # Calculate perpendicular directions for split
        base_angle = math.degrees(math.atan2(self.vel_y, self.vel_x))
        
        # Create 3 projectiles: straight, +30 degrees, -30 degrees
        for angle_offset in [0, 30, -30]:
            final_angle = base_angle + angle_offset
            final_rad = math.radians(final_angle)
            
            # Calculate target position based on angle
            distance = 300
            target_x = self.x + math.cos(final_rad) * distance
            target_y = self.y + math.sin(final_rad) * distance
            
            # Create child projectile (cannot split again)
            child = BossProjectile(
                self.x, self.y,
                target_x, target_y,
                speed=self.speed * 0.8,  # Slightly slower
                damage=max(1, self.damage // 2),  # Half damage
                projectile_type="split_bolt",
                can_split=False,
                parent_projectiles_list=None
            )
            self.parent_projectiles_list.append(child)
        
        print(f"Projectile split into 3 at ({self.x:.0f}, {self.y:.0f})")
    
    def check_player_collision(self, player):
        """Check if projectile hits player"""
        if not self.alive or not player:
            return False
        
        if self.rect.colliderect(player.rect):
            player.take_damage(self.damage)
            self.alive = False
            self.create_impact_particles()
            return True
        return False
    
    def draw(self, surface, scroll_offset=0):
        """Draw projectile and trail effects"""
        if not self.alive:
            # Still draw trail particles for a bit after death
            for particle in self.trail_particles:
                alpha = int(255 * (particle['life'] / particle['max_life']))
                size = max(1, int(3 * (particle['life'] / particle['max_life'])))
                screen_x = int(particle['x'] - scroll_offset)
                screen_y = int(particle['y'])
                if 0 <= screen_x <= surface.get_width():
                    pygame.draw.circle(surface, particle['color'], (screen_x, screen_y), size)
            return
        
        screen_x = int(self.x - scroll_offset)
        screen_y = int(self.y)
        
        # Draw trail particles
        for particle in self.trail_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            size = max(1, int(2 * (particle['life'] / particle['max_life'])))
            trail_x = int(particle['x'] - scroll_offset)
            trail_y = int(particle['y'])
            if 0 <= trail_x <= surface.get_width():
                pygame.draw.circle(surface, particle['color'], (trail_x, trail_y), size)
        
        # Draw main projectile
        if 0 <= screen_x <= surface.get_width():
            # Outer glow
            for i in range(3):
                glow_size = self.size + i * 2
                alpha = max(0, 100 - i * 30)
                glow_color = (*self.color, alpha)
                glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, self.color, (glow_size, glow_size), glow_size)
                surface.blit(glow_surf, (screen_x - glow_size, screen_y - glow_size))
            
            # Core projectile
            pygame.draw.circle(surface, (255, 255, 255), (screen_x, screen_y), self.size)
            pygame.draw.circle(surface, self.color, (screen_x, screen_y), self.size - 2)

# Boss animation manifest - now uses individual files from assets/BossLevel/
BOSS_ASSETS_PATH = "assets/BossLevel"


class DungeonBoss(Level2Enemy):
    """Base boss class with common functionality"""
    
    def __init__(self, x, y, difficulty="easy", width=128, height=128):
        # Load boss animations from individual files - scale to 128x128 (good balance)
        boss_anims = build_boss_animations_from_individual_files(BOSS_ASSETS_PATH, scale_to=(128, 128))
        super().__init__(x, y, width, height, anim_manifest={})
        
        # Create a separate smaller hitbox for collision to prevent player getting stuck
        # Boss visual sprite: 128x128, hitbox: 50x70 (narrower and shorter)
        hitbox_width = 50
        hitbox_height = 70
        
        # Store display rect (for drawing sprite)
        self.display_rect = pygame.Rect(x, y, width, height)
        
        # Create smaller collision hitbox at bottom center of sprite
        hitbox_x = self.display_rect.centerx - hitbox_width // 2
        hitbox_y = self.display_rect.bottom - hitbox_height
        
        # Use hitbox as main rect for collision detection
        self.rect = pygame.Rect(hitbox_x, hitbox_y, hitbox_width, hitbox_height)
        self.hitbox = self.rect  # Reference for compatibility
        
        # Override the animations with our custom loaded ones
        self.anims = boss_anims
        
        # Set initial image from loaded animations (replace brown default)
        if "idle" in self.anims and self.anims["idle"]:
            self.image = self.anims["idle"][0]
            self.current_state = "idle"
        
        # Animation control variables
        self.anim_tick = 0
        self.anim_speed = 6  # Frames between animation updates (lower = faster)
        self._last_x = self.rect.x  # Track position changes for movement detection
        
        # Ensure physics variables are set (inherited from parent but make sure)
        if not hasattr(self, 'y_velocity'):
            self.y_velocity = 0
        if not hasattr(self, 'gravity'):
            self.gravity = 0.8  # Boss gravity
        if not hasattr(self, 'on_ground'):
            self.on_ground = False
        
        self.difficulty = difficulty
        self.name = f"Dungeon Boss ({difficulty.upper()})"
        
        # Boss stats based on difficulty
        if difficulty == "easy":
            self.max_hp = 500
            self.speed = 1.5
            self.attack_damage = 1
            self.attack_cooldown = 2000  # 2 seconds
        else:  # hard
            self.max_hp = 800
            self.speed = 2.5
            self.attack_damage = 2
            self.attack_cooldown = 1200  # 1.2 seconds
        
        self.current_hp = self.max_hp
        self.sight_range = 500  # Boss can see far
        
        # Boss melee attack range - shorter for more fair combat
        self.attack_range = pygame.Vector2(80, 80)  # Reasonable melee range for boss size
        
        # Boss phases
        self.phase = 1
        self.phase_2_threshold = self.max_hp * 0.5  # Phase 2 at 50% HP
        self.phase_2_triggered = False
        
        # Enhanced visuals
        self.boss_glow_timer = 0
        self.is_enraged = False
        self.shield_active = False
        self.shield_cooldown = 0
        self.shield_duration = 0
        
        # Attack patterns
        self.attack_pattern = "melee"  # melee, dash, summon, shield
        self.pattern_timer = 180  # Start at max to trigger immediate pattern selection
        self.pattern_duration = 180  # 3 seconds per pattern
        
        # Dash attack
        self.is_dashing = False
        self.dash_speed = 8
        self.dash_duration = 0
        self.dash_max_duration = 30  # For tracking dash progress
        self.dash_cooldown = 0
        
        # Melee attack timing
        self.last_attack_time = 0
        
        # Summon minions
        self.summon_cooldown = 0
        self.minions_summoned = []
        
        # Ground slam attack
        self.slam_particles = []
        self.is_slamming = False
        self.slam_timer = 0
        
        # Projectile attacks
        self.projectiles = []
        self.projectile_cooldown = 0
        self.burst_fire_count = 0
        self.burst_fire_timer = 0
        self.is_burst_firing = False
        self.is_casting_single = False  # For single projectile (Cast animation)
        self.cast_timer = 0  # Timer for casting animation
        
        # Visual effects
        self.aura_particles = []
        self.phase_transition_particles = []
        
        # Anti-stuck tracking
        self._stuck_counter = 0
        
        print(f"Boss spawned: {self.name} with {self.max_hp} HP")
    
    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        """Update boss AI with complex patterns"""
        if not self.alive:
            self.update_death_animation(dt)
            return
        
        self.scroll_offset = scroll_offset
        self.boss_glow_timer += dt * 0.05
        
        # Check for phase 2 transition
        if not self.phase_2_triggered and self.current_hp <= self.phase_2_threshold:
            self.trigger_phase_2()
        
        # Update cooldowns
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt * 16.67  # Convert to ms
        if self.shield_cooldown > 0:
            self.shield_cooldown -= dt * 16.67
        if self.summon_cooldown > 0:
            self.summon_cooldown -= dt * 16.67
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= dt * 16.67
        if self.shield_duration > 0:
            self.shield_duration -= dt * 16.67
        if self.last_attack_time > 0:
            self.last_attack_time -= dt * 16.67
            if self.shield_duration <= 0:
                self.shield_active = False
        
        # Update burst fire
        if self.is_burst_firing:
            self.burst_fire_timer -= dt * 16.67
            if self.burst_fire_timer <= 0:
                self.fire_projectile_at_player(player)
                self.burst_fire_count -= 1
                if self.burst_fire_count <= 0:
                    self.is_burst_firing = False
                    self.projectile_cooldown = 2000 if self.difficulty == "easy" else 1500
                else:
                    self.burst_fire_timer = 200  # 200ms between burst shots
        
        # Update projectiles
        for projectile in self.projectiles[:]:
            projectile.update(dt, obstacles)
            if projectile.check_player_collision(player):
                print(f"Boss projectile hit player!")
            if not projectile.alive:
                self.projectiles.remove(projectile)
        
        # Update pattern timer
        self.pattern_timer += dt
        if self.pattern_timer >= self.pattern_duration:
            self.choose_next_pattern(player)
            self.pattern_timer = 0
        
        # Execute current pattern
        if self.is_dashing:
            self.execute_dash(player, obstacles, dt)
        elif self.is_slamming:
            self.execute_ground_slam(player, dt)
        elif self.shield_active:
            self.execute_shield_mode(player, obstacles, dt)
            # Make sure shield doesn't last forever
            if self.shield_duration <= 0:
                self.shield_active = False
                print("Shield expired!")
        else:
            self.execute_current_pattern(player, obstacles, dt)
        
        # Safety check: if boss is in a special state for too long, force it out
        if hasattr(self, '_state_timer'):
            self._state_timer += dt
            # If in a special state for more than 5 seconds, force back to normal
            if self._state_timer > 300:  # 5 seconds at 60fps
                if self.is_dashing:
                    print("Forcing dash to end (timeout)")
                    self.is_dashing = False
                    self.dash_duration = 0
                    self.dash_cooldown = 3000
                if self.is_slamming:
                    print("Forcing slam to end (timeout)")
                    self.is_slamming = False
                    self.slam_timer = 0
                if self.shield_active:
                    print("Forcing shield to end (timeout)")
                    self.shield_active = False
                    self.shield_duration = 0
                self._state_timer = 0
        else:
            self._state_timer = 0
        
        # Reset state timer when not in special states
        if not self.is_dashing and not self.is_slamming and not self.shield_active:
            self._state_timer = 0
        
        # Prevent player from getting stuck inside boss - push player away
        if player and self.rect.colliderect(player.rect):
            # Calculate push direction based on relative positions
            if player.rect.centerx < self.rect.centerx:
                # Player on left, push left
                push_force = -5
            else:
                # Player on right, push right
                push_force = 5
            
            # Push player horizontally
            player.rect.x += push_force
            
            # Also push vertically if player is being squished
            if player.rect.centery < self.rect.centery:
                player.rect.y -= 3
        
        # Track movement for anti-stuck detection
        movement = abs(self.rect.x - self._last_x)
        
        # Improved anti-stuck failsafe
        if not self.is_dashing and not self.is_slamming and not self.shield_active and not self.is_burst_firing:
            # If boss hasn't moved much
            if movement < 0.5:
                # Check if we're in a projectile pattern (those don't require movement)
                if self.attack_pattern not in ["projectile_single", "projectile_burst", "projectile_tracking", "projectile_split"]:
                    # Boss is stuck, force a new pattern sooner
                    if self.pattern_timer > 20:  # If stuck for more than 0.33 seconds
                        print(f"Boss stuck (moved {movement:.2f}px), forcing new pattern from {self.attack_pattern}...")
                        # Force projectile pattern when stuck (safest option)
                        self.attack_pattern = "projectile_burst" if self.phase == 2 else "projectile_single"
                        self.pattern_timer = 0
                        # Reset projectile cooldown to allow immediate firing
                        self.projectile_cooldown = 0
                    
                    # Increment stuck counter only if in movement-based patterns
                    if hasattr(self, '_stuck_counter'):
                        self._stuck_counter += 1
                else:
                    # Reset stuck counter during projectile patterns (they don't need movement)
                    if hasattr(self, '_stuck_counter'):
                        self._stuck_counter = 0
            else:
                # Boss is moving, reset counter
                if hasattr(self, '_stuck_counter'):
                    self._stuck_counter = 0
        else:
            # Reset during special states
            if hasattr(self, '_stuck_counter'):
                self._stuck_counter = 0
        
        # Additional stuck check: if boss is severely stuck in movement patterns
        if hasattr(self, '_stuck_counter') and self._stuck_counter > 90:  # 1.5 seconds stuck
            # Only apply severe stuck fix for non-projectile patterns
            if self.attack_pattern not in ["projectile_single", "projectile_burst", "projectile_tracking", "projectile_split"]:
                print("Boss severely stuck! Switching to projectile spam mode...")
                self.attack_pattern = "projectile_burst"
                self.projectile_cooldown = 0
                self.pattern_timer = 0
                self._stuck_counter = 0
                # Small position nudge to unstick
                if player:
                    # Move slightly away from player
                    if self.rect.centerx > player.rect.centerx:
                        self.rect.x += 10
                    else:
                        self.rect.x -= 10
        
        # Update visual effects
        self.update_aura_particles(dt)
        self.update_slam_particles(dt)
        
        # Update animations
        self.update_boss_animation()
        
        # Apply physics (gravity and ground collision)
        if not self.is_dashing:
            self.apply_physics(obstacles)
        
        # Safety: Keep boss within bounds (prevent falling off map)
        if self.rect.y > 600:  # If boss falls too far
            print(f"Boss fell off map! Resetting position...")
            self.rect.y = 300  # Reset to a safe Y position
            self.y_velocity = 0
            self.on_ground = False
        
        # Keep boss within horizontal bounds
        if self.rect.x < 50:
            self.rect.x = 50
        elif self.rect.x > 1100:
            self.rect.x = 1100
    
    def update_boss_animation(self):
        """Custom animation update for boss with multiple states - prevents freezing"""
        self.anim_tick = (self.anim_tick + 1) % 10000000
        
        # Update casting timer
        if self.cast_timer > 0:
            self.cast_timer -= 1
            # When cast timer ends, clear the casting flag
            if self.cast_timer == 0:
                self.is_casting_single = False
        
        # Update attack animation timer (CRITICAL: Proper timer management)
        if hasattr(self, 'attack_anim_timer') and self.attack_anim_timer > 0:
            # Decrement the timer
            self.attack_anim_timer -= 1
            # Increment elapsed for progress calculation
            if not hasattr(self, 'attack_anim_elapsed'):
                self.attack_anim_elapsed = 0
            self.attack_anim_elapsed += 1
            
            # Clear when timer reaches zero
            if self.attack_anim_timer <= 0:
                self.attack_anim_elapsed = 0
                print("Attack animation completed!")
        
        # Track velocity/movement intent for better animation detection
        has_velocity = hasattr(self, 'velocity_x') and abs(getattr(self, 'velocity_x', 0)) > 0.1
        position_changed = abs(self.rect.x - self._last_x) > 0.1
        
        # Determine current animation state (priority order)
        if hasattr(self, 'attack_anim_timer') and self.attack_anim_timer > 0 and "attack" in self.anims and self.anims["attack"]:
            # Melee attack animation
            state = "attack"
            frames = self.anims["attack"]
            if frames and hasattr(self, 'attack_anim_duration') and self.attack_anim_duration > 0:
                progress = min(1.0, self.attack_anim_elapsed / self.attack_anim_duration)
                idx = min(int(progress * len(frames)), len(frames) - 1)
            else:
                idx = 0
        elif self.is_burst_firing and "spell" in self.anims and self.anims["spell"]:
            # Spell animation for burst/multi-projectile attacks (16 frames)
            state = "spell"
            frames = self.anims["spell"]
            idx = (self.anim_tick // 8) % len(frames) if frames else 0  # Slower for epic spell
        elif self.cast_timer > 0 and "cast" in self.anims and self.anims["cast"]:
            # Cast animation for single projectiles (9 frames)
            state = "cast"
            frames = self.anims["cast"]
            idx = (self.anim_tick // self.anim_speed) % len(frames) if frames else 0
        elif self.is_dashing or position_changed or has_velocity:
            # Moving - use run/walk animation (including when dashing or trying to move)
            state = "run"
            frames = self.anims.get("run", [])
            idx = (self.anim_tick // self.anim_speed) % len(frames) if frames else 0
        else:
            # Idle animation - always animate even when standing still
            state = "idle"
            frames = self.anims.get("idle", [])
            idx = (self.anim_tick // self.anim_speed) % len(frames) if frames else 0
        
        # Always ensure we have valid frames and index
        if state and frames and len(frames) > 0:
            idx = max(0, min(idx, len(frames) - 1))  # Clamp index to valid range
            img = frames[idx]
            self.image = img if self.facing_right else pygame.transform.flip(img, True, False)
            self.current_state = state
        
        # Update position tracking
        self._last_x = self.rect.x
    
    def choose_next_pattern(self, player):
        """Choose next attack pattern based on phase, difficulty, and player distance"""
        if not player:
            return
        
        distance_to_player = abs(self.rect.centerx - player.rect.centerx)
        height_difference = abs(self.rect.centery - player.rect.centery)
        player_on_platform = height_difference > 100  # Player is significantly higher/lower
        
        if self.phase == 1:
            # Phase 1: Aggressive melee-focused patterns
            if distance_to_player < 150 and not player_on_platform:
                self.attack_pattern = "melee"
                self.pattern_duration = 180
            elif distance_to_player < 300 and self.dash_cooldown <= 0 and not player_on_platform:
                self.attack_pattern = "dash"
                self.pattern_duration = 60
            elif distance_to_player > 200 or player_on_platform:
                # Always prefer projectiles when far away
                self.attack_pattern = "projectile_single"
                self.pattern_duration = 60  # Give more time for cooldown to reset
            else:
                self.attack_pattern = "melee"
                self.pattern_duration = 180
        else:
            # Phase 2: DEFENSIVE ranged strategy - maintain distance, use projectiles and shield
            available_patterns = []
            
            # PHASE 2 STRATEGY: Avoid close combat, use projectiles and defensive abilities
            if distance_to_player < 200:
                # Player too close - retreat with dash or use shield
                if self.dash_cooldown <= 0:
                    available_patterns.extend(["dash", "dash", "dash"])  # Heavily favor dash to create distance
                if self.shield_cooldown <= 0:
                    available_patterns.append("shield")
                # Add projectiles even when close (shoot while backing away)
                available_patterns.extend(["projectile_single", "projectile_burst"])
                # Only melee as absolute last resort when cornered
                if distance_to_player < 80 and not player_on_platform:
                    available_patterns.append("melee")
            else:
                # Good distance - focus on projectile attacks
                if self.difficulty == "hard":
                    available_patterns.extend([
                        "projectile_burst", "projectile_burst", "projectile_burst",  # Heavily favor burst fire
                        "projectile_tracking", "projectile_tracking",
                        "projectile_split", "projectile_split"
                    ])
                else:
                    available_patterns.extend([
                        "projectile_single", "projectile_single",
                        "projectile_burst",
                        "projectile_split"
                    ])
                
                # Shield for defense while attacking
                if self.shield_cooldown <= 0:
                    available_patterns.append("shield")
            
            # Hard mode exclusive summons
            if self.summon_cooldown <= 0 and self.difficulty == "hard" and distance_to_player > 250:
                available_patterns.append("summon")
            
            # Always ensure projectiles are an option
            if not available_patterns:
                available_patterns.extend(["projectile_single", "projectile_burst"])
            
            self.attack_pattern = random.choice(available_patterns)
            
            # Set pattern duration
            if "projectile" in self.attack_pattern:
                self.pattern_duration = 60  # Longer to allow cooldowns to reset
            elif self.attack_pattern == "dash":
                self.pattern_duration = 60
            elif self.attack_pattern == "ground_slam":
                self.pattern_duration = 90
            elif self.attack_pattern == "shield":
                self.pattern_duration = 150  # Longer shield duration in phase 2
            else:
                self.pattern_duration = 120  # Shorter melee duration in phase 2
        
        # Reset pattern timer when switching patterns
        self.pattern_timer = self.pattern_duration
        
        print(f"Boss switches to: {self.attack_pattern} (Phase {self.phase}, distance: {distance_to_player:.0f})")
    
    def execute_current_pattern(self, player, obstacles, dt):
        """Execute the current attack pattern"""
        if self.attack_pattern == "melee":
            self.execute_melee_pattern(player, obstacles, dt)
        elif self.attack_pattern == "dash":
            # Dash is started once, then execute_dash handles it until complete
            if not self.is_dashing:
                self.start_dash_attack(player)
        elif self.attack_pattern == "ground_slam":
            if not self.is_slamming:
                self.start_ground_slam(player)
        elif self.attack_pattern == "shield":
            if not self.shield_active:
                self.activate_shield()
        elif self.attack_pattern == "summon":
            self.summon_minions()
        elif self.attack_pattern == "projectile_single":
            # Keep trying to fire if on cooldown
            if self.projectile_cooldown <= 0:
                self.start_single_projectile(player)
        elif self.attack_pattern == "projectile_burst":
            # Start burst if not already firing
            if not self.is_burst_firing and self.projectile_cooldown <= 0:
                self.start_burst_fire(player)
        elif self.attack_pattern == "projectile_tracking":
            if self.projectile_cooldown <= 0:
                self.start_tracking_projectiles(player)
        elif self.attack_pattern == "projectile_split":
            if self.projectile_cooldown <= 0:
                self.start_split_projectiles(player)
    
    def execute_melee_pattern(self, player, obstacles, dt):
        """Standard melee chase and attack with improved movement"""
        if not player:
            return
        
        distance_x = abs(self.rect.centerx - player.rect.centerx)
        distance_y = abs(self.rect.centery - player.rect.centery)
        
        # Calculate distance for attack range check
        distance = math.sqrt(distance_x**2 + distance_y**2)
        
        # More aggressive movement - smaller dead zone
        if self.rect.centerx < player.rect.centerx - 30:
            self.direction = 1
            self.facing_right = True
            # Move faster if far away
            speed_multiplier = 1.5 if distance_x > 200 else 1.0
            self.move_horizontal(self.speed * speed_multiplier, obstacles)
        elif self.rect.centerx > player.rect.centerx + 30:
            self.direction = -1
            self.facing_right = False
            # Move faster if far away
            speed_multiplier = 1.5 if distance_x > 200 else 1.0
            self.move_horizontal(-self.speed * speed_multiplier, obstacles)
        
        # Attack if in range - use the attack_range we set (80x80)
        attack_rect = self.get_attack_rect()
        if attack_rect.colliderect(player.rect) and self.can_attack():
            self.on_attack(player)
    
    def can_attack(self):
        """Check if boss can perform a melee attack based on cooldown"""
        return self.last_attack_time <= 0
    
    def on_attack(self, player):
        """Boss-specific attack with cooldown management"""
        super().on_attack(player)  # Call parent attack method
        self.last_attack_time = self.attack_cooldown  # Reset cooldown timer
        
        # Boss deals more damage based on difficulty
        if player and hasattr(player, 'take_damage'):
            additional_damage = self.attack_damage - 1  # Parent already does 1 damage
            if additional_damage > 0:
                player.take_damage(additional_damage)
    
    def start_dash_attack(self, player):
        """Start a dash attack - aggressive in Phase 1, retreat in Phase 2"""
        if not player or self.is_dashing or self.dash_cooldown > 0:
            return
        
        self.is_dashing = True
        self.dash_max_duration = 40 if self.phase == 2 else 30  # Longer dash in phase 2
        self.dash_duration = self.dash_max_duration
        self.dash_speed = 12 if self.phase == 2 else 8  # Faster in phase 2
        
        # PHASE 2: Dash AWAY from player to create distance
        # PHASE 1: Dash TOWARD player for aggressive attack
        if self.phase == 2:
            # Retreat dash - go opposite direction of player
            if player.rect.centerx > self.rect.centerx:
                self.facing_right = False  # Dash left (away from player on right)
            else:
                self.facing_right = True   # Dash right (away from player on left)
            print(f"Boss retreats with dash! (Phase 2)")
        else:
            # Aggressive dash - go toward player
            if player.rect.centerx > self.rect.centerx:
                self.facing_right = True
            else:
                self.facing_right = False
            print(f"Boss dash attack toward player! (Phase 1)")
    
    def execute_dash(self, player, obstacles, dt):
        """Execute dash attack with improved collision and animation"""
        if self.dash_duration > 0:
            self.dash_duration -= dt
            
            # Determine dash direction (toward player or current facing)
            if player:
                # Face toward player if not already dashing in a direction
                if self.dash_duration == self.dash_max_duration:  # Just started
                    self.facing_right = player.rect.centerx > self.rect.centerx
            
            # Move fast in dash direction
            dash_dx = self.dash_speed if self.facing_right else -self.dash_speed
            
            # Store old position for collision resolution
            old_x = self.rect.x
            old_y = self.rect.y
            
            # Move boss
            self.rect.x += dash_dx
            
            # Check obstacle collision
            if obstacles:
                for obstacle in obstacles:
                    if self.rect.colliderect(obstacle):
                        # Stop dash on collision
                        self.rect.x = old_x
                        self.is_dashing = False
                        self.dash_duration = 0
                        break
            
            # Check collision with player
            if player and self.rect.colliderect(player.rect):
                player.take_damage(self.attack_damage)
                # Add knockback to player
                knockback_force = 15 if self.facing_right else -15
                if hasattr(player, 'velocity_x'):
                    player.velocity_x = knockback_force
                if hasattr(player, 'velocity_y'):
                    player.velocity_y = -5  # Slight upward knockback
                self.is_dashing = False
                self.dash_duration = 0
                print(f"Boss dash hit player for {self.attack_damage} damage!")
            
            # Create dash trail particles
            if random.random() < 0.3:
                self.aura_particles.append({
                    'x': self.rect.centerx,
                    'y': self.rect.centery + random.randint(-20, 20),
                    'life': 20,
                    'max_life': 20,
                    'color': (180, 100, 255) if self.phase == 2 else (150, 150, 200)
                })
        else:
            self.is_dashing = False
            self.dash_cooldown = 3000 if self.difficulty == "easy" else 2000
    
    def start_ground_slam(self, player):
        """Start ground slam attack"""
        if self.is_slamming:
            return
        
        self.is_slamming = True
        self.slam_timer = 30  # Wind-up time
        self.change_state("Attack")
        print("Boss preparing ground slam!")
    
    def execute_ground_slam(self, player, dt):
        """Execute ground slam attack"""
        # Wind-up phase
        if self.slam_timer > 0:
            self.slam_timer -= dt
            if self.slam_timer <= 0:
                # Timer just reached 0, execute the slam NOW
                # Create shockwave
                radius = 150 if self.difficulty == "easy" else 200
                
                if player:
                    distance = math.sqrt((self.rect.centerx - player.rect.centerx)**2 + 
                                    (self.rect.centery - player.rect.centery)**2)
                    if distance < radius:
                        player.take_damage(self.attack_damage)
                        print("Ground slam hit player!")
                
                # Create visual particles
                for i in range(20):
                    angle = random.uniform(0, 360)
                    speed = random.uniform(2, 5)
                    self.slam_particles.append({
                        'x': self.rect.centerx,
                        'y': self.rect.bottom,
                        'dx': math.cos(math.radians(angle)) * speed,
                        'dy': math.sin(math.radians(angle)) * speed - 2,
                        'life': 30,
                        'max_life': 30,
                        'color': (200, 150, 100)
                    })
                
                # End the slam
                self.is_slamming = False
                print("Ground slam completed!")
    
    def activate_shield(self):
        """Activate defensive shield"""
        if self.shield_active:
            return
        
        self.shield_active = True
        self.shield_duration = 3000 if self.difficulty == "easy" else 5000
        self.shield_cooldown = 10000 if self.difficulty == "easy" else 7000
        self.change_state("Shield")
        print("Boss activates shield!")
    
    def execute_shield_mode(self, player, obstacles, dt):
        """Boss backs away while shield is active"""
        if not player:
            return
        
        # Back away from player slowly
        if self.rect.centerx < player.rect.centerx:
            self.direction = -1
            self.facing_right = False
            self.move_horizontal(-self.speed * 0.5, obstacles)
        else:
            self.direction = 1
            self.facing_right = True
            self.move_horizontal(self.speed * 0.5, obstacles)
    
    def summon_minions(self):
        """Hard mode only - summon skeleton minions"""
        if self.difficulty != "hard" or self.summon_cooldown > 0:
            return
        
        self.summon_cooldown = 15000  # 15 seconds
        
        # Signal to spawn minions (handled by game.py)
        self.summon_event = {
            'count': 2,
            'positions': [
                (self.rect.x - 100, self.rect.y),
                (self.rect.x + 100, self.rect.y)
            ]
        }
        print("Boss summoning minions!")
    
    def start_single_projectile(self, player):
        """Fire a single projectile at player"""
        if not player or self.projectile_cooldown > 0:
            return
        
        self.fire_projectile_at_player(player, "shadow_bolt")
        self.projectile_cooldown = 1500 if self.difficulty == "easy" else 1000
        print("Boss fires single projectile!")
    
    def start_burst_fire(self, player):
        """Start burst fire sequence (3-5 rapid shots)"""
        if not player or self.projectile_cooldown > 0 or self.is_burst_firing:
            return
        
        self.is_burst_firing = True
        self.burst_fire_count = 5 if self.difficulty == "hard" else 3
        self.burst_fire_timer = 100  # Start immediately
        print(f"Boss starts burst fire! ({self.burst_fire_count} shots)")
    
    def start_tracking_projectiles(self, player):
        """Fire multiple projectiles that track player position (hard mode)"""
        if not player or self.projectile_cooldown > 0 or self.difficulty != "hard":
            return
        
        # Fire 3 projectiles with slight spread
        for i in range(3):
            angle_offset = (i - 1) * 30  # -30, 0, +30 degrees
            self.fire_tracking_projectile(player, angle_offset)
        
        self.projectile_cooldown = 2500
        print("Boss fires tracking projectiles!")
    
    def start_split_projectiles(self, player):
        """Fire projectiles that split mid-flight into 3 smaller ones"""
        if not player or self.projectile_cooldown > 0:
            return
        
        # Trigger Spell animation for split projectiles
        self.is_casting_single = True
        self.cast_timer = 30
        
        # Fire 1-2 splitting projectiles depending on difficulty
        num_projectiles = 2 if self.difficulty == "hard" else 1
        
        for i in range(num_projectiles):
            # Slight vertical offset for multiple projectiles
            y_offset = (i - 0.5) * 40 if num_projectiles > 1 else 0
            
            projectile = BossProjectile(
                self.rect.centerx,
                self.rect.centery - 20 + y_offset,
                player.rect.centerx,
                player.rect.centery,
                speed=4,
                damage=self.attack_damage,
                projectile_type="split_bolt",
                can_split=True,
                parent_projectiles_list=self.projectiles  # Pass reference so it can add children
            )
            self.projectiles.append(projectile)
        
        self.projectile_cooldown = 2000 if self.difficulty == "easy" else 1500
        print(f"Boss fires {num_projectiles} splitting projectile(s)!")
    
    def fire_projectile_at_player(self, player, projectile_type="shadow_bolt"):
        """Fire a projectile directly at player's current position"""
        if not player:
            return
        
        # Trigger Cast animation for single projectile
        self.is_casting_single = True
        self.cast_timer = 30  # ~0.5 seconds at 60 FPS
        
        # Aim at player's center
        projectile = BossProjectile(
            self.rect.centerx, 
            self.rect.centery - 20,  # Shoot from boss center
            player.rect.centerx,
            player.rect.centery,
            speed=5 if self.phase == 2 else 4,
            damage=self.attack_damage,
            projectile_type=projectile_type,
            can_split=False,
            parent_projectiles_list=None
        )
        self.projectiles.append(projectile)
    
    def fire_tracking_projectile(self, player, angle_offset=0):
        """Fire a projectile with slight angle offset for spread"""
        if not player:
            return
        
        # Calculate base direction to player
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        base_angle = math.degrees(math.atan2(dy, dx))
        
        # Apply offset
        final_angle = base_angle + angle_offset
        final_rad = math.radians(final_angle)
        
        # Calculate target position
        distance = 400  # How far to project the target
        target_x = self.rect.centerx + math.cos(final_rad) * distance
        target_y = self.rect.centery + math.sin(final_rad) * distance
        
        projectile = BossProjectile(
            self.rect.centerx,
            self.rect.centery - 20,
            target_x,
            target_y,
            speed=4.5,
            damage=self.attack_damage,
            projectile_type="energy_blast",
            can_split=False,
            parent_projectiles_list=None
        )
        self.projectiles.append(projectile)
        projectile = BossProjectile(
            self.rect.centerx,
            self.rect.centery - 20,
            target_x,
            target_y,
            speed=4.5,
            damage=self.attack_damage,
            projectile_type="energy_blast"
        )
        self.projectiles.append(projectile)
    
    def take_damage(self, damage):
        """Override to handle shield"""
        if self.shield_active:
            damage = damage // 2  # Shield reduces damage by half
            print(f"Shield absorbed {damage} damage!")
        
        super().take_damage(damage)
        
        # Visual feedback
        self.change_state("hurt")  # Use lowercase to match animation states
    
    def change_state(self, new_state):
        """Change the boss animation state"""
        if new_state in self.anims and self.anims[new_state]:
            self.current_state = new_state
            self.anim_frame = 0  # Reset animation frame
    
    def trigger_phase_2(self):
        """Trigger phase 2 at 50% HP with enhanced abilities"""
        self.phase = 2
        self.phase_2_triggered = True
        self.is_enraged = True
        self.speed *= 1.4  # 40% faster movement
        self.attack_cooldown = int(self.attack_cooldown * 0.7)  # 30% faster attacks
        
        # Reset all cooldowns for immediate phase 2 attack
        self.projectile_cooldown = 0
        self.dash_cooldown = 0
        self.pattern_timer = self.pattern_duration  # Force new pattern selection
        
        # Enhanced projectile abilities in phase 2
        if self.difficulty == "hard":
            self.max_hp += 100  # Slight HP boost for hard mode
            self.current_hp += 50
        
        # Create dramatic visual effect
        for i in range(80):
            angle = random.uniform(0, 360)
            speed = random.uniform(3, 12)
            self.phase_transition_particles.append({
                'x': self.rect.centerx + random.uniform(-30, 30),
                'y': self.rect.centery + random.uniform(-30, 30),
                'dx': math.cos(math.radians(angle)) * speed,
                'dy': math.sin(math.radians(angle)) * speed,
                'life': 90,
                'max_life': 90,
                'color': (255, 50, 50) if random.random() < 0.7 else (255, 200, 50)
            })
        
        # Immediate aggressive action
        self.attack_pattern = "projectile_burst" if self.difficulty == "hard" else "projectile_single"
        self.pattern_duration = 30
        
        print(f"🔥 BOSS PHASE 2 ACTIVATED! 🔥")
        print(f"Enhanced speed, projectile mastery, and {self.difficulty} mode abilities unlocked!")
    
    def update_aura_particles(self, dt):
        """Update boss aura particles"""
        # Create aura particles
        if self.phase == 2 and random.random() < 0.2:
            angle = random.uniform(0, 360)
            distance = 40
            self.aura_particles.append({
                'x': self.rect.centerx + math.cos(math.radians(angle)) * distance,
                'y': self.rect.centery + math.sin(math.radians(angle)) * distance,
                'life': 30,
                'max_life': 30,
                'color': (255, 150, 150) if self.is_enraged else (150, 150, 255)
            })
        
        # Update particles
        for particle in self.aura_particles[:]:
            particle['life'] -= dt
            particle['y'] -= dt * 0.5
            if particle['life'] <= 0:
                self.aura_particles.remove(particle)
        
        # Update phase transition particles
        for particle in self.phase_transition_particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['life'] -= dt
            if particle['life'] <= 0:
                self.phase_transition_particles.remove(particle)
    
    def update_slam_particles(self, dt):
        """Update ground slam particles"""
        for particle in self.slam_particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['dy'] += 0.3 * dt  # Gravity
            particle['life'] -= dt
            if particle['life'] <= 0:
                self.slam_particles.remove(particle)
    
    def draw(self, surface):
        """Draw boss with enhanced visuals"""
        if not self.alive or not self.visible:
            return
        
        # Draw phase transition particles
        for particle in self.phase_transition_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            size = int(3 + (particle['max_life'] - particle['life']) / 10)
            color = (*particle['color'], min(alpha, 255))
            pygame.draw.circle(surface, particle['color'][:3],
                            (int(particle['x'] - self.scroll_offset), int(particle['y'])),
                            size)
        
        # Draw boss glow aura
        if self.phase == 2:
            pulse = 1.0 + math.sin(self.boss_glow_timer) * 0.3
            screen_x = self.rect.centerx - self.scroll_offset
            screen_y = self.rect.centery
            
            for i in range(3):
                radius = int((60 + i * 20) * pulse)
                alpha = max(0, 40 - i * 15)
                color = (255, 100, 100) if self.is_enraged else (150, 150, 255)
                glow_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, alpha), (radius, radius), radius)
                surface.blit(glow_surf, (screen_x - radius, screen_y - radius))
        
        # Draw aura particles
        for particle in self.aura_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            pygame.draw.circle(surface, particle['color'][:3],
                            (int(particle['x'] - self.scroll_offset), int(particle['y'])),
                            2)
        
        # Draw shield effect
        if self.shield_active:
            screen_x = self.rect.centerx - self.scroll_offset
            screen_y = self.rect.centery
            shield_pulse = math.sin(self.boss_glow_timer * 3) * 0.2 + 0.8
            shield_radius = int(70 * shield_pulse)
            
            for i in range(2):
                radius = shield_radius - i * 10
                alpha = 50 - i * 20
                shield_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(shield_surf, (100, 200, 255, alpha), (radius, radius), radius, 3)
                surface.blit(shield_surf, (screen_x - radius, screen_y - radius))
        
        # Draw ground slam particles
        for particle in self.slam_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            size = max(1, int(4 * (particle['life'] / particle['max_life'])))
            pygame.draw.circle(surface, particle['color'][:3],
                            (int(particle['x'] - self.scroll_offset), int(particle['y'])),
                            size)
        
        # Draw projectiles
        for projectile in self.projectiles:
            projectile.draw(surface, self.scroll_offset)
        
        # Draw boss sprite - position larger sprite over smaller hitbox
        # Calculate sprite position to center it over hitbox
        sprite_x = self.rect.centerx - self.image.get_width() // 2 - self.scroll_offset
        sprite_y = self.rect.bottom - self.image.get_height()  # Align bottom with hitbox bottom
        surface.blit(self.image, (sprite_x, sprite_y))
        
        # Debug: Draw hitbox (comment out for release)
        # pygame.draw.rect(surface, (255, 0, 0), 
        #                 (self.rect.x - self.scroll_offset, self.rect.y, self.rect.width, self.rect.height), 2)
        
        # Draw enhanced health bar
        if self.alive:
            bar_width = 150
            bar_height = 12
            screen_x = self.rect.centerx - self.scroll_offset
            bar_x = screen_x - bar_width // 2
            bar_y = self.rect.y - 30
            
            # Background
            pygame.draw.rect(surface, (40, 40, 40),
                        (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4))
            
            # Health bar (color changes with phase)
            health_width = int((self.current_hp / self.max_hp) * bar_width)
            if self.phase == 2:
                bar_color = (255, 100, 100)  # Red for phase 2
            else:
                bar_color = (100, 255, 100)  # Green for phase 1
            
            pygame.draw.rect(surface, bar_color, (bar_x, bar_y, health_width, bar_height))
            
            # Border
            pygame.draw.rect(surface, (255, 255, 255),
                        (bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4), 2)
            
            # HP text
            font = pygame.font.Font(None, 20)
            hp_text = f"{self.current_hp}/{self.max_hp}"
            text_surf = font.render(hp_text, True, (255, 255, 255))
            text_rect = text_surf.get_rect(center=(screen_x, bar_y - 15))
            surface.blit(text_surf, text_rect)
            
            # Phase indicator
            if self.phase == 2:
                phase_font = pygame.font.Font(None, 24)
                phase_text = phase_font.render("PHASE 2", True, (255, 100, 100))
                phase_rect = phase_text.get_rect(center=(screen_x, bar_y + bar_height + 15))
                surface.blit(phase_text, phase_rect)
    
    def get_collision_rect(self):
        """Return the hitbox rect for collision detection (smaller than visual sprite)"""
        return self.rect


# Easy mode boss
class EasyDungeonBoss(DungeonBoss):
    """Easy difficulty boss - good for learning patterns"""
    def __init__(self, x, y):
        super().__init__(x, y, difficulty="easy")
        print("Easy Boss spawned - Good luck!")


# Hard mode boss
class HardDungeonBoss(DungeonBoss):
    """Hard difficulty boss - challenging fight"""
    def __init__(self, x, y):
        super().__init__(x, y, difficulty="hard")
        print("Hard Boss spawned - Prepare yourself!")

