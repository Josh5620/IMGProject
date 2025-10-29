# particles.py
import pygame
import random

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, *args, **kwargs):
        pass

    def draw(self, surface, scroll):
        pass



class LeafParticle(Particle):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.size = random.randint(5, 15)
        self.speed_x = random.uniform(-0.5, 0.5)
        self.speed_y = random.uniform(0.5, 1.5)
        self.angle = random.randint(0, 360)
        self.rotation_speed = random.uniform(-1, 1)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (139, 69, 19), (0, 0, self.size, self.size / 2))
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self, obstacles, scroll):
        self.x += self.speed_x
        self.y += self.speed_y
        self.angle += self.rotation_speed
        self.rect.center = (self.x, self.y)

        if self.y > 640:
            self.y = -self.size
            self.x = random.randint(0, 960)

        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                self.y = -self.size # Move the leaf off-screen to make it "disappear"
                self.x = random.randint(0, 960)
                break

    def draw(self, surface, scroll):
        rotated_image = pygame.transform.rotate(self.image, self.angle)
        surface.blit(rotated_image, (self.x - scroll, self.y))


class ScreenDropletParticle:
    def __init__(self):

        self.relative_x = random.uniform(-10, 10)
        self.relative_y = 20  # Start below the center point

        # Simple physics for the visual effect
        self.speed_y = random.uniform(1, 2.5)
        self.lifespan = random.randint(20, 40)
        self.color = (100, 150, 255)
        self.size = random.randint(3, 5)

    def update(self):

        self.relative_y += self.speed_y  # Just falls straight down
        self.lifespan -= 1


class DashTrailParticle(Particle):
    """Blue trail particle for dash effect"""
    def __init__(self, x, y, direction):
        super().__init__(x, y)
        # Store as relative position from player center
        self.relative_x = 0
        self.relative_y = random.uniform(-15, 15)
        self.direction = direction  # -1 for left, 1 for right
        self.speed_x = random.uniform(-2, -0.5) * direction  # Trail behind
        self.speed_y = random.uniform(-1, 1)
        self.lifespan = random.randint(8, 15)
        self.max_lifespan = self.lifespan
        self.size = random.randint(4, 8)
        # Bright cyan/blue color
        self.color = (0, 200, 255)
        self.alpha = 255
        
    def update(self, *args, **kwargs):
        self.relative_x += self.speed_x
        self.relative_y += self.speed_y
        self.lifespan -= 1
        # Fade out over time
        self.alpha = int(255 * (self.lifespan / self.max_lifespan))
        # Shrink over time
        self.size = max(1, int(8 * (self.lifespan / self.max_lifespan)))
        
    def draw(self, surface, anchor_x, anchor_y):
        """Draw relative to anchor position (player center)"""
        if self.lifespan > 0:
            particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, self.alpha)
            pygame.draw.circle(particle_surface, color_with_alpha, (self.size, self.size), self.size)
            draw_x = anchor_x + self.relative_x - self.size
            draw_y = anchor_y + self.relative_y - self.size
            surface.blit(particle_surface, (draw_x, draw_y))
    
    def is_dead(self):
        return self.lifespan <= 0


class DoubleJumpParticle(Particle):
    """Smoke/cloud particle for double jump effect"""
    def __init__(self, x, y):
        super().__init__(x, y)
        # Store as relative position from player
        self.relative_x = random.uniform(-10, 10)
        self.relative_y = 10  # Start at player's feet
        self.speed_x = random.uniform(-1.5, 1.5)
        self.speed_y = random.uniform(-2, -0.5)  # Upward
        self.lifespan = random.randint(15, 25)
        self.max_lifespan = self.lifespan
        self.size = random.randint(6, 10)
        # Light blue/white smoke color
        self.color = random.choice([
            (180, 220, 255),  # Light blue
            (200, 230, 255),  # Very light blue
            (220, 240, 255),  # Almost white with blue tint
        ])
        self.alpha = 200
        
    def update(self, *args, **kwargs):
        self.relative_x += self.speed_x
        self.relative_y += self.speed_y
        self.speed_y -= 0.15  # Upward acceleration (smoke rises)
        self.lifespan -= 1
        # Fade out over time
        self.alpha = int(200 * (self.lifespan / self.max_lifespan))
        # Grow slightly over time (smoke expands)
        growth_factor = 1 + (1 - self.lifespan / self.max_lifespan) * 0.5
        self.size = int(10 * growth_factor)
        
    def draw(self, surface, anchor_x, anchor_y):
        """Draw relative to anchor position (player center)"""
        if self.lifespan > 0:
            particle_surface = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
            color_with_alpha = (*self.color, self.alpha)
            pygame.draw.circle(particle_surface, color_with_alpha, (self.size, self.size), self.size)
            draw_x = anchor_x + self.relative_x - self.size
            draw_y = anchor_y + self.relative_y - self.size
            surface.blit(particle_surface, (draw_x, draw_y))
    
    def is_dead(self):
        return self.lifespan <= 0