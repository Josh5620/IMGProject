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
    
    def check_collision(self, player, scroll_offset=0):
        """Check collision with player, accounting for scroll offset like Level 1 enemies"""
        now = pygame.time.get_ticks()
        
        # Convert player rect to world space
        player_world_rect = player.rect.copy()
        player_world_rect.x += scroll_offset
        
        # Check collision using world space coordinates
        if self.rect.colliderect(player_world_rect):
            if now - self.last_hit_time > self.cooldown_duration:
                self.last_hit_time = now
                player.lives -= self.damage
                player.iFrame()

    def update(self, player, scroll_offset=0):
        self.update_animation()
        self.check_collision(player, scroll_offset)

class FrameBasedTrap(AnimatedTrap):
    """
    A trap that only damages the player during specific animation frames.
    Useful for lightning strikes, fire bursts, etc. where only certain frames are dangerous.
    """
    def __init__(self, x, y, spritesheet_path, frame_width, frame_height, 
                 damage=1, cooldown=1000, damage_frames=None, animation_speed=100):
        """
        Args:
            damage_frames: List of frame indices that deal damage. If None, all frames deal damage.
                          Example: [2, 3] means only frames 2 and 3 hurt the player
            animation_speed: Milliseconds per frame (default 100)
        """
        super().__init__(x, y, spritesheet_path, frame_width, frame_height, damage, cooldown)
        self.damage_frames = damage_frames if damage_frames is not None else list(range(len(self.frames)))
        self.animation_speed = animation_speed
        
    def check_collision(self, player, scroll_offset=0):
        """Only check collision if current frame is a damage frame"""
        # Only deal damage if we're on a damage frame
        if self.current_frame not in self.damage_frames:
            return
            
        now = pygame.time.get_ticks()
        
        # Convert player rect to world space
        player_world_rect = player.rect.copy()
        player_world_rect.x += scroll_offset
        
        # Check collision using world space coordinates
        if self.rect.colliderect(player_world_rect):
            if now - self.last_hit_time > self.cooldown_duration:
                self.last_hit_time = now
                player.lives -= self.damage
                player.iFrame()

class LightningTrap(FrameBasedTrap):
    """Lightning trap that only damages on the strike frame"""
    def __init__(self, x, y, damage=1, cooldown=2000):
        # Lightning sprite: 960x96 = 10 frames at 96x96 each
        # The actual lightning strike happens in the middle frames
        super().__init__(
            x, y, 
            'assets/Level2/Traps/LightningTrap.png',
            frame_width=96,
            frame_height=96,
            damage=damage,
            cooldown=cooldown,
            damage_frames=[4, 5, 6],  # Middle frames where lightning actually strikes
            animation_speed=200  # Slower animation - more time to walk through
        )

class FireTrap(FrameBasedTrap):
    """Fire trap that damages during the flame burst frames"""
    def __init__(self, x, y, damage=1, cooldown=1500):
        # Fire sprite: 384x64 = 6 frames at 64x64 each
        # Fire builds up then bursts
        super().__init__(
            x, y,
            'assets/Level2/Traps/FireTrap.png',
            frame_width=64,
            frame_height=64,
            damage=damage,
            cooldown=cooldown,
            damage_frames=[3, 4, 5],  # Later frames where fire is actively burning
            animation_speed=250  # Slower animation - more time to walk through
        )

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

class EndWithDifficulty(block):
    """End object with specific boss difficulty for Level 2"""
    def __init__(self, x, y, difficulty):
        super().__init__(x, y)
        self.solid = False
        self.difficulty = difficulty  # Store which difficulty this end triggers
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
    
    def collideHurt(self, player):
        if self.rect.colliderect(player.rect):
            print(f"You Win! Boss difficulty: {self.difficulty}")
            player.won = True
            # Store difficulty on player so Level2 can read it
            if hasattr(player, 'level') and player.level:
                player.level.boss_difficulty = self.difficulty
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
