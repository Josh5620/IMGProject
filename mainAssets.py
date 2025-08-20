import pygame

class mainCharacter:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load("mc.png")
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def move(self, dx, dy, obstacles=None):
        # Store old position
        old_x, old_y = self.rect.x, self.rect.y
        
        # Move horizontally first
        self.rect.x += dx
        if obstacles and self.check_collision(obstacles):
            self.rect.x = old_x  # Undo horizontal movement
        
        # Move vertically second
        self.rect.y += dy
        if obstacles and self.check_collision(obstacles):
            self.rect.y = old_y  # Undo vertical movement
    
    def check_collision(self, obstacles):
        """Simple collision check - returns True if colliding with any obstacle"""
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                return True
        return False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def get_position(self):
        return self.rect.topleft

    def startGrav(self, gravLine):
        self.gravEnabled = True
        self.gravLine = gravLine


class block:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load("block.png")
        
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (self.rect.width // 4, self.rect.height // 4))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def is_colliding_with(self, player):
        """Simple collision check - just returns True/False"""
        return self.rect.colliderect(player.rect)

    
