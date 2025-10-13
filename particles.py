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