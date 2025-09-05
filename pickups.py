import pygame
import random

def rescaleObject(object, scale_factor):
    scaledObject = pygame.transform.scale_by(object, scale_factor)
    return scaledObject

class pickUps:
    def __init__(self, x, y):
        self.image = None
        self.rect = None
        self.original_x = x
        self.original_y = y
        self.x = x
        self.y = y
        self.name = ""
        # CHANGE THIS IF THE SCREEN SIZE CHANGES
        self.screen_width = 960
        self.screen_height = 640
    
    def setName(self, name):
        self.name = name

    def update_position(self, scroll):
        if self.rect:
            self.rect.x = self.original_x - scroll
            self.rect.y = self.original_y

    def is_offscreen(self, surface, margin=100):
        if not self.rect:
            return False
        
        if self.rect.x + self.rect.width < -margin:
            return True
        
        if self.rect.x > surface.get_width() + margin:
            return True
            
        return False

    def draw(self, surface):
        if self.image and self.rect:
            if self.rect.x > -self.rect.width and self.rect.x < surface.get_width():
                surface.blit(self.image, self.rect.topleft)

    def is_colliding_with(self, player):
        if self.rect and self.rect.colliderect(player.rect):
            print("You have picked up a " + self.name + "!")
            return True
        return False

    def get_rect(self):
        return self.rect    

    def respawn(self, obstacles=None, scroll=0):
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            margin = 50
            buffer_ahead = 200
            
            visible_world_left = scroll
            visible_world_right = scroll + self.screen_width
            
            spawn_left = visible_world_left + margin
            spawn_right = visible_world_right + buffer_ahead - margin
            
            new_x = random.randint(int(spawn_left), int(spawn_right - self.rect.width))
            new_y = random.randint(margin, self.screen_height - margin - self.rect.height)
            
            temp_rect = pygame.Rect(new_x, new_y, self.rect.width, self.rect.height)
            
            collision_found = False
            if obstacles:
                for obstacle in obstacles:
                    obstacle_original_rect = pygame.Rect(obstacle.original_x, obstacle.original_y, 
                                                       obstacle.rect.width, obstacle.rect.height)
                    if temp_rect.colliderect(obstacle_original_rect):
                        collision_found = True
                        break
            
            if not collision_found:
                self.original_x = new_x
                self.original_y = new_y
                self.x = new_x
                self.y = new_y
                self.collected = False
                
                return
            
            attempts += 1
        
        print("Could not find safe respawn location, using default")
        default_x = scroll + self.screen_width // 2
        self.original_x = default_x
        self.original_y = self.screen_height // 2
        self.x = default_x
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
    
    def respawn(self, obstacles=None, scroll=0):
        super().respawn(obstacles, scroll)
        print(f"Coin respawned at ({self.x}, {self.y})")

class Meat(pickUps):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = rescaleObject(pygame.image.load("assets/meat.png"), 1)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.setName("Meat")
        self.collected = False

    def update(self, player):
        if not self.collected and self.is_colliding_with(player):
            self.collected = True
            return True
        return False
    
    def respawn(self, obstacles=None, scroll=0):
        super().respawn(obstacles, scroll)
        self.collected = False