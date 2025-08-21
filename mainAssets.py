import pygame

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
    
    def move(self, dx, dy, obstacles=None):
        old_x, old_y = self.rect.x, self.rect.y
        
        
        self.rect.x += dx
        if obstacles and self.check_collision(obstacles):
            self.rect.x = old_x

        
        self.rect.y += dy
        if obstacles and self.check_collision(obstacles):
            self.rect.y = old_y

    def jump(self):
        if not self.jumping:
            print("Jumping")
            self.jumping = True
            self.y_velocity = self.jump_height
            print("JUmping at velocity of:" + str(self.y_velocity))

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
            self.rect.y -= self.y_velocity
            self.y_velocity -= self.y_gravity
            
            if self.y_velocity < -self.jump_height:
                jumping = False
                self.y_velocity = self.jump_height
        self.check_collision(obstacles)
        self.applyGrav()
        
        

    def check_collision(self, obstacles):    
        for block in obstacles:
            if self.rect.colliderect(block.get_rect()):
                if self.y_velocity > 0:
                    print("1")
                    self.rect.bottom = block.get_rect().top
                    self.jumping = False
                    self.on_ground = True
                    self.y_velocity = 0
                    self.image = pygame.image.load("mc.png")

    def applyGrav(self):
        if not self.on_ground:
            
            self.y_velocity += self.y_gravity
            self.rect.y += self.y_velocity
            print(self.y_velocity)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
    def get_position(self):
        return self.rect.topleft
    
    
            


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
    
    def get_rect(self):
        return self.rect

    
