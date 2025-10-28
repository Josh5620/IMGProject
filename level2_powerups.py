"""
Level 2 Powerups for Red Riding Hood Character
Enhanced powerups with unique abilities and visual effects
"""

import pygame
import math
import random


class Level2Powerup:
    """Enhanced powerup class specifically for Level 2 gameplay with red riding hood theming"""
    
    def __init__(self, x, y, powerup_type="health_burst"):
        self.rect = pygame.Rect(x, y, 45, 45)  # Slightly bigger than Level 1
        self.powerup_type = powerup_type
        self.collected = False
        self.bob_timer = 0
        self.original_y = y
        self.rotation = 0
        self.pulse_timer = 0
        self.collection_particles = []
        self.sparkle_timer = 0
        
        # Enhanced colors with fairy tale theming (red, white, gold)
        self.colors = {
            "health_burst": {"main": (255, 100, 100), "glow": (255, 150, 150), "bright": (255, 200, 200), "theme": "Healing"},
            "fire_cloak": {"main": (255, 200, 0), "glow": (255, 220, 50), "bright": (255, 240, 100), "theme": "Fire Protection"},
            "speed_wind": {"main": (100, 200, 255), "glow": (150, 220, 255), "bright": (200, 240, 255), "theme": "Wind Speed"},
            "wolf_strength": {"main": (139, 69, 19), "glow": (160, 90, 40), "bright": (200, 120, 60), "theme": "Wolf Strength"},
            "grandma_amulet": {"main": (255, 100, 200), "glow": (255, 150, 220), "bright": (255, 200, 240), "theme": "Protection Amulet"},
            "forest_wisdom": {"main": (34, 139, 34), "glow": (60, 180, 75), "bright": (100, 220, 120), "theme": "Forest Wisdom"}
        }
        
        self.color_set = self.colors.get(powerup_type, {
            "main": (255, 255, 255), 
            "glow": (200, 200, 200), 
            "bright": (255, 255, 255),
            "theme": "Unknown"
        })
    
    def update(self, player, dt=1.0):
        """Update powerup with fairy tale animations and effects"""
        if self.collected:
            self.update_collection_particles(dt)
            return
            
        # Enhanced bobbing with gentle floating
        self.bob_timer += dt * 0.12
        self.rect.y = self.original_y + int(math.sin(self.bob_timer) * 10)
        
        # Smooth rotation
        self.rotation += dt * 1.5
        if self.rotation >= 360:
            self.rotation = 0
        
        # Pulsing glow effect
        self.pulse_timer += dt * 0.15
        self.sparkle_timer += dt * 0.3
        
        # Check collision with player
        if self.rect.colliderect(player.rect):
            self.create_collection_particles()
            self.apply_effect(player)
            self.collected = True
    
    def apply_effect(self, player):
        """Apply Level 2 powerup effect to player"""
        print(f"Red Riding Hood activated {self.color_set['theme']}!")
        player.apply_level2_powerup(self.powerup_type)
    
    def create_collection_particles(self):
        """Create special collection particles with fairy tale magic effect"""
        for i in range(20):  # More particles for magical effect
            particle = {
                'x': self.rect.centerx + random.randint(-15, 15),
                'y': self.rect.centery + random.randint(-15, 15),
                'dx': random.uniform(-4, 4),
                'dy': random.uniform(-5, 2),
                'life': 40,
                'max_life': 40,
                'color': self.color_set["bright"],
                'size': random.randint(2, 5)
            }
            self.collection_particles.append(particle)
    
    def update_collection_particles(self, dt):
        """Update collection particle effects"""
        for particle in self.collection_particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['dy'] += 0.15 * dt  # Gentler gravity for magical feel
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.collection_particles.remove(particle)
    
    def draw_icon(self, surface, center_x, center_y, size):
        """Draw powerup-specific fairy tale icon"""
        if self.powerup_type == "health_burst":
            # Draw heart with cross (healing)
            heart_points = []
            for i in range(10):
                angle = i * 36
                x = center_x + int((size//3) * math.cos(math.radians(angle)))
                y = center_y + int((size//3) * math.sin(math.radians(angle)))
                heart_points.append((x, y))
            pygame.draw.polygon(surface, self.color_set["bright"], heart_points)
        
        elif self.powerup_type == "fire_cloak":
            # Draw flames
            for i in range(3):
                x_offset = (i - 1) * (size // 6)
                flame_points = [
                    (center_x + x_offset, center_y + size//3),
                    (center_x + x_offset - size//8, center_y - size//6),
                    (center_x + x_offset, center_y - size//4),
                    (center_x + x_offset + size//8, center_y - size//6),
                ]
                pygame.draw.polygon(surface, self.color_set["bright"], flame_points)
        
        elif self.powerup_type == "speed_wind":
            # Draw wind lines
            for i in range(5):
                start_x = center_x - size//2
                start_y = center_y - size//3 + i * (size//3)
                end_x = center_x + size//4
                end_y = start_y - 5
                pygame.draw.line(surface, self.color_set["bright"], 
                            (start_x, start_y), (end_x, end_y), 3)
        
        elif self.powerup_type == "wolf_strength":
            # Draw strength symbol (claws)
            for i in range(3):
                angle = (i - 1) * 30
                x1 = center_x + int((size//4) * math.cos(math.radians(angle)))
                y1 = center_y + int((size//4) * math.sin(math.radians(angle)))
                x2 = center_x + int((size//2) * math.cos(math.radians(angle)))
                y2 = center_y + int((size//2) * math.sin(math.radians(angle)))
                pygame.draw.line(surface, self.color_set["bright"], (x1, y1), (x2, y2), 4)
        
        elif self.powerup_type == "grandma_amulet":
            # Draw amulet/circle with gem
            pygame.draw.circle(surface, self.color_set["bright"], 
                            (center_x, center_y), size//3, 3)
            pygame.draw.circle(surface, self.color_set["main"], 
                            (center_x, center_y), size//6)
        
        elif self.powerup_type == "forest_wisdom":
            # Draw leaf pattern
            for i in range(5):
                angle = i * 72
                x = center_x + int((size//3) * math.cos(math.radians(angle)))
                y = center_y + int((size//3) * math.sin(math.radians(angle)))
                pygame.draw.circle(surface, self.color_set["bright"], (x, y), size//8)
    
    def draw(self, surface):
        """Draw powerup with enhanced fairy tale visual effects"""
        if self.collected:
            # Draw collection particles
            for particle in self.collection_particles:
                alpha = int(255 * (particle['life'] / particle['max_life']))
                if alpha > 0:
                    color = (*particle['color'], min(alpha, 255))
                    pygame.draw.circle(surface, color[:3], 
                                    (int(particle['x']), int(particle['y'])), 
                                    particle['size'])
            return
        
        center_x = self.rect.centerx
        center_y = self.rect.centery
        
        # Enhanced pulsing effect
        pulse_scale = 1.0 + math.sin(self.pulse_timer) * 0.25
        glow_radius = int(30 * pulse_scale)
        
        # Outer magical glow (more intense)
        for i in range(4):
            radius = glow_radius - i * 4
            if radius > 0:
                alpha = 40 - i * 8
                glow_color = (*self.color_set["glow"], alpha)
                pygame.draw.circle(surface, glow_color[:3], 
                                (center_x, center_y), radius)
        
        # Rotating outer ring
        ring_size = int(22 * pulse_scale)
        for i in range(8):
            angle = math.radians(self.rotation + i * 45)
            x = center_x + int(ring_size * math.cos(angle))
            y = center_y + int(ring_size * math.sin(angle))
            sparkle_size = int(3 + 2 * math.sin(self.sparkle_timer + i))
            pygame.draw.circle(surface, self.color_set["bright"], (x, y), sparkle_size)
        
        # Main powerup circle
        main_radius = int(20 * pulse_scale)
        pygame.draw.circle(surface, self.color_set["main"], 
                        (center_x, center_y), main_radius)
        
        # Inner bright core
        inner_radius = int(14 * pulse_scale)
        pygame.draw.circle(surface, self.color_set["bright"], 
                        (center_x, center_y), inner_radius)
        
        # Draw themed icon
        icon_size = int(24 * pulse_scale)
        self.draw_icon(surface, center_x, center_y, icon_size)
        
        # Magical sparkle trail
        sparkle_count = 6
        for i in range(sparkle_count):
            angle = (self.sparkle_timer * 60 + i * 60) % 360
            sparkle_distance = 35 + math.sin(self.sparkle_timer * 2 + i) * 8
            sparkle_x = center_x + int(sparkle_distance * math.cos(math.radians(angle)))
            sparkle_y = center_y + int(sparkle_distance * math.sin(math.radians(angle)))
            
            sparkle_alpha = int(150 + 105 * math.sin(self.sparkle_timer * 3 + i))
            sparkle_size = 3 + int(math.sin(self.sparkle_timer * 4 + i))
            pygame.draw.circle(surface, (*self.color_set["bright"], sparkle_alpha), 
                            (sparkle_x, sparkle_y), sparkle_size)


# Powerup types for Level 2
LEVEL2_POWERUP_TYPES = [
    "health_burst",      # Instant full health restoration
    "fire_cloak",        # Temporary invincibility
    "speed_wind",        # Enhanced speed boost
    "wolf_strength",     # Damage multiplier
    "grandma_amulet",    # Shield protection
    "forest_wisdom"      # Ultimate ability
]

