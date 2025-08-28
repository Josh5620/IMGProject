import pygame
import random

def rescaleObject(object, scale_factor):
    scaledObject = pygame.transform.scale_by(object, scale_factor)
    return scaledObject

class pickUps:
    def __init__(self, x, y):
        self.image = None  # Will be set by subclasses
        self.rect = None   # Will be set after image is loaded
        self.x = x
        self.y = y
        self.name = ""
                # CHANGE THIS IF THE SDCREEN SIZE CHANGES###############
        self.screen_width = 960
        self.screen_height = 640
    
    def setName(self, name):
        self.name = name

    def draw(self, surface):
        if self.image and self.rect:
            surface.blit(self.image, self.rect)

    def is_colliding_with(self, player):
        if self.rect and self.rect.colliderect(player.rect):
            print("You have picked up a " + self.name + "!")
            return True
        return False

    def get_rect(self):
        return self.rect    

    def respawn(self, obstacles=None):
        """Respawn the coin at a random location within the screen bounds"""
        max_attempts = 100  # Prevent infinite loop
        attempts = 0
        
        while attempts < max_attempts:
            # Generate random position within screen bounds (with some margin)
            margin = 50
            new_x = random.randint(margin, self.screen_width - margin - self.rect.width)
            new_y = random.randint(margin, self.screen_height - margin - self.rect.height)
            
            # Create a temporary rect to test the new position
            temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
            
            # Check if the new position collides with any obstacles
            collision_found = False
            if obstacles:
                for obstacle in obstacles:
                    if temp_rect.colliderect(obstacle.get_rect()):
                        collision_found = True
                        break
            
            # If no collision, use this position
            if not collision_found:
                self.rect.topleft = (new_x, new_y)
                self.x = new_x
                self.y = new_y
                self.collected = False
                
                return
            
            attempts += 1
        
        # If we couldn't find a safe spot after max_attempts, just place it at a default location
        print("Could not find safe respawn location, using default")
        self.rect.topleft = (self.screen_width // 2, self.screen_height // 2)
        self.x = self.screen_width // 2
        self.y = self.screen_height // 2
        self.collected = False

class Coin(pickUps):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = pygame.image.load("assets/coin.png")
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.setName("Coin")
        self.collected = False

    def update(self, player):
        if not self.collected and self.is_colliding_with(player):
            self.collected = True
            return True
        return False
    
    def respawn(self, obstacles=None):
        super().respawn(obstacles)
        print(f"Coin respawned at ({self.x}, {self.y})")

class Meat(pickUps):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = rescaleObject(pygame.image.load("assets/meat.png"), 1)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.setName("Meat")

    def draw(self, surface):
        if self.image and self.rect:
            surface.blit(self.image, self.rect)

    def update(self, player):
        if self.is_colliding_with(player):
            return True
        return False