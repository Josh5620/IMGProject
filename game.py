import pygame
import pytmx
from entities import mainCharacter
from Level1Enemies import Level1Enemy, Archer, Warrior
from blocks import block, Spikes, start, end, Ice
from pickups import Coin, Meat


class Game:
    def __init__(self, width=960, height=640):
        self.WIDTH = width
        self.HEIGHT = height
        self.scroll_threshold = width / 4
        self.screen = None
        self.clock = pygame.time.Clock()
        
        self.scroll = 0
        self.ground_scroll = 0
        self.player_prev_x = 0
        self.coin_count = 0
        
        self.bg_images = []
        self.bg_width = 0
        self.tmx_data = None
        self.obstacles = []
        self.start_position = (300, 300)
        
        self.font = pygame.font.Font(None, 36)
        self.heart = None
        
        self.player = None
        self.pickups = []
        self.enemies = []
        self.arrows = []
        self.doScroll = True
        
    def load_background(self, bg_folder, num_layers):
        self.bg_images = []
        for i in range(num_layers):
            bg_image = pygame.image.load(f'{bg_folder}/Layer_{i}.png').convert_alpha()
            bg_image = pygame.transform.scale(bg_image, (self.WIDTH, self.HEIGHT))
            self.bg_images.append(bg_image)
        self.bg_width = self.bg_images[0].get_width()
        
    def load_tilemap(self, tilemap_file):
        self.tmx_data = pytmx.util_pygame.load_pygame(tilemap_file)
        
    def load_ui_assets(self):
        heart = pygame.image.load('assets/heart.png').convert_alpha()
        self.heart = pygame.transform.scale_by(heart, 0.05)
        
    def reset_game(self):
        if self.player:
            self.player.lives = 500
            self.player.x = self.start_position[0]
            self.player.y = self.start_position[1]
            self.player.rect.x = self.start_position[0]
            self.player.rect.y = self.start_position[1]
            self.player.won = False
        self.scroll = 0
        self.ground_scroll = 0
        self.player_prev_x = self.start_position[0]
        self.coin_count = 0
        
    def draw_bg(self):
        start_bg_x = int(self.scroll // self.bg_width) - 1
        end_bg_x = int((self.scroll + self.WIDTH) // self.bg_width) + 2
        
        if self.doScroll:
            for x in range(start_bg_x, end_bg_x):
                speed = 1
                for i in self.bg_images:
                    bg_pos_x = (x * self.bg_width) - self.scroll * speed
                    if bg_pos_x > -self.bg_width and bg_pos_x < self.WIDTH:
                        self.screen.blit(i, (bg_pos_x, 0))
                    speed += 0.1
                
    def update_lives(self):
        if self.player and self.heart:
            for i in range(self.player.lives):
                self.screen.blit(self.heart, (10 + i * 30, 10))
                
    def handle_scrolling(self):
        if not self.player or not self.doScroll:
            return
            
        current_player_x = self.player.rect.x
        
        if current_player_x > (self.WIDTH - self.scroll_threshold):
            self.player.rect.x = self.WIDTH - self.scroll_threshold
            if self.player.scroll_speed > 0:
                self.scroll += self.player.scroll_speed
                self.ground_scroll += self.player.scroll_speed * 6
        elif current_player_x < self.scroll_threshold:
            if self.scroll == 0 and self.ground_scroll == 0:
                pass
            else:
                self.player.rect.x = self.scroll_threshold
                if self.player.scroll_speed < 0:
                    self.scroll += self.player.scroll_speed
                    self.ground_scroll += self.player.scroll_speed * 6
                    if self.scroll < 0:
                        self.scroll = 0
                    if self.ground_scroll < 0:
                        self.ground_scroll = 0
                        
    def draw_debug_info(self):
        fps = self.clock.get_fps()
        fps_text = self.font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
        self.screen.blit(fps_text, (self.WIDTH - 150, 10))
        
        bg_scroll_text = self.font.render(f"BG Scroll: {self.scroll:.1f}", True, (255, 255, 255))
        ground_scroll_text = self.font.render(f"Ground Scroll: {self.ground_scroll:.1f}", True, (255, 255, 255))
        self.screen.blit(bg_scroll_text, (self.WIDTH - 250, 50))
        self.screen.blit(ground_scroll_text, (self.WIDTH - 250, 90))
        
        pygame.draw.line(self.screen, (255, 0, 0), (self.scroll_threshold, 0), (self.scroll_threshold, self.HEIGHT))
        pygame.draw.line(self.screen, (255, 0, 0), (self.WIDTH - self.scroll_threshold, 0), (self.WIDTH - self.scroll_threshold, self.HEIGHT))
        
    def draw_tilemap(self):
        if not self.tmx_data:
            return
            
        TILE_SIZE = 32
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        tile_x = (x * TILE_SIZE) - self.ground_scroll
                        if tile_x > -TILE_SIZE and tile_x < self.WIDTH:
                            self.screen.blit(tile, (tile_x, y * TILE_SIZE))
                            
    def update_obstacles(self):
        for obstacle in self.obstacles:
            obstacle.update_position(self.ground_scroll)
            obstacle.draw(self.screen)
            
    def update_pickups(self):
        for pickup in self.pickups:
            pickup.update_position(self.ground_scroll)
            
            if pickup.is_offscreen(self.screen):
                pickup.respawn(self.obstacles, self.ground_scroll)
                
            pickup.draw(self.screen)
            
    def update_enemies(self):
        
        alive_enemies = []
        for enemy in self.enemies:
            if hasattr(enemy, '__class__') and hasattr(enemy.__class__, '__bases__') and Level1Enemy in enemy.__class__.__bases__:
                enemy.update(self.player, dt=1.0, obstacles=self.obstacles, scroll_offset=self.ground_scroll)
            else:
                enemy.update(self.player)

            
            if enemy.alive:
                alive_enemies.append(enemy)
                enemy.draw(self.screen)
        
        self.enemies = alive_enemies
        return alive_enemies
            
    def handle_input(self, keys):
        if keys[pygame.K_w]:
            if self.player and not self.player.invulnerable:
                self.player.take_damage()
                
                
    def check_win_lose_conditions(self):
        if self.player.lives <= 0:
            return "game_over"
        if self.player.won:
            return "boss_level1"
        return "playing"
        
    def run(self, screen):
        self.screen = screen
        self.reset_game()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                    
            self.screen.fill((0, 0, 0))
            self.draw_bg()
            
            self.update_obstacles()
            self.draw_tilemap()
            self.update_pickups()
            alive_enemies = self.update_enemies()
            
            for a in list(self.arrows):
                a.update(self.obstacles)
                a.collide(self.player, scroll_offset=self.ground_scroll)
                if not a.alive:
                    self.arrows.remove(a)
            for a in self.arrows:
                a.draw(self.screen, scroll_offset=self.ground_scroll)
            
            
            self.handle_pickup_collection()
            
            keys = pygame.key.get_pressed()
            self.handle_input(keys)
            
            if self.player:
                self.player.update(keys, self.obstacles,alive_enemies)
                self.player.draw(self.screen)
            
            self.handle_scrolling()
            
            self.update_lives()
            self.draw_debug_info()
            
            game_state = self.check_win_lose_conditions()
            if game_state != "playing":
                return game_state
            
            pygame.display.flip()
            self.clock.tick(60)
            
        return "menu"
        
    def handle_pickup_collection(self):
        pass

class Level1(Game):
    def __init__(self, width=960, height=640):
        super().__init__(width, height)
        
        self.load_background('assets/BGL', 11)
        self.load_tilemap("forestMap.tmx")
        self.load_ui_assets()
        
        self.process_tilemap()
        self.initialize_game_objects()
        
    def process_tilemap(self):
        TILE_SIZE = 32
        self.obstacles = []
        found_gids = set()
        self.start_position = (0, 100)
        
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid != 0:
                        found_gids.add(gid)
                        
                        props = self.tmx_data.get_tile_properties_by_gid(gid)
                        
                        # Handle enemy spawns - check if enemy property exists and get its AI type
                        if props and "enemy" in props:
                            ai_type = props.get("enemy")
                            enemy_x = x * TILE_SIZE
                            enemy_y = (y * TILE_SIZE) - 32
                            
                            # Create appropriate enemy type
                            if ai_type == "archer":
                                enemy = Archer(enemy_x, enemy_y)
                                enemy.level = self
                                self.enemies.append(enemy)
                            elif ai_type == "warrior":
                                enemy = Warrior(enemy_x, enemy_y)
                                enemy.level = self
                                self.enemies.append(enemy)

                            
                            print(f"Spawned {ai_type} enemy at ({enemy_x}, {enemy_y})")
                        
                        # Handle other tile types
                        elif props and props.get("type") == "tombstone":
                            obstacle = Spikes(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
                        elif props and props.get("type") == "ice":
                            obstacle = Ice(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
                        elif props and props.get("type") == "start":
                            obstacle = start(x * TILE_SIZE, y * TILE_SIZE)
                            self.start_position = (x * TILE_SIZE + 30, y * TILE_SIZE - 70)
                            self.obstacles.append(obstacle)
                        elif props and props.get("type") == "end":
                            obstacle = end(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
                        else:
                            # Regular block
                            obstacle = block(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
        
        print(f"Level 1 - All tile IDs found: {sorted(found_gids)}")
        print(f"Level 1 - Number of obstacles created: {len(self.obstacles)}")
        print(f"Level 1 - Number of enemies spawned: {len(self.enemies)}")
        
    def initialize_game_objects(self):
        self.player = mainCharacter(self.start_position[0], self.start_position[1])
        self.player.level = self
        self.player.enemies = self.enemies
        
        self.coin = Coin(400, 300)
        self.meat = Meat(200, 300)
        self.pickups = [self.coin, self.meat]
        
        if not hasattr(self, 'enemies') or self.enemies is None:
            self.enemies = []
        
    def handle_pickup_collection(self):
        if self.coin.update(self.player):
            self.coin_count += 1
            self.coin.respawn(self.obstacles, self.ground_scroll)
            print("Coin count: ", self.coin_count)
        
        if self.meat.update(self.player):
            self.player.lives += 1
            self.meat.respawn(self.obstacles, self.ground_scroll)
    
    
class BossLevel1(Game):
    def __init__(self, width=960, height=640):
        self.doScroll = False
        super().__init__(width, height)
        
        self.load_background('assets/BGL', 11)
        self.load_tilemap("forestBossMap.tmx")
        self.load_ui_assets()
        
        self.process_tilemap()
        self.initialize_game_objects()
        
        
    def process_tilemap(self):
        TILE_SIZE = 32
        self.obstacles = []
        found_gids = set()
        self.start_position = (0, 100)
        
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid != 0:
                        found_gids.add(gid)
                        
                        props = self.tmx_data.get_tile_properties_by_gid(gid)
                        
                        # Handle enemy spawns - check if enemy property exists and get its AI type
                        if props and "enemy" in props:
                            ai_type = props.get("enemy")
                            enemy_x = x * TILE_SIZE
                            enemy_y = (y * TILE_SIZE) - 32
                            
                            # Create appropriate enemy type
                            if ai_type == "archer":
                                enemy = Archer(enemy_x, enemy_y)
                                enemy.level = self
                                self.enemies.append(enemy)
                            elif ai_type == "warrior":
                                enemy = Warrior(enemy_x, enemy_y)
                                enemy.level = self
                                self.enemies.append(enemy)

                            
                            print(f"Spawned {ai_type} enemy at ({enemy_x}, {enemy_y})")
                        
                        # Handle other tile types
                        elif props and props.get("type") == "tombstone":
                            obstacle = Spikes(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
                        elif props and props.get("type") == "ice":
                            obstacle = Ice(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
                        elif props and props.get("type") == "start":
                            obstacle = start(x * TILE_SIZE, y * TILE_SIZE)
                            self.start_position = (x * TILE_SIZE + 30, y * TILE_SIZE - 70)
                            self.obstacles.append(obstacle)
                        elif props and props.get("type") == "end":
                            obstacle = end(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
                        else:
                            # Regular block
                            obstacle = block(x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
    def initialize_game_objects(self):
        self.player = mainCharacter(self.start_position[0], self.start_position[1])
        self.player.level = self
        self.player.enemies = self.enemies
        
        self.coin = Coin(400, 300)
        self.meat = Meat(200, 300)
        self.pickups = [self.coin, self.meat]
        
        if not hasattr(self, 'enemies') or self.enemies is None:
            self.enemies = []
