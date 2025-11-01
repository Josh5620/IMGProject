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
    
    def __init__(self, x, y, target_x, target_y, speed=4, damage=1, projectile_type="shadow_bolt"):
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.speed = speed
        self.damage = damage
        self.projectile_type = projectile_type
        self.alive = True
        self.max_range = 800
        
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
    
    def update(self, dt, obstacles=None):
        """Update projectile movement and effects"""
        if not self.alive:
            return
        
        self.life_timer += dt
        
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
        # Load boss animations from individual files
        boss_anims = build_boss_animations_from_individual_files(BOSS_ASSETS_PATH, scale_to=(128, 128))
        super().__init__(x, y, width, height, anim_manifest={})
        
        # Override the animations with our custom loaded ones
        self.anims = boss_anims
        
        # Set initial image from loaded animations (replace brown default)
        if "idle" in self.anims and self.anims["idle"]:
            self.image = self.anims["idle"][0]
            self.current_state = "idle"
        
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
        self.pattern_timer = 0
        self.pattern_duration = 180  # 3 seconds per pattern
        
        # Dash attack
        self.is_dashing = False
        self.dash_speed = 8
        self.dash_duration = 0
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
        
        # Visual effects
        self.aura_particles = []
        self.phase_transition_particles = []
        
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
        else:
            self.execute_current_pattern(player, obstacles, dt)
        
        # Update visual effects
        self.update_aura_particles(dt)
        self.update_slam_particles(dt)
        
        # Update animations
        self.update_animation()
        
        # Apply physics
        if not self.is_dashing:
            self.apply_physics(obstacles)
    
    def choose_next_pattern(self, player):
        """Choose next attack pattern based on phase, difficulty, and player distance"""
        if not player:
            return
        
        distance_to_player = abs(self.rect.centerx - player.rect.centerx)
        height_difference = abs(self.rect.centery - player.rect.centery)
        player_on_platform = height_difference > 100  # Player is significantly higher/lower
        
        if self.phase == 1:
            # Phase 1: Basic patterns with occasional projectiles
            if distance_to_player < 150 and not player_on_platform:
                self.attack_pattern = "melee"
                self.pattern_duration = 180
            elif distance_to_player < 300 and self.dash_cooldown <= 0 and not player_on_platform:
                self.attack_pattern = "dash"
                self.pattern_duration = 60
            elif distance_to_player > 200 or player_on_platform:
                if self.projectile_cooldown <= 0:
                    self.attack_pattern = "projectile_single"
                    self.pattern_duration = 30
                else:
                    self.attack_pattern = "melee"
                    self.pattern_duration = 180
            else:
                self.attack_pattern = "melee"
                self.pattern_duration = 180
        else:
            # Phase 2: All patterns available with enhanced projectile usage
            available_patterns = []
            
            # Close range attacks
            if distance_to_player < 150 and not player_on_platform:
                available_patterns.extend(["melee", "melee"])  # Favor melee when close
                if distance_to_player < 200:
                    available_patterns.append("ground_slam")
            
            # Medium range attacks
            if distance_to_player < 300 and self.dash_cooldown <= 0 and not player_on_platform:
                available_patterns.append("dash")
            
            # Long range or platform attacks
            if distance_to_player > 150 or player_on_platform:
                if self.projectile_cooldown <= 0:
                    if self.difficulty == "hard":
                        available_patterns.extend(["projectile_burst", "projectile_tracking"])
                    else:
                        available_patterns.append("projectile_single")
            
            # Defensive patterns
            if self.shield_cooldown <= 0 and self.current_hp < self.max_hp * 0.3:  # Low health
                available_patterns.append("shield")
            
            # Hard mode exclusive
            if self.summon_cooldown <= 0 and self.difficulty == "hard":
                available_patterns.append("summon")
            
            # Fallback to melee if no patterns available
            if not available_patterns:
                available_patterns.append("melee")
            
            self.attack_pattern = random.choice(available_patterns)
            
            # Set pattern duration
            if "projectile" in self.attack_pattern:
                self.pattern_duration = 45
            elif self.attack_pattern == "dash":
                self.pattern_duration = 60
            elif self.attack_pattern == "ground_slam":
                self.pattern_duration = 90
            elif self.attack_pattern == "shield":
                self.pattern_duration = 120
            else:
                self.pattern_duration = 180
        
        print(f"Boss switches to: {self.attack_pattern} (distance: {distance_to_player:.0f}, platform: {player_on_platform})")
    
    def execute_current_pattern(self, player, obstacles, dt):
        """Execute the current attack pattern"""
        if self.attack_pattern == "melee":
            self.execute_melee_pattern(player, obstacles, dt)
        elif self.attack_pattern == "dash":
            self.start_dash_attack(player)
        elif self.attack_pattern == "ground_slam":
            self.start_ground_slam(player)
        elif self.attack_pattern == "shield":
            self.activate_shield()
        elif self.attack_pattern == "summon":
            self.summon_minions()
        elif self.attack_pattern == "projectile_single":
            self.start_single_projectile(player)
        elif self.attack_pattern == "projectile_burst":
            self.start_burst_fire(player)
        elif self.attack_pattern == "projectile_tracking":
            self.start_tracking_projectiles(player)
    
    def execute_melee_pattern(self, player, obstacles, dt):
        """Standard melee chase and attack"""
        if not player:
            return
        
        # Move towards player
        if self.rect.centerx < player.rect.centerx - 50:
            self.direction = 1
            self.facing_right = True
            self.move_horizontal(self.speed, obstacles)
        elif self.rect.centerx > player.rect.centerx + 50:
            self.direction = -1
            self.facing_right = False
            self.move_horizontal(-self.speed, obstacles)
        
        # Attack if in range
        distance = abs(self.rect.centerx - player.rect.centerx)
        if distance < 80 and self.can_attack():
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
        """Start a dash attack towards player"""
        if not player or self.is_dashing:
            return
        
        self.is_dashing = True
        self.dash_duration = 30  # 0.5 seconds at 60fps
        self.dash_cooldown = 5000 if self.difficulty == "easy" else 3000
        
        # Set dash direction
        if player.rect.centerx > self.rect.centerx:
            self.facing_right = True
        else:
            self.facing_right = False
        
        print("Boss dash attack!")
    
    def execute_dash(self, player, obstacles, dt):
        """Execute dash attack"""
        if self.dash_duration > 0:
            self.dash_duration -= dt
            
            # Move fast in dash direction
            dash_dx = self.dash_speed if self.facing_right else -self.dash_speed
            self.move_horizontal(dash_dx, obstacles)
            
            # Check collision with player
            if player and self.rect.colliderect(player.rect):
                player.take_damage(self.attack_damage)
                self.is_dashing = False
                self.dash_duration = 0
            
            # Create dash trail particles
            if random.random() < 0.3:
                self.aura_particles.append({
                    'x': self.rect.centerx,
                    'y': self.rect.centery + random.randint(-20, 20),
                    'life': 20,
                    'max_life': 20,
                    'color': (180, 100, 255)
                })
        else:
            self.is_dashing = False
    
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
        if self.slam_timer > 0:
            self.slam_timer -= dt
            return
        
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
        
        self.is_slamming = False
    
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
    
    def fire_projectile_at_player(self, player, projectile_type="shadow_bolt"):
        """Fire a projectile directly at player's current position"""
        if not player:
            return
        
        # Aim at player's center
        projectile = BossProjectile(
            self.rect.centerx, 
            self.rect.centery - 20,  # Shoot from boss center
            player.rect.centerx,
            player.rect.centery,
            speed=5 if self.phase == 2 else 4,
            damage=self.attack_damage,
            projectile_type=projectile_type
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
        
        # Draw boss sprite
        super().draw(surface)
        
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

