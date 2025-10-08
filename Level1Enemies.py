import pygame
import math
from weapons.projectiles import ProjectileManager, EnemyProjectile, ChargedProjectile


class Level1Enemy:
    
    def __init__(self, x, y, width=48, height=48):
        # Main
        self.rect        = pygame.Rect(x, y, width, height)
        self.original_x  = x
        self.original_y  = y
        self.name        = "Enemy"

        # Lifecycle and visibility
        self.alive       = True
        self.visible     = True
        self.image       = pygame.Surface((width, height))
        self.image.fill((255, 100, 100))

        # Movement and physics
        self.speed       = 2.0
        self.direction   = 1
        self.facing_right = (self.direction > 0)
        self.y_velocity  = 0
        self.gravity     = 0.5
        self.on_ground   = False
        self.isIdle = False
        self.player_world_rect = None

        # Simple AI state
        self.ai_state    = "idle"
        self.ai_timer    = 0

        # Patrol configuration
        self.patrol_start = x
        self.patrol_range = 150

        # Legacy sight cone settings
        self.sight_range  = 200
        self.sight_width  = 80
        self.sight_color = (255, 0, 0, 100)
        self.player_spotted = False

        # Debug
        self.debug_mode = True  # set True to show debug visuals

        # Health system
        self.max_hp = 100
        self.current_hp = self.max_hp

        # Attack setup in front of the enemy
        self.attack_range     = pygame.Vector2(40, 40)   # attack box size 
        self.player_in_attack = False
        self.attack_cooldown = 1000  
        self.last_attack_time = 0
        self.attack_flash_time = 1500  
        self.attack_flash_until = 0



        
    def update(self, player, dt=1.0, obstacles=None, scroll_offset=0):
        if not self.alive:
            return
        
        # Set scroll offset first
        self.scroll_offset = scroll_offset
        
        # Convert player from screen coordinates to world coordinates
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

        if self.debug_mode and self.player_spotted:
            purple_rect = pygame.Rect(screen_x + self.rect.width//2 - 8, screen_y - 20, 16, 16)
            pygame.draw.rect(surface, (128, 0, 128), purple_rect)  # Purple square
        

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
        super().__init__(x, y, width, height)
        self.image.fill((0, 0, 255))
        self.sight_range = 250
        self.sight_width = 60
        self.patrol_range = 400
        self.patrol_center = x
        self.patrol_left_bound = x - self.patrol_range // 2
        self.patrol_right_bound = x + self.patrol_range // 2
        self.name = "Archer"

        # shooting setup
        self.shoot_cooldown = 1000  # 1 second between shots
        self.last_shot_time = 0
        self.arrow_speed = 6
        self.isIdle = False
        
        # Shooting delay after spotting player
        self.shoot_delay = 1000  # 1 second delay after first spotting player
        self.first_spotted_time = 0
        self.player_spotted_recently = False
        
    def can_shoot(self):
        current_time = pygame.time.get_ticks()
        # Check if enough time has passed since last shot
        if current_time - self.last_shot_time < self.shoot_cooldown:
            return False
        # Check if delay after first spotting player has elapsed
        if self.player_spotted_recently and current_time - self.first_spotted_time < self.shoot_delay:
            return False
        return True

    def on_attack(self, player):
        spawn_x = self.rect.right if self.facing_right else self.rect.left - 16
        spawn_y = self.rect.centery - 4

        arrow = Arrow(spawn_x, spawn_y, dir_right=self.facing_right, speed=self.arrow_speed)

        if hasattr(self, "level") and hasattr(self.level, "arrows"):
            self.level.arrows.append(arrow)
        elif hasattr(self, "arrows"):
            self.arrows.append(arrow)

        self.last_shot_time = pygame.time.get_ticks()  # cooldown start
        print(f"{self.name} shoots an arrow!")


    def update_ai(self, player, obstacles, dt):
        if getattr(self, "isIdle", False):
            return

        if player and self.is_player_in_sight(player):
            # Track when player is first spotted
            if not self.player_spotted_recently:
                self.player_spotted_recently = True
                self.first_spotted_time = pygame.time.get_ticks()
                print(f"{self.name} spotted player! Preparing to shoot...")
            
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
        super().__init__(x, y, width, height)
        self.image.fill((255, 0, 0))
        self.sight_range = 150
        self.sight_width = 100
        self.patrol_range = 100
        self.speed = 1.5
        self.patrol_center = x
        self.patrol_left_bound = x - self.patrol_range // 2
        self.patrol_right_bound = x + self.patrol_range // 2
        self.isIdle = True
        self.name = "Warrior"
        
    def update_ai(self, player, obstacles, dt):
        # If idle, stay at starting position and don't patrol
        if self.isIdle:
            return
        
        # If player is spotted, stop moving and look at player
        if self.player_spotted and player:
            # Face the player
            if player.rect.centerx + self.scroll_offset > self.rect.centerx:
                self.facing_right = True
                self.direction = 1
            else:
                self.facing_right = False
                self.direction = -1
            return  # Don't move while player is in sight
        
        if self.on_ground:
            movement = self.direction * self.speed
            
            if self.direction > 0 and self.rect.x >= self.patrol_right_bound:
                self.direction *= -1
                self.facing_right = (self.direction > 0)
                movement = self.direction * self.speed
            elif self.direction < 0 and self.rect.x <= self.patrol_left_bound:
                self.direction *= -1
                self.facing_right = (self.direction > 0)
                movement = self.direction * self.speed
            
            self.move_horizontal(movement, obstacles)
        
    def on_player_spotted(self, player):
        print("Warrior sees player!")
    
    def on_attack(self, player):

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
        self.image = pygame.Surface((w, h))
        self.image.fill((220, 200, 40))

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

    