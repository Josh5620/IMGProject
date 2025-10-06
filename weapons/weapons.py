"""
weapons.py - Weapon System for Main Project Integration

This integrates with your existing entities.py animation system and collision detection.
"""

import pygame
import math
from .projectiles import PlayerProjectile, EnemyProjectile, ChargedProjectile, ProjectileManager

class WeaponSystem:
    """
    Weapon system designed to integrate with your mainCharacter class.
    Add this as a mixin or copy methods directly into mainCharacter.
    """
    
    def init_weapon_system(self):
        """Call this in your mainCharacter.__init__() method"""
        # Weapon properties
        self.health = 100
        self.max_health = 100
        self.melee_cooldown = 0
        self.projectile_cooldown = 0
        self.charge_cooldown = 0
        self.is_attacking = False
        self.attack_animation_timer = 0
        
        # Melee visual effects
        self.melee_effect_timer = 0
        self.melee_effect_particles = []
        self.screen_shake_timer = 0
        
        # Charging system
        self.is_charging = False
        self.charge_time = 0
        self.max_charge_time = 120  # 2 seconds at 60 FPS
        
        # Weapon animation states (integrate with your CELL_MAP)
        self.weapon_state = None  # None, "attacking", "charging"
        
        # Track if we need to override normal animation
        self.weapon_animation_override = False
    
    def update_weapon_system(self):
        """
        Call this in your mainCharacter.update() method 
        BEFORE calling update_animation()
        """
        # Update cooldowns
        if self.melee_cooldown > 0:
            self.melee_cooldown -= 1
        if self.projectile_cooldown > 0:
            self.projectile_cooldown -= 1
        if self.charge_cooldown > 0:
            self.charge_cooldown -= 1
        
        # Update charging
        if self.is_charging and self.charge_time < self.max_charge_time:
            self.charge_time += 1
        
        # Update attack animation
        if self.attack_animation_timer > 0:
            self.attack_animation_timer -= 1
            if self.attack_animation_timer == 0:
                self.is_attacking = False
        
        # Update melee effects
        self.update_melee_effects()
    
    def get_current_weapon_animation_state(self):
        """
        Call this in your update_animation() method to check if weapon 
        should override normal movement animations.
        
        Returns: animation_state string or None if no override needed
        """
        if self.weapon_animation_override:
            if self.weapon_state == "attacking":
                return "attack"  # You'll need to add this to CELL_MAP
            elif self.weapon_state == "charging":
                return "charge"  # You'll need to add this to CELL_MAP
        
        return None  # Use normal movement-based animation
    
    def melee_attack(self, enemies, blocks=None):
        """
        Perform melee attack using your existing collision system
        
        Args:
            enemies: List of enemy objects to check for hits
            blocks: Optional list of blocks to check (for breaking blocks)
        """
        if self.melee_cooldown > 0:
            return []
        
        self.melee_cooldown = 30  # 0.5 seconds at 60 FPS
        self.is_attacking = True
        self.attack_animation_timer = 15
        self.weapon_state = "attacking"
        self.weapon_animation_override = True
        
        # Add visual effects
        self.melee_effect_timer = 20  # How long the effect lasts
        self.melee_effect_particles = []
        self.screen_shake_timer = 5  # Small screen shake on hit
        
        # TODO: Play attack sound effect
        
        hit_enemies = []
        MELEE_RANGE = 80
        MELEE_DAMAGE = 20
        
        # Create attack hitbox based on facing direction
        attack_rect = self.get_melee_hitbox(MELEE_RANGE)
        
        # Check collision with enemies using your collision system approach
        for enemy in enemies:
            if hasattr(enemy, 'rect') and attack_rect.colliderect(enemy.rect):
                hit_enemies.append(enemy)
                
                # Create hit particles at impact point
                impact_x = enemy.rect.centerx
                impact_y = enemy.rect.centery
                self.create_melee_hit_particles(impact_x, impact_y)
                
                if hasattr(enemy, 'take_damage'):
                    enemy.take_damage(MELEE_DAMAGE)
                elif hasattr(enemy, 'collideHurt'):
                    # If enemy uses same pattern as Spikes class
                    enemy.collideHurt(self, MELEE_DAMAGE)
        
        # Optional: Break blocks with melee attacks
        if blocks:
            for block in blocks[:]:  # Use slice to avoid modification during iteration
                if hasattr(block, 'rect') and attack_rect.colliderect(block.rect):
                    if hasattr(block, 'can_break') and block.can_break:
                        blocks.remove(block)
        
        return hit_enemies
    
    def create_melee_hit_particles(self, x, y):
        """Create particle effects at melee hit location"""
        import random
        
        # Create multiple particles for impact effect
        for i in range(6):
            particle = {
                'x': x + random.randint(-10, 10),
                'y': y + random.randint(-10, 10),
                'vel_x': random.uniform(-3, 3),
                'vel_y': random.uniform(-3, -1),  # Mostly upward
                'life': 20,
                'color': (255, 255, 100) if random.random() > 0.5 else (255, 200, 50),
                'size': random.randint(2, 4)
            }
            self.melee_effect_particles.append(particle)
    
    def update_melee_effects(self):
        """Update visual effects for melee attacks"""
        # Update attack timer
        if self.attack_animation_timer > 0:
            self.attack_animation_timer -= 1
            if self.attack_animation_timer <= 0:
                self.is_attacking = False
                self.weapon_animation_override = False
        
        # Update effect timer
        if self.melee_effect_timer > 0:
            self.melee_effect_timer -= 1
        
        # Update particles
        for particle in self.melee_effect_particles[:]:
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['vel_y'] += 0.2  # Gravity
            particle['life'] -= 1
            
            if particle['life'] <= 0:
                self.melee_effect_particles.remove(particle)
    
    def draw_melee_effects(self, screen, camera_offset=(0, 0)):
        """Draw visual effects for melee attacks"""
        # Draw attack range indicator (only while attacking)
        if self.is_attacking and self.attack_animation_timer > 10:
            attack_rect = self.get_melee_hitbox(80)
            # Draw semi-transparent attack arc
            attack_color = (255, 255, 255, 100)  # White with transparency
            
            # Create a surface for the attack effect
            attack_surf = pygame.Surface((attack_rect.width, attack_rect.height), pygame.SRCALPHA)
            
            # Draw attack slash effect (more prominent)
            slash_thickness = max(3, self.attack_animation_timer // 2)  # Thicker slashes
            slash_color = (255, 255, 255, 150)  # Brighter white
            
            if self.facing_right:
                # Main diagonal slash from top-left to bottom-right
                pygame.draw.line(attack_surf, slash_color, 
                               (5, 5), (attack_rect.width - 5, attack_rect.height - 5), 
                               slash_thickness)
                # Secondary horizontal slash
                pygame.draw.line(attack_surf, (255, 200, 100, 120),
                               (0, attack_rect.height // 2), (attack_rect.width, attack_rect.height // 2),
                               slash_thickness // 2)
                # Add sparkle line
                pygame.draw.line(attack_surf, (255, 255, 255, 200),
                               (attack_rect.width // 4, 0), (3 * attack_rect.width // 4, attack_rect.height),
                               2)
            else:
                # Main diagonal slash from top-right to bottom-left
                pygame.draw.line(attack_surf, slash_color,
                               (attack_rect.width - 5, 5), (5, attack_rect.height - 5),
                               slash_thickness)
                # Secondary horizontal slash
                pygame.draw.line(attack_surf, (255, 200, 100, 120),
                               (0, attack_rect.height // 2), (attack_rect.width, attack_rect.height // 2),
                               slash_thickness // 2)
                # Add sparkle line
                pygame.draw.line(attack_surf, (255, 255, 255, 200),
                               (3 * attack_rect.width // 4, 0), (attack_rect.width // 4, attack_rect.height),
                               2)
            
            screen.blit(attack_surf, (attack_rect.x - camera_offset[0], attack_rect.y - camera_offset[1]))
        
        # Draw hit particles
        for particle in self.melee_effect_particles:
            alpha = particle['life'] / 20.0  # Fade out over time
            particle_color = (
                int(particle['color'][0] * alpha),
                int(particle['color'][1] * alpha),
                int(particle['color'][2] * alpha)
            )
            
            pygame.draw.circle(screen, particle_color,
                             (int(particle['x'] - camera_offset[0]), 
                              int(particle['y'] - camera_offset[1])),
                             particle['size'])
    
    def get_melee_hitbox(self, range_pixels):
        """Create attack hitbox based on character facing direction"""
        if self.facing_right:
            # Attack to the right
            attack_x = self.rect.right
            attack_y = self.rect.centery - range_pixels // 2
        else:
            # Attack to the left
            attack_x = self.rect.left - range_pixels
            attack_y = self.rect.centery - range_pixels // 2
        
        return pygame.Rect(attack_x, attack_y, range_pixels, range_pixels)
    
    def shoot_projectile(self):
        """Create and return a player projectile"""
        if self.projectile_cooldown > 0:
            return None
        
        self.projectile_cooldown = 15  # 0.25 seconds
        
        # TODO: Play shooting sound effect
        
        # Create projectile at character's position
        direction = 1 if self.facing_right else -1
        
        if self.facing_right:
            projectile_x = self.rect.right
        else:
            projectile_x = self.rect.left - 10
        
        projectile_y = self.rect.centery
        
        return PlayerProjectile(projectile_x, projectile_y, direction)
    

    
    def start_charging(self):
        """Start charging a projectile"""
        if self.charge_cooldown > 0 or self.is_charging:
            return False
        
        self.is_charging = True
        self.charge_time = 0
        self.weapon_state = "charging"
        self.weapon_animation_override = True
        
        # TODO: Play charging sound effect
        
        return True
    
    def stop_charging_and_shoot(self, target_x=None, target_y=None):
        """Stop charging and create charged projectile"""
        if not self.is_charging:
            return None
        
        # Calculate charge level (0.0 to 1.0)
        charge_level = min(1.0, self.charge_time / self.max_charge_time)
        
        # Reset charging state
        self.is_charging = False
        self.charge_time = 0
        self.charge_cooldown = 60  # 1 second cooldown
        self.weapon_state = None
        self.weapon_animation_override = False
        
        # TODO: Play release sound effect (pitch based on charge_level)
        
        direction = 1 if self.facing_right else -1
        
        if self.facing_right:
            projectile_x = self.rect.right
        else:
            projectile_x = self.rect.left - 10
        
        projectile_y = self.rect.centery
        
        return ChargedProjectile(projectile_x, projectile_y, direction, charge_level, target_x, target_y)
    
    def cancel_charging(self):
        """Cancel charging without shooting"""
        self.is_charging = False
        self.charge_time = 0
        self.weapon_state = None
        self.weapon_animation_override = False
    
    def get_charge_level(self):
        """Get current charge level (0.0 to 1.0)"""
        if not self.is_charging:
            return 0.0
        return min(1.0, self.charge_time / self.max_charge_time)
    
    def take_weapon_damage(self, damage):
        """
        Take damage - integrates with your existing iFrame() system
        Returns True if character died
        """
        if hasattr(self, 'invulnerable') and self.invulnerable:
            return False  # Already invulnerable
        
        self.health = max(0, self.health - damage)
        
        # Trigger your existing invulnerability system
        if hasattr(self, 'iFrame'):
            self.iFrame()
        
        # TODO: Play hurt sound effect
        
        return self.health <= 0
    
    def draw_weapon_effects(self, screen, camera_offset=(0, 0)):
        """
        Draw weapon-related visual effects.
        Call this in your mainCharacter.draw() method AFTER drawing the sprite.
        
        Args:
            screen: pygame surface to draw on
            camera_offset: (x, y) camera offset for scrolling games
        """
        
        # Adjust positions for camera offset
        draw_x = self.rect.x - camera_offset[0]
        draw_y = self.rect.y - camera_offset[1]
        
        # Draw charging effects
        if self.is_charging:
            self._draw_charging_effects(screen, draw_x, draw_y)
        
        # Draw melee effects (slash effects and particles)
        self.draw_melee_effects(screen, camera_offset)
        
        # Draw melee range indicator when attacking (for debugging)
        if self.is_attacking and False:  # Set to True for debugging
            self._draw_melee_range(screen, draw_x, draw_y, camera_offset)
        
        # Draw health bar (you might want to move this to your UI system)
        self._draw_health_bar(screen, draw_x, draw_y)
    
    def _draw_charging_effects(self, screen, draw_x, draw_y):
        """Draw charging visual effects"""
        charge_level = self.get_charge_level()
        center_x = draw_x + self.rect.width // 2
        center_y = draw_y + self.rect.height // 2
        
        # Charging glow around character
        glow_radius = int(20 + charge_level * 30)
        glow_intensity = int(100 + charge_level * 155)
        
        # Pulsing effect
        pulse_factor = math.sin(self.charge_time * 0.3) * 0.3 + 0.7
        pulse_radius = int(glow_radius * pulse_factor)
        glow_color = (glow_intensity, int(glow_intensity * 0.8), glow_intensity)
        
        # Draw glow layers
        for i in range(3):
            layer_radius = pulse_radius - (i * 8)
            layer_alpha = int((glow_intensity * (3 - i)) / 6)
            if layer_radius > 0:
                pygame.draw.circle(screen, (layer_alpha, int(layer_alpha * 0.8), layer_alpha), 
                                 (center_x, center_y), layer_radius, 2)
        
        # Charging particles
        if charge_level > 0.3:
            import random
            particle_count = int(charge_level * 8)
            for _ in range(particle_count):
                if random.randint(1, 3) == 1:
                    angle = random.uniform(0, 2 * math.pi)
                    distance = random.randint(int(glow_radius * 0.7), int(glow_radius * 1.2))
                    particle_x = center_x + int(distance * math.cos(angle))
                    particle_y = center_y + int(distance * math.sin(angle))
                    particle_size = random.randint(1, 3)
                    pygame.draw.circle(screen, (255, 255, 255), (particle_x, particle_y), particle_size)
        
        # Charge level indicator bar
        self._draw_charge_bar(screen, draw_x, draw_y, charge_level)
    
    def _draw_charge_bar(self, screen, draw_x, draw_y, charge_level):
        """Draw charge level bar above character"""
        bar_width = 60
        bar_height = 6
        bar_x = draw_x
        bar_y = draw_y - 25
        
        # Background
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        # Charge level
        charge_width = int(bar_width * charge_level)
        charge_color = (int(255 * (1 - charge_level)), int(255 * charge_level), 0)
        pygame.draw.rect(screen, charge_color, (bar_x, bar_y, charge_width, bar_height))
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 1)
    
    def _draw_melee_range(self, screen, draw_x, draw_y, camera_offset):
        """Draw melee attack range for debugging"""
        MELEE_RANGE = 80
        if self.facing_right:
            range_x = draw_x + self.rect.width
            range_y = draw_y + self.rect.height // 2 - MELEE_RANGE // 2
        else:
            range_x = draw_x - MELEE_RANGE
            range_y = draw_y + self.rect.height // 2 - MELEE_RANGE // 2
        
        pygame.draw.rect(screen, (255, 255, 255), (range_x, range_y, MELEE_RANGE, MELEE_RANGE), 2)
    
    def _draw_health_bar(self, screen, draw_x, draw_y):
        """Draw health bar above character"""
        health_bar_width = 60
        health_bar_height = 6
        health_bar_x = draw_x
        health_bar_y = draw_y - 15
        
        # Background (red)
        pygame.draw.rect(screen, (255, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
        # Health (green)
        health_width = int((self.health / self.max_health) * health_bar_width)
        pygame.draw.rect(screen, (0, 255, 0), (health_bar_x, health_bar_y, health_width, health_bar_height))

def handle_projectile_collisions(projectile_manager, player, enemies, blocks):
    """
    Handle projectile collisions using your existing collision system patterns.
    Call this in your main game loop.
    
    Args:
        projectile_manager: ProjectileManager instance
        player: mainCharacter instance
        enemies: List of enemy objects
        blocks: List of block objects
    """
    
    # Check projectile-enemy collisions (from player projectiles)
    player_hits = projectile_manager.check_collisions(enemies, 'enemy')
    for hit in player_hits:
        target = hit['target']
        damage = hit['damage']
        
        if hasattr(target, 'take_damage'):
            target.take_damage(damage)
        elif hasattr(target, 'collideHurt'):
            # Use same pattern as your Spikes class
            target.collideHurt(player, damage)
        
        print(f"Player projectile hit enemy for {damage} damage!")
    
    # Check projectile-player collisions (from enemy projectiles)
    enemy_hits = projectile_manager.check_collisions([player], 'player')
    for hit in enemy_hits:
        damage = hit['damage']
        
        if hasattr(player, 'take_weapon_damage'):
            player.take_weapon_damage(damage)
        elif hasattr(player, 'iFrame'):
            # Integrate with existing damage system
            if not player.invulnerable:
                player.lives -= damage
                player.iFrame()
        
        print(f"Enemy projectile hit player for {damage} damage!")
    
    # Check projectile-block collisions
    block_hits = projectile_manager.check_collisions(blocks, None)  # Hit any projectile
    for hit in block_hits:
        block = hit['target']
        projectile = hit['projectile']
        
        # Destroy projectile on block hit
        projectile.active = False
        
        # Optional: Break destructible blocks
        if hasattr(block, 'can_break') and block.can_break:
            blocks.remove(block)

# Integration helper functions for your existing code

def add_weapon_animations_to_cell_map():
    """
    Add these to your CELL_MAP dictionary in entities.py
    You'll need to create sprite sheets for these animations.
    """
    weapon_animations = {
        'attack': [  # Melee attack animation
            (0, 0), (1, 0), (2, 0), (3, 0),  # Attack frames
            (0, 1), (1, 1), (2, 1), (3, 1)   # More attack frames
        ],
        'charge': [  # Charging animation (energy buildup)
            (0, 0), (1, 0), (2, 0), (3, 0),  # Charging frames
            (0, 1), (1, 1), (2, 1), (3, 1)   # More charging frames
        ]
    }
    
    # Add these to your existing CELL_MAP dictionary:
    # CELL_MAP.update(weapon_animations)
    
    return weapon_animations