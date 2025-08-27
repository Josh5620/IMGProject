import pygame
import random

def rescaleObject(object, scale_factor):
    scaledObject = pygame.transform.scale_by(object, scale_factor)
    return scaledObject
class mainCharacter:
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = pygame.image.load("mc.png")
        self.jumpimage = pygame.image.load("mcjump.png")
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        
        # Instance variables instead of class variables
        self.y_gravity = 0.5
        self.jump_height = 10
        self.y_velocity = 0
        self.jumping = False
        self.on_ground = False
        self.visible = True
        self.invulnerable = False
        self.lives = 3 
    
    def move(self, dx, dy, obstacles=None):
        old_x, old_y = self.rect.x, self.rect.y
        
        # Handle horizontal movement
        if dx != 0:
            self.rect.x += dx
            if obstacles and self.check_horizontal_collision(obstacles):
                self.rect.x = old_x
        # Handle vertical movement
        if dy != 0:
            self.rect.y += dy
            if obstacles and self.check_vertical_collision(obstacles):
                self.rect.y = old_y

    def check_horizontal_collision(self, obstacles):
        for block in obstacles:
            if isinstance(block, Spikes):
                block.collideHurt(self)
            if self.rect.colliderect(block.get_rect()):
                
                return True
        return False
    
    def check_vertical_collision(self, obstacles):
        for block in obstacles:
            if isinstance(block, Spikes):
                block.collideHurt(self)
            if self.rect.colliderect(block.get_rect()):
                
                return True
        return False

    def jump(self):
        #if not self.jumping and self.on_ground: I turn off 
        self.jumping = True
        self.on_ground = False
        self.y_velocity = -self.jump_height  
        
    def update(self, keys, obstacles):
        if keys[pygame.K_LEFT]:
            self.move(-5, 0, obstacles)
        if keys[pygame.K_RIGHT]:
            self.move(5, 0, obstacles)
        if keys[pygame.K_UP]:
            self.jump()
        if keys[pygame.K_DOWN]:
            self.move(0, 5, obstacles)
        
        if self.jumping:            
            self.image = self.jumpimage
        
        # Apply physics (gravity and movement)
        self.applyGrav(obstacles)
        
    def check_collision(self, obstacles):    
        for block in obstacles:
            if isinstance(block, Spikes):
                block.collideHurt(self)
            if self.rect.colliderect(block.get_rect()):
                # Check if falling down and hitting top of block (landing)
                if self.y_velocity > 0:
                    # print("Touched Ground")
                    self.rect.bottom = block.get_rect().top
                    self.jumping = False
                    self.on_ground = True
                    self.y_velocity = 0
                    self.image = pygame.image.load("mc.png")
                    return True
                
                # Check if moving up and hitting bottom of block (head bump)
                elif self.y_velocity < 0:
                    print("Hit ceiling")
                    self.rect.top = block.get_rect().bottom
                    self.y_velocity = 0
                    return True
        
        # If no collision detected and player was on ground, they're now falling
        if self.on_ground:
            # Check if player is still touching ground
            ground_check = pygame.Rect(self.rect.x, self.rect.y + 1, self.rect.width, self.rect.height)
            still_on_ground = False
            for block in obstacles:
                if ground_check.colliderect(block.get_rect()):
                    still_on_ground = True
                    break
            
            if not still_on_ground:
                print("Started falling")
                self.on_ground = False
        
        return False

    def applyGrav(self, obstacles):
        # Apply gravity to velocity
        if not self.check_vertical_collision(obstacles):
            self.on_ground = False
        if not self.on_ground:
            self.y_velocity += self.y_gravity
        
        # Apply velocity to position
        if self.y_velocity != 0:
            self.rect.y += self.y_velocity
            self.check_collision(obstacles)
            
    def iFrame(self):
        print("You've been hit!!")
        self.invulnerable = True
        self.invulnerable_start = pygame.time.get_ticks()

    def draw(self, surface):
        # Handle invulnerability timing
        if self.invulnerable:
            now = pygame.time.get_ticks()
            if now - self.invulnerable_start >= 2000:  # CHANGE INVI TIMING HERE
                self.invulnerable = False
            
            blink_interval = 100
            time_since_start = now - self.invulnerable_start
            should_show = (time_since_start // blink_interval) % 2 == 0
            
            if should_show and self.visible:
                surface.blit(self.image, self.rect)
        else:
            if self.visible:
                surface.blit(self.image, self.rect)
            
    def get_position(self):
        return self.rect.topleft
    
class block:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.image = rescaleObject(pygame.image.load("block.png"), 0.1)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def collideHurt(self, player):
        return 0
    
    def get_rect(self):
        return self.rect

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
        self.image = pygame.image.load("coin.png")
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

class Spikes(block):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = rescaleObject(pygame.image.load("spike.png"),1 )
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
        surface.blit(self.image, self.rect)
class Meat(pickUps):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.image = rescaleObject(pygame.image.load("meat.png"), 1)
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