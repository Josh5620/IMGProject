import pygame

class mainCharacter:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load("mc.png")
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def move(self, dx, dy, obstacles=None):
        old_x, old_y = self.rect.x, self.rect.y
        
        
        self.rect.x += dx
        if obstacles and self.check_collision(obstacles):
            self.rect.x = old_x

        
        self.rect.y += dy
        if obstacles and self.check_collision(obstacles):
            self.rect.y = old_y

    def jump(self):
        self.rect.y -= 100

    def check_collision(self, obstacles):
        
        for obstacle in obstacles:
            if self.rect.colliderect(obstacle.rect):
                return True
        return False

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def get_position(self):
        return self.rect.topleft
    
    def startGrav(self):
        self.gravEnabled = True
        while self.gravEnabled:
            self.rect.y += 1
            if self.check_collision(obstacles):
                self.rect.y -= 1
                break
            


class block:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load("block.png")
        
        self.rect = self.image.get_rect()
        self.image = pygame.transform.scale(self.image, (self.rect.width // 10, self.rect.height // 10))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def is_colliding_with(self, player):
        
        return self.rect.colliderect(player.rect)

    
