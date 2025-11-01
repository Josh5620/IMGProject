"""
Level 2 Boss - Final Dungeon Boss with Easy and Hard modes
Two-phase boss fight with unique attack patterns
"""

import pygame
import math
import random
from Level2Enemies import Level2Enemy, BoneParticle, build_state_animations_from_manifest

# Boss animation manifest (using skeleton sprites as base)
BOSS_ANIM = {
    "Idle": {
        "file": "assets/Level2/Skeleton/Idle.png",
        "frame_width": 150,
        "frame_count": 4,
        "scale_to": (192, 192)  # Larger than regular skeleton
    },
    "Walk": {
        "file": "assets/Level2/Skeleton/Walk.png",
        "frame_width": 150,
        "frame_count": 4,
        "scale_to": (192, 192)
    },
    "Attack": {
        "file": "assets/Level2/Skeleton/Attack.png",
        "frame_width": 150,
        "frame_count": 8,
        "scale_to": (192, 192)
    },
    "Shield": {
        "file": "assets/Level2/Skeleton/Shield.png",
        "frame_width": 150,
        "frame_count": 4,
        "scale_to": (192, 192)
    },
    "Take Hit": {
        "file": "assets/Level2/Skeleton/Take Hit.png",
        "frame_width": 150,
        "frame_count": 4,
        "scale_to": (192, 192)
    },
    "Death": {
        "file": "assets/Level2/Skeleton/Death.png",
        "frame_width": 150,
        "frame_count": 4,
        "scale_to": (192, 192)
    }
}


class DungeonBoss(Level2Enemy):
    """Base boss class with common functionality"""
    
    def __init__(self, x, y, difficulty="easy", width=192, height=192):
        super().__init__(x, y, width, height, anim_manifest=BOSS_ANIM)
        
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
        
        # Summon minions
        self.summon_cooldown = 0
        self.minions_summoned = []
        
        # Ground slam attack
        self.slam_particles = []
        self.is_slamming = False
        self.slam_timer = 0
        
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
        if self.shield_duration > 0:
            self.shield_duration -= dt * 16.67
            if self.shield_duration <= 0:
                self.shield_active = False
        
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
            self.execute_shield_mode(player, dt)
        else:
            self.execute_current_pattern(player, obstacles, dt)
        
        # Update visual effects
        self.update_aura_particles(dt)
        self.update_slam_particles(dt)
        
        # Apply physics
        if not self.is_dashing:
            self.apply_physics(obstacles)
    
    def choose_next_pattern(self, player):
        """Choose next attack pattern based on phase and difficulty"""
        if not player:
            return
        
        distance_to_player = abs(self.rect.centerx - player.rect.centerx)
        
        if self.phase == 1:
            # Phase 1: Simpler patterns
            if distance_to_player < 150:
                self.attack_pattern = "melee"
            elif distance_to_player < 300 and self.dash_cooldown <= 0:
                self.attack_pattern = "dash"
                self.pattern_duration = 60  # Shorter for dash
            else:
                self.attack_pattern = "melee"
                self.pattern_duration = 180
        else:
            # Phase 2: All patterns available
            available_patterns = ["melee"]
            
            if self.dash_cooldown <= 0:
                available_patterns.append("dash")
            if self.shield_cooldown <= 0:
                available_patterns.append("shield")
            if self.summon_cooldown <= 0 and self.difficulty == "hard":
                available_patterns.append("summon")
            
            # Add ground slam for both difficulties in phase 2
            if distance_to_player < 200:
                available_patterns.append("ground_slam")
            
            self.attack_pattern = random.choice(available_patterns)
            
            # Set pattern duration
            if self.attack_pattern == "dash":
                self.pattern_duration = 60
            elif self.attack_pattern == "ground_slam":
                self.pattern_duration = 90
            elif self.attack_pattern == "shield":
                self.pattern_duration = 120
            else:
                self.pattern_duration = 180
        
        print(f"Boss switches to: {self.attack_pattern}")
    
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
    
    def take_damage(self, damage):
        """Override to handle shield"""
        if self.shield_active:
            damage = damage // 2  # Shield reduces damage by half
            print(f"Shield absorbed {damage} damage!")
        
        super().take_damage(damage)
        
        # Visual feedback
        self.change_state("Take Hit")
    
    def trigger_phase_2(self):
        """Trigger phase 2 at 50% HP"""
        self.phase = 2
        self.phase_2_triggered = True
        self.is_enraged = True
        self.speed *= 1.3  # 30% faster
        self.attack_cooldown = int(self.attack_cooldown * 0.8)  # 20% faster attacks
        
        # Create dramatic visual effect
        for i in range(50):
            angle = random.uniform(0, 360)
            speed = random.uniform(2, 8)
            self.phase_transition_particles.append({
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'dx': math.cos(math.radians(angle)) * speed,
                'dy': math.sin(math.radians(angle)) * speed,
                'life': 60,
                'max_life': 60,
                'color': (255, 100, 100)
            })
        
        print(f"BOSS PHASE 2! Speed increased, attacks faster!")
    
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

