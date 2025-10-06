import pygame
import math

class BaseProjectile:
    """Base class for all projectiles - defines common behavior"""
    def __init__(self, x, y, direction, speed=8, damage=15):
        self.x = x
        self.y = y
        self.width = 10
        self.height = 5
        self.speed = speed
        self.direction = direction  # 1 for right, -1 for left
        self.damage = damage
        self.active = True
        self.owner = None  # Will be set to 'player' or 'enemy'
        
    def update(self):
        """Base update - can be overridden by subclasses"""
        # Move projectile
        self.x += self.speed * self.direction
        
        # Remove if off screen
        if self.x < -50 or self.x > 1250:  # Give some buffer
            self.active = False
    
    def get_rect(self):
        """Get collision rectangle"""
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def draw(self, screen):
        """Base draw method - should be overridden by subclasses"""
        if self.active:
            pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.width, self.height))
    
    def on_hit(self, target):
        """Called when projectile hits something - can be overridden"""
        self.active = False
        return self.damage

class PlayerProjectile(BaseProjectile):
    """Player's projectile - fast fish projectile"""
    def __init__(self, x, y, direction):
        super().__init__(x, y, direction, speed=10, damage=20)
        self.owner = 'player'
        self.trail_positions = []  # For trail effect
        
        # Load fish image
        try:
            self.image = pygame.image.load("fish.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (40, 24))  # Made bigger: doubled size
            # Flip image if going left
            if direction == -1:
                self.image = pygame.transform.flip(self.image, True, False)
            self.width = 40
            self.height = 24
        except:
            self.image = None
            print("Could not load fish.png, using default drawing")
        
    def update(self):
        # Add current position to trail
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > 5:
            self.trail_positions.pop(0)
            
        super().update()
    
    def draw(self, screen):
        if not self.active:
            return
            
        # Draw trail effect (bigger bubbles for visibility)
        for i, (trail_x, trail_y) in enumerate(self.trail_positions):
            alpha = (i + 1) / len(self.trail_positions)
            trail_color = (int(100 * alpha), int(150 * alpha), int(255 * alpha))  # Blue trail for fish
            bubble_size = int(3 + alpha * 2)  # Bigger bubbles: 3-5 pixels
            pygame.draw.circle(screen, trail_color, (int(trail_x), int(trail_y + self.height//2)), bubble_size)
        
        # Draw fish projectile
        if self.image:
            screen.blit(self.image, (self.x, self.y))
        else:
            # Fallback drawing if image failed to load
            pygame.draw.rect(screen, (100, 150, 255), (self.x, self.y, self.width, self.height))
            pygame.draw.circle(screen, (150, 200, 255), (int(self.x + self.width//2), int(self.y + self.height//2)), 3)

class EnemyProjectile(BaseProjectile):
    """Enemy's projectile - slower, red, with arc trajectory"""
    def __init__(self, x, y, direction, target_x=None, target_y=None):
        super().__init__(x, y, direction, speed=6, damage=15)
        self.owner = 'enemy'
        self.start_y = y
        self.distance_traveled = 0
        self.arc_height = 30  # How high the arc goes
        
        # Calculate arc trajectory if target is provided
        if target_x is not None and target_y is not None:
            self.target_x = target_x
            self.target_y = target_y
            self.use_arc = True
        else:
            self.use_arc = False
    
    def update(self):
        # Move horizontally
        self.x += self.speed * self.direction
        self.distance_traveled += abs(self.speed)
        
        # Apply arc trajectory
        if self.use_arc:
            # Simple parabolic arc
            progress = self.distance_traveled / 200.0  # Adjust for arc length
            if progress <= 1.0:
                self.y = self.start_y - (self.arc_height * 4 * progress * (1 - progress))
        
        # Remove if off screen
        if self.x < -50 or self.x > 1250:
            self.active = False
    
    def draw(self, screen):
        if not self.active:
            return
            
        # Draw main projectile (red fireball)
        pygame.draw.circle(screen, (255, 50, 50), (int(self.x + self.width//2), int(self.y + self.height//2)), 4)
        pygame.draw.circle(screen, (255, 150, 100), (int(self.x + self.width//2), int(self.y + self.height//2)), 2)


class ChargedProjectile(BaseProjectile):
    """Charged projectile with arc trajectory based on charge level"""
    def __init__(self, x, y, direction, charge_level, target_x=None, target_y=None):
        # Scale properties based on charge level (0.0 to 1.0)
        speed = 5 + (charge_level * 10)  # Speed: 5-15
        damage = 15 + int(charge_level * 35)  # Damage: 15-50
        
        super().__init__(x, y, direction, speed, damage)
        self.owner = 'player'
        self.charge_level = charge_level
        self.start_x = x
        self.start_y = y
        self.target_x = target_x if target_x else x + (direction * 200 * (1 + charge_level))
        self.target_y = target_y if target_y else y
        
        # Arc trajectory calculations
        self.distance_to_target = abs(self.target_x - self.start_x)
        self.max_arc_height = 50 + (charge_level * 100)  # Arc height: 50-150 pixels
        self.distance_traveled = 0
        self.total_distance = self.distance_to_target
        
        # Load fish image for charged projectile
        try:
            self.image = pygame.image.load("fish.png").convert_alpha()
            # Make charged fish larger based on charge level (30-60 pixels wide)
            fish_size = int(30 + (charge_level * 30))
            fish_height = int(fish_size * 0.6)  # Maintain aspect ratio
            self.image = pygame.transform.scale(self.image, (fish_size, fish_height))
            # Flip image if going left
            if direction == -1:
                self.image = pygame.transform.flip(self.image, True, False)
            self.width = fish_size
            self.height = fish_height
        except:
            self.image = None
            print("Could not load fish.png for charged projectile")
        
        # Visual effects based on charge
        self.size = 3 + int(charge_level * 7)  # Size: 3-10 (for fallback circles)
        self.trail_length = int(3 + charge_level * 7)  # Trail: 3-10 points
        self.trail_positions = []
        
        # Color intensity based on charge (gold/yellow for charged fish)
        self.base_color = (int(255), int(200 + charge_level * 55), int(50))  # Gold color
        self.glow_color = (int(255), int(255), int(150 + charge_level * 105))  # Bright gold
        
    def update(self):
        # Calculate progress along the arc (0.0 to 1.0)
        if self.total_distance > 0:
            progress = self.distance_traveled / self.total_distance
        else:
            progress = 1.0
        
        if progress >= 1.0:
            self.active = False
            return
        
        # Calculate position along arc
        # X position (linear interpolation)
        self.x = self.start_x + (self.target_x - self.start_x) * progress
        
        # Y position (parabolic arc)
        arc_factor = 4 * progress * (1 - progress)  # Parabolic curve (0 at start/end, 1 at middle)
        self.y = self.start_y + (self.target_y - self.start_y) * progress - (self.max_arc_height * arc_factor)
        
        # Update distance traveled
        self.distance_traveled += self.speed
        
        # Add current position to trail
        self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > self.trail_length:
            self.trail_positions.pop(0)
    
    def draw(self, screen):
        if not self.active:
            return
        
        # Draw trail effect (gold/yellow sparkles for charged fish)
        for i, (trail_x, trail_y) in enumerate(self.trail_positions):
            trail_alpha = (i + 1) / len(self.trail_positions)
            trail_size = int(self.size * trail_alpha * 0.7)
            trail_color = (
                int(self.base_color[0] * trail_alpha),
                int(self.base_color[1] * trail_alpha),
                int(self.base_color[2] * trail_alpha)
            )
            if trail_size > 0:
                pygame.draw.circle(screen, trail_color, (int(trail_x), int(trail_y)), trail_size)
        
        # Draw charged fish projectile
        if self.image:
            # Add glow effect around fish
            glow_rect = self.image.get_rect()
            glow_rect.center = (int(self.x), int(self.y))
            
            # Create a glowing effect by drawing multiple slightly offset fish with reduced alpha
            glow_offsets = [(-2, -2), (-2, 2), (2, -2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)]
            glow_surf = pygame.Surface((self.width + 4, self.height + 4), pygame.SRCALPHA)
            glow_surf.fill((*self.glow_color, 100))  # Semi-transparent glow
            
            for offset_x, offset_y in glow_offsets:
                glow_pos = (glow_rect.x + offset_x, glow_rect.y + offset_y)
                screen.blit(glow_surf, glow_pos, special_flags=pygame.BLEND_ADD)
            
            # Draw the main fish
            screen.blit(self.image, glow_rect)
        else:
            # Fallback: draw circles if fish image failed to load
            center_x, center_y = int(self.x), int(self.y)
            
            # Outer glow (larger, dimmer)
            pygame.draw.circle(screen, self.glow_color, (center_x, center_y), self.size + 2)
            
            # Main projectile
            pygame.draw.circle(screen, self.base_color, (center_x, center_y), self.size)
            
            # Inner core (bright white)
            core_size = max(1, int(self.size * 0.4))
            pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), core_size)
        
        # Add charge-based sparkle effects around the projectile
        if self.charge_level > 0.5:
            import random
            center_x, center_y = int(self.x), int(self.y)  # Define center position
            for _ in range(int(self.charge_level * 3)):
                if random.randint(1, 4) == 1:
                    sparkle_distance = random.randint(5, 15)
                    angle = random.uniform(0, 2 * math.pi)
                    sparkle_x = center_x + int(sparkle_distance * math.cos(angle))
                    sparkle_y = center_y + int(sparkle_distance * math.sin(angle))
                    sparkle_color = (255, 255, 255) if random.randint(1, 2) == 1 else self.glow_color
                    pygame.draw.circle(screen, sparkle_color, (sparkle_x, sparkle_y), 1)
    
    def get_charge_info(self):
        """Return information about this charged projectile"""
        return {
            'charge_level': self.charge_level,
            'damage': self.damage,
            'arc_height': self.max_arc_height,
            'size': self.size
        }

class ProjectileManager:
    """Manages all projectiles in the game"""
    def __init__(self):
        self.projectiles = []
    
    def add_projectile(self, projectile):
        """Add a projectile to the manager"""
        self.projectiles.append(projectile)
    
    def update(self):
        """Update all projectiles"""
        for projectile in self.projectiles:
            projectile.update()
        
        # Remove inactive projectiles
        self.projectiles = [p for p in self.projectiles if p.active]
    
    def draw(self, screen):
        """Draw all projectiles"""
        for projectile in self.projectiles:
            projectile.draw(screen)
    
    def check_collisions(self, targets, projectile_owner=None):
        """Check collisions between projectiles and targets"""
        hits = []
        
        for projectile in self.projectiles[:]:  # Use slice to avoid modification during iteration
            if not projectile.active:
                continue
            
            # Skip if projectile belongs to same owner as targets
            if projectile_owner and projectile.owner == projectile_owner:
                continue
                
            projectile_rect = projectile.get_rect()
            
            for target in targets:
                if hasattr(target, 'get_rect'):
                    target_rect = target.get_rect()
                    if projectile_rect.colliderect(target_rect):
                        damage = projectile.on_hit(target)
                        hits.append({
                            'projectile': projectile,
                            'target': target,
                            'damage': damage
                        })
                        break
        
        return hits
    
    def get_projectiles_by_owner(self, owner):
        """Get all projectiles belonging to a specific owner"""
        return [p for p in self.projectiles if p.owner == owner]
    
    def clear_all(self):
        """Remove all projectiles"""
        self.projectiles.clear()
    
    def get_count(self):
        """Get total number of active projectiles"""
        return len(self.projectiles)