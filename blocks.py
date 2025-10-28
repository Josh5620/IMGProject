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

    def update(self):
        pass
    
    def draw(self, surface):
        if self.rect.x > -self.rect.width and self.rect.x < surface.get_width():
            surface.blit(self.image, self.rect.topleft)

    def collideHurt(self, player):
        return 0
    
    def get_rect(self):
        return self.rect
    
class AnimatedTrap(block):
    def __init__(self, x, y, spritesheet_path, frame_width, frame_height, damage=1, cooldown=1000):

        super().__init__(x, y)
        spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
        self.frames = []
        for i in range(spritesheet.get_width() // frame_width):
            frame = spritesheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height))
            self.frames.append(frame)

        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect(midtop=(x, y))

        hitbox_width = self.rect.width * 0.5
        hitbox_height = self.rect.height * 0.5
        self.hitbox = pygame.Rect(0, 0, hitbox_width, hitbox_height)
        self.hitbox.center = self.rect.center

        self.animation_speed = 50 # milliseconds per frame
        self.last_update = pygame.time.get_ticks()

        self.damage = damage
        self.cooldown_duration = cooldown
        self.last_hit_time = 0

    def update_animation(self):
        now = pygame.time.get_ticks()
        if now - self.last_update > self.animation_speed:
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
    
    def check_collision(self, player):
        now = pygame.time.get_ticks()
        if self.rect.colliderect(player.rect):
            if now - self.last_hit_time > self.cooldown_duration:
                self.last_hit_time = now
                player.lives -= self.damage
                player.iFrame()

    def update(self, player):
        self.update_animation()
        self.check_collision(player)

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
    
