import pygame
import math
from entities import build_state_animations_from_manifest
import time

WARRIOR_ANIM = {
    "run":       {"file": "assets/Level1/Warrior/Run.png",       "frame_width": 40},
    "attack": {"file": "assets/Level1/Warrior/Attack.png", "frame_width": 40}
}

ARCHER_ANIM = {
    "run":       {"file": "assets/Level1/Archer/Run.png",       "frame_width": 64},
    "attack": {"file": "assets/Level1/Archer/Attack.png", "frame_width": 64}
}


class Level1Enemy:
    
    def __init__(self, x, y, width=48, height=48, anim_manifest : dict = None):
        
        
        self.rect        = pygame.Rect(x, y, width, height)
        self.original_x  = x
        self.original_y  = y
        self.name        = "Enemy"

        self.alive       = True
        self.visible     = True
        self.image       = pygame.Surface((width, height))
        self.image.fill((255, 100, 100))

        self.speed       = 2.0
        self.direction   = 1
        self.facing_right = (self.direction > 0)
        self.y_velocity  = 0
        self.gravity     = 0.5
        self.on_ground   = False
        self.isIdle = False
        self.player_world_rect = None

        self.ai_state    = "idle"
        self.ai_timer    = 0

        self.patrol_start = x
        self.patrol_range = 150

        self.sight_range  = 200
        self.sight_width  = 80
        self.sight_color = (255, 0, 0, 100)
        self.player_spotted = False

        self.debug_mode = True

        self.max_hp = 100
        self.current_hp = self.max_hp

        self.attack_range     = pygame.Vector2(40, 40)
        self.player_in_attack = False
        self.attack_cooldown = 3000  
        self.last_attack_time = 0
        self.attack_flash_time = 1500  
        self.attack_flash_until = 0
        
        self.exclamation_img = pygame.image.load("assets/exclamation.png").convert_alpha()
        self.exclamation_img = pygame.transform.scale(self.exclamation_img, (16, 24))
        self.anims = build_state_animations_from_manifest(anim_manifest or {})
        self.anim_tick = 0
        self.anim_speed = 10
        self.attack_anim_timer = 0
        self.attack_anim_elapsed = 0
        self.attack_anim_duration = 0
        self.current_state = "run" if "run" in self.anims else None
        if "run" in self.anims and self.anims["run"]:
            self.image = self.anims["run"][0]
        self._last_x = self.rect.x
        if not hasattr(self, "facing_right"):
            self.facing_right = True
            
            
    def _anim_index(self, frames):
        if not frames:
            return 0
        return (self.anim_tick // self.anim_speed) % len(frames)

    def update_anim_timers(self, dt):
        if self.attack_anim_timer > 0:
            self.attack_anim_timer = max(0, self.attack_anim_timer - dt)
            self.attack_anim_elapsed = min(self.attack_anim_duration, self.attack_anim_elapsed + dt)


    def start_attack_anim(self, duration_ms=400):
        self.attack_anim_duration = max(1, duration_ms)
        self.attack_anim_timer = duration_ms
        self.attack_anim_elapsed = 0

    def update_animation(self):
        self.anim_tick = (self.anim_tick + 1) % 10000000

        # Attack animation (non-looping)
        if self.attack_anim_timer > 0 and "attack" in self.anims and self.anims["attack"]:
            state = "attack"
            frames = self.anims["attack"]
            if frames:
                progress = self.attack_anim_elapsed / self.attack_anim_duration
                idx = min(int(progress * len(frames)), len(frames) - 1)
            else:
                idx = 0

        else:
            state = "run" if "run" in self.anims else None
            frames = self.anims.get("run", [])
            if state and frames:
                if self.rect.x == self._last_x:
                    idx = 0  
                else:
                    idx = (self.anim_tick // self.anim_speed) % len(frames)
            else:
                idx = 0

        if state and frames:
            img = frames[idx]
            self.image = img if self.facing_right else pygame.transform.flip(img, True, False)
            self.current_state = state

        self._last_x = self.rect.x


        
    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        if not self.alive:
            return
        
        # Set scroll offset first
        self.scroll_offset = scroll_offset
        
        self.player_world_rect = player.rect.copy()
        self.player_world_rect.x += self.scroll_offset

        self.update_timers(dt)
        if obstacles is None:
            obstacles = []
        
        if self.is_player_in_sight(player):
            if not self.player_spotted:
                self.on_player_spotted(player)
                self.player_spotted = True
        else:
            self.player_spotted = False
        
        self.update_ai(player, obstacles, dt)
        self.apply_physics(obstacles)
        self.update_attack_detection(player)
        if self.player_in_attack:
            self.attack(player)
        self.update_anim_timers(dt)
        self.update_animation()
  
    def update_timers(self, dt):
        self.ai_timer += dt
            
    def update_ai(self, player, obstacles, dt):

        if self.isIdle:
            return
        
        if self.player_spotted and player:
            # Face the player
            if player.rect.centerx + self.scroll_offset > self.rect.centerx:
                self.facing_right = True
                self.direction = 1
            else:
                self.facing_right = False
                self.direction = -1
            return  
            
        if self.ai_timer > 120:
            self.direction *= -1
            self.facing_right = (self.direction > 0)
            self.ai_timer = 0
            
    def apply_physics(self, obstacles):
        if not self.on_ground:
            self.y_velocity += self.gravity
        if self.y_velocity != 0:
            self.rect.y += self.y_velocity
            self.check_vertical_collision(obstacles)
            
    def move_horizontal(self, dx, obstacles):
        if dx == 0:
            return
            
        old_x = self.rect.x
        
        if self.on_ground and not self.should_ignore_edges():
            ground_ahead = self.check_ground_ahead(dx, obstacles)
            
            if not ground_ahead:
                self.handle_edge_detection()
                return
        
        self.rect.x += dx
        
        if self.check_horizontal_collision(obstacles):
            self.rect.x = old_x
            self.handle_wall_collision()
            
    def check_ground_ahead(self, dx, obstacles):

        if dx > 0: 
            check_x = self.rect.right + 5  # Look ahead a bit more
        else:  # Moving left
            check_x = self.rect.left - 5   # Look ahead a bit more
            
        # Create ground check rectangle below the projected position
        ground_check = pygame.Rect(check_x - 5, self.rect.bottom, 32, 20)  
        
        self.debug_ground_check = ground_check
        
        ground_found = False
        for obstacle in obstacles:
            # Convert obstacle rect back to world space for collision testing
            world_obstacle_rect = obstacle.get_rect().copy()
            world_obstacle_rect.x = obstacle.original_x
            world_obstacle_rect.y = obstacle.original_y
            
            if ground_check.colliderect(world_obstacle_rect):
                ground_found = True
                break
        
        return ground_found
        
    def should_ignore_edges(self):
        return False  
        
    def handle_edge_detection(self):
        if not hasattr(self, 'last_direction_change'):
            self.last_direction_change = 0
        
        current_time = pygame.time.get_ticks()
        if current_time - self.last_direction_change > 500:  # 500ms delay
            self.direction *= -1
            self.facing_right = (self.direction > 0)
            self.last_direction_change = current_time
        
    def handle_wall_collision(self):
        self.direction *= -1
        self.facing_right = (self.direction > 0)
        
    def check_horizontal_collision(self, obstacles):
        for obstacle in obstacles:
            # Convert obstacle rect back to world space for collision testing
            world_obstacle_rect = obstacle.get_rect().copy()
            world_obstacle_rect.x = obstacle.original_x 
            world_obstacle_rect.y = obstacle.original_y
            
            if self.rect.colliderect(world_obstacle_rect):
                return True
        return False
        
    def check_vertical_collision(self, obstacles):
        for obstacle in obstacles:
            # Convert obstacle rect back to world space for collision testing
            world_obstacle_rect = obstacle.get_rect().copy()
            world_obstacle_rect.x = obstacle.original_x
            world_obstacle_rect.y = obstacle.original_y
            
            if self.rect.colliderect(world_obstacle_rect):
                if self.y_velocity > 0:
                    self.rect.bottom = world_obstacle_rect.top
                    self.y_velocity = 0
                    self.on_ground = True
                elif self.y_velocity < 0:
                    self.rect.top = world_obstacle_rect.bottom
                    self.y_velocity = 0
                return True
        if self.on_ground:
            ground_check = pygame.Rect(self.rect.x, self.rect.y + 1, self.rect.width, self.rect.height)
            still_on_ground = False
            for obstacle in obstacles:
                # Convert obstacle rect back to world space for ground check
                world_obstacle_rect = obstacle.get_rect().copy()
                world_obstacle_rect.x = obstacle.original_x
                world_obstacle_rect.y = obstacle.original_y
                
                if ground_check.colliderect(world_obstacle_rect):
                    still_on_ground = True
                    break
            if not still_on_ground:
                self.on_ground = False
        return False
        
    def get_sight_rect(self):
        if self.facing_right:
            sight_x = self.rect.centerx
            sight_y = self.rect.centery - (self.sight_width // 2)
            return pygame.Rect(sight_x, sight_y, self.sight_range, self.sight_width)
        else:
            sight_x = self.rect.centerx - self.sight_range
            sight_y = self.rect.centery - (self.sight_width // 2)
            return pygame.Rect(sight_x, sight_y, self.sight_range, self.sight_width)
    
    def draw_line_of_sight(self, surface):
        if not self.debug_mode:
            return
        sight_rect = self.get_sight_rect()
        
        # Convert to screen space for drawing
        screen_sight_rect = sight_rect.copy()
        screen_sight_rect.x -= self.scroll_offset
        
        temp_surface = pygame.Surface((screen_sight_rect.width, screen_sight_rect.height), pygame.SRCALPHA)
        temp_surface.fill(self.sight_color)
        surface.blit(temp_surface, (screen_sight_rect.x, screen_sight_rect.y))
    
    def is_player_in_sight(self, player):
        if not player:
            return False
        sight_rect = self.get_sight_rect()

        return sight_rect.colliderect(self.player_world_rect)

    def on_player_spotted(self, player):
        print("Enemy has spotted the player!")
        pass
        
    def draw(self, surface):
        if not self.alive or not self.visible:
            return
        
        # Convert enemy position to screen coordinates
        screen_x = self.rect.x - self.scroll_offset
        screen_y = self.rect.y
        
        self.draw_line_of_sight(surface)
        surface.blit(self.image, (screen_x, screen_y))

        if self.player_spotted:
            bounce = abs(math.sin(pygame.time.get_ticks() * 0.01)) * 3
            exclamation_x = screen_x + self.rect.width // 2 - self.exclamation_img.get_width() // 2
            exclamation_y = screen_y - self.exclamation_img.get_height() - 5 - bounce
            surface.blit(self.exclamation_img, (exclamation_x, exclamation_y))
        

        if self.debug_mode and hasattr(self, 'debug_ground_check') and hasattr(self, 'scroll_offset'):

            screen_ground_check = self.debug_ground_check.copy()
            screen_ground_check.x -= self.scroll_offset
            

            pygame.draw.rect(surface, (0, 255, 0), screen_ground_check, 2)
        

        if self.debug_mode:
            self.draw_debug_ranges(surface, self.scroll_offset)
                         
    def draw_debug_ranges(self, surface, scroll_offset=0):
        attack_rect = self.get_attack_rect().move(-scroll_offset, 0)
        pygame.draw.rect(surface, (255, 100, 0), attack_rect, 1)
    
    def get_rect(self):
        return self.rect
    
    def get_attack_rect(self):
        if self.facing_right:
            x = self.rect.right
        else:
            x = self.rect.left - self.attack_range.x
        y = self.rect.centery - self.attack_range.y / 2
        return pygame.Rect(x, y, self.attack_range.x, self.attack_range.y)

    def update_attack_detection(self, player):
        attack_rect = self.get_attack_rect()
        self.player_in_attack = attack_rect.colliderect(self.player_world_rect)
        
    def attack(self, player):
        now = pygame.time.get_ticks()
        if now - self.last_attack_time >= self.attack_cooldown:
            if self.player_in_attack:
                self.last_attack_time = now
                
                self.on_attack(player)  # call simple attack event

    def on_attack(self, player):
        print(f"{self.name} attacks player!")
        pass

    def take_damage(self, damage):
        self.current_hp -= damage
        print(f"{self.name} took {damage} damage! HP: {self.current_hp}/{self.max_hp}")
        
        if self.current_hp <= 0:
            self.alive = False
            print(f"{self.name} has been defeated!")




class Archer(Level1Enemy):
    
    def __init__(self, x, y, width=48, height=48):
        super().__init__(x, y, width, height, anim_manifest=ARCHER_ANIM)

        self.sight_range = 250
        self.sight_width = 60
        self.patrol_range = 400
        self.patrol_center = x
        self.patrol_left_bound = x - self.patrol_range // 2
        self.patrol_right_bound = x + self.patrol_range // 2
        self.speed = 1.2
        self.name = "Archer"
        self.pending_arrow = False
        self.arrow_spawn_time = 0
        self.debug_mode = False


        self.shoot_cooldown = 2000  
        self.last_shot_time = 0
        self.arrow_speed = 6
        self.isIdle = False
        
        # Shooting delay after spotting player
        self.shoot_delay = 2000  
        self.first_spotted_time = 0
        self.player_spotted_recently = False
        
        # Exclamation indicator for player detection
        self.player_detected = False
        self.detection_timer = 0.0
        self.detection_duration = 60  # Frames to show exclamation
        try:
            self.exclamation_img = pygame.image.load("assets/exclamation.png").convert_alpha()
            self.exclamation_img = pygame.transform.scale(self.exclamation_img, (24, 24))
        except:
            self.exclamation_img = None
        
    def can_shoot(self):
        current_time = pygame.time.get_ticks()
        # Check if enough time has passed since last shot
        if current_time - self.last_shot_time < self.shoot_cooldown:
            return False
        if self.player_spotted_recently and current_time - self.first_spotted_time < self.shoot_delay:
            return False
        return True

    def on_attack(self, player):
        spawn_x = self.rect.right if self.facing_right else self.rect.left - 16
        spawn_y = self.rect.centery - 4
        
        self.start_attack_anim(200)
        arrow = Arrow(spawn_x, spawn_y, dir_right=self.facing_right, speed=self.arrow_speed)

        if hasattr(self, "level") and hasattr(self.level, "arrows"):
            self.level.arrows.append(arrow)
        elif hasattr(self, "arrows"):
            self.arrows.append(arrow)

        self.last_shot_time = pygame.time.get_ticks()  # cooldown start
        print(f"{self.name} shoots an arrow!")


    def update_ai(self, player, obstacles, dt):
        # Update detection timer
        if self.detection_timer > 0:
            self.detection_timer -= dt
        
        if getattr(self, "isIdle", False):
            return

        if player and self.is_player_in_sight(player):
            distance_to_player = abs(self.player_world_rect.centerx - self.rect.centerx)
            

            if distance_to_player < 60: 
                return 
            if not self.player_spotted_recently:
                self.player_spotted_recently = True
                self.first_spotted_time = pygame.time.get_ticks()
                
                self.player_detected = True
                self.detection_timer = self.detection_duration
                print(f"{self.name} spotted player! Preparing to shoot...")
                self.start_attack_anim(200)
            
            if self.can_shoot():
                
                self.on_attack(player)
            if player.rect.centerx + self.scroll_offset > self.rect.centerx:
                self.facing_right = True
                self.direction = 1
            else:
                self.facing_right = False
                self.direction = -1
            return
        else:
            # Reset spotted flag when player is no longer in sight
            self.player_spotted_recently = False
            self.player_detected = False

        # normal patrol
        if self.on_ground:
            movement = self.direction * self.speed
            if self.direction > 0 and self.rect.x >= self.patrol_right_bound:
                self.direction *= -1
                self.facing_right = (self.direction > 0)
            elif self.direction < 0 and self.rect.x <= self.patrol_left_bound:
                self.direction *= -1
                self.facing_right = (self.direction > 0)
            self.move_horizontal(movement, obstacles)

class Warrior(Level1Enemy):
    
    
    def __init__(self, x, y, width=48, height=48):
        super().__init__(x, y, width, height, anim_manifest=WARRIOR_ANIM)
        
        self.sight_range = 150
        self.sight_width = 100
        self.patrol_range = 100
        self.speed = 1
        self.patrol_center = x
        self.patrol_left_bound = x - self.patrol_range // 2
        self.patrol_right_bound = x + self.patrol_range // 2
        self.isIdle = False
        self.name = "Warrior"
        self.chase_speed = 1.5
        self.chase_range = 300
        self.start_x = x
        self.debug_mode = False
        
        # Exclamation indicator for player detection
        self.player_detected = False
        self.detection_timer = 0.0
        self.detection_duration = 60  # Frames to show exclamation
        try:
            self.exclamation_img = pygame.image.load("assets/exclamation.png").convert_alpha()
            self.exclamation_img = pygame.transform.scale(self.exclamation_img, (24, 24))
        except:
            self.exclamation_img = None
        
    def update_ai(self, player, obstacles, dt): 
        # Update detection timer
        if self.detection_timer > 0:
            self.detection_timer -= dt
        
        if self.isIdle:
            return
        
        if self.player_spotted and player:
            # Trigger exclamation when first spotting player
            if not self.player_detected:
                self.player_detected = True
                self.detection_timer = self.detection_duration
                
            distance_from_start = abs(self.rect.x - self.start_x)
            distance_to_player = abs(self.player_world_rect.centerx - self.rect.centerx)


            if distance_to_player < 60: 
                return 
            
            if distance_from_start < self.chase_range:
                if player.rect.centerx + self.scroll_offset > self.rect.centerx:
                    self.facing_right = True
                    self.direction = 1
                    movement = self.chase_speed
                else:
                    self.facing_right = False
                    self.direction = -1
                    movement = -self.chase_speed
                
                self.move_horizontal(movement, obstacles)
            else:
                pass
            return
        else:
            # Reset exclamation when player is no longer spotted
            self.player_detected = False
            
        if self.on_ground:
            movement = self.direction * self.speed
            
            if self.direction > 0 and self.rect.x >= self.patrol_right_bound:
                self.direction *= -1
                self.facing_right = (self.direction > 0)
            elif self.direction < 0 and self.rect.x <= self.patrol_left_bound:
                self.direction *= -1
                self.facing_right = (self.direction > 0)
            
            self.move_horizontal(movement, obstacles)
        
    def on_player_spotted(self, player):
        print("Warrior sees player! Starting the chase!")
    
    def on_attack(self, player):
        self.start_attack_anim(30)
        hit_width, hit_height = 60, 40  # adjust to taste
        if self.facing_right:
            x = self.rect.right
        else:
            x = self.rect.left - hit_width
        y = self.rect.centery - hit_height // 2

        hit_box = pygame.Rect(x, y, hit_width, hit_height)

        
        surface = pygame.display.get_surface()
        if surface:

            screen_hit_box = hit_box.copy()
            screen_hit_box.x -= self.scroll_offset
            
            green_surf = pygame.Surface((screen_hit_box.width, screen_hit_box.height), pygame.SRCALPHA)
            green_surf.fill((0, 255, 0, 120))  
            surface.blit(green_surf, screen_hit_box.topleft)
            pygame.display.update(screen_hit_box)


        if player and hit_box.colliderect(self.player_world_rect):
            print("Warrior hit the player!")
            player.take_damage(1)
        else:
            print("Warrior missed!")

class Arrow:
    def __init__(self, x, y, dir_right: bool, speed=8, gravity=0.0, ttl_ms=4000, size=(18, 4)):
        w, h = size
        self.rect = pygame.Rect(int(x), int(y), w, h)  # world space
        self.vx = speed if dir_right else -speed
        self.vy = 0.0
        self.alive = True
        self.spawn_ms = pygame.time.get_ticks()
        self.ttl_ms = ttl_ms
        self.image = pygame.image.load("assets/arrow.png").convert_alpha()
        
        if not dir_right:
            self.image = pygame.transform.flip(self.image, True,False)

    def update(self, obstacles):
        if not self.alive:
            return
        # ttl
        if pygame.time.get_ticks() - self.spawn_ms > self.ttl_ms:
            self.alive = False
            return

        # physics
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        for o in obstacles:
            r = o.get_rect().copy()
            r.x = o.original_x
            r.y = o.original_y
            if self.rect.colliderect(r):
                self.alive = False
                return

    def collide(self, player, scroll_offset=0):
        if not self.alive:
            return False
        # convert player rect to world space
        pw = player.rect.copy()
        pw.x += scroll_offset
        if self.rect.colliderect(pw):
            if hasattr(player, "lives"):
                player.take_damage(1)
            self.alive = False
            return True
        return False

    def draw(self, surface, scroll_offset=0):
        if not self.alive:
            return
        surface.blit(self.image, (self.rect.x - scroll_offset, self.rect.y))

    def get_rect(self):
        return self.rect
    
class BreakableBlock(Level1Enemy): # <-- Inherit from Enemy
    def __init__(self, x, y, image):
        
        super().__init__(x, y) 
        self.debug_mode = False
        self.isIdle = True 
        self.max_hp = 40
        self.current_hp = self.max_hp
        self.image = image
        # Disable physics
        self.gravity = 0
        self.y_velocity = 0
        
    def should_ignore_edges(self):
        return True  
        
    def apply_physics(self, obstacles):
        pass
        
    def move_horizontal(self, dx, obstacles):
        pass
        
    def check_horizontal_collision(self, obstacles):
        return False
        
    def check_vertical_collision(self, obstacles):
        return False
        
    def on_attack(self, player):
        pass

    def on_player_spotted(self, player):
        pass

    def is_player_in_sight(self, player):
        return False

class Mushroom(BreakableBlock):
    def __init__(self, x, y, image):
        super().__init__(x, y, image)
        self.name = "Mushroom"
        self.debug_mode = False
        self.isIdle = True 
        self.max_hp = 1
        self.current_hp = self.max_hp
        self.image = image
        self.gravity = 0
        self.y_velocity = 0
        self.on_ground = True
        
        self.is_collectible = True
        self.solid = False
        
    def get_rect(self):
        return pygame.Rect(self.rect.x, self.rect.y, 0, 0)
        
    def check_player_collision(self, player, scroll_offset):
        if not self.alive:
            return False
            
        player_world_rect = player.rect.copy()
        player_world_rect.x += scroll_offset
        
        if self.rect.colliderect(player_world_rect):
            return True
        return False
        
    def collect(self):
        self.alive = False
        
    def on_attack(self, player):
        pass
    