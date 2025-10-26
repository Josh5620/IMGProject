import pygame

def rescaleObject(object, scale_factor):
    scaledObject = pygame.transform.scale_by(object, scale_factor)
    return scaledObject

class block:
    def __init__(self, x, y):
        self.original_x = x
        self.original_y = y
        self.x = x
        self.y = y
        self.image = pygame.Surface((16,16), pygame.SRCALPHA)  
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.solid = True
    
    def update_position(self, scroll):
        self.rect.x = self.original_x - scroll
        self.rect.y = self.original_y
    
    def draw(self, surface):
        if self.rect.x > -self.rect.width and self.rect.x < surface.get_width():
            surface.blit(self.image, self.rect.topleft)

    def collideHurt(self, player):
        return 0
    
    def get_rect(self):
        return self.rect
    
    
class Spikes(block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = rescaleObject(pygame.image.load("assets/spike.png"),1 )
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        
    
    def collideHurt(self, player):
        if self.rect.colliderect(player.rect):
            if not player.invulnerable:
                print("Ouch! Hit Spikes!")
                player.lives -= 1
                player.iFrame()
        return 0

    def draw(self, surface):
        if self.rect.x > -self.rect.width and self.rect.x < surface.get_width():
            surface.blit(self.image, self.rect.topleft)

class start(block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.solid = False
        
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
    
    def collideHurt(self, player):
        return 0

class end(block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.solid = False
 
        
        
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA) 
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    
    def collideHurt(self, player):
        if self.rect.colliderect(player.rect):
            print("You Win!")
            player.won = True
            return 0

class Ice(block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = rescaleObject(pygame.image.load("assets/block.png"), 0.1)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)

    def collideHurt(self, player):
        current_time = pygame.time.get_ticks()
        if not hasattr(player, 'slow_until') or current_time > player.slow_until:
            print("Slowed down by Ice!")
            player.speed_boost = 0.5  # Reduce speed boost to 50%
            player.slow_until = current_time + 2000  # 2 seconds

        return 0