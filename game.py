import pygame
import pytmx
from entities import MainCharacter
from Level1Enemies import BreakableBlock, Level1Enemy, Archer, Warrior
from blocks import block, Spikes, start, end, Ice
from pickups import Coin, Meat
from particles import LeafParticle
import random

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
        
        self.leaf_particles = [LeafParticle(random.randint(0, 960), random.randint(-200, 0)) for _ in range(50)]
        
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
            
        for particle in self.leaf_particles:
            particle.draw(self.screen, self.scroll)
                
    def update_lives(self):
        if self.player and self.heart:
            for i in range(self.player.lives):
                self.screen.blit(self.heart, (10 + i * 30, 10))

    def update_particles(self):
            
        for particle in self.leaf_particles:
            particle.update(self.obstacles, self.scroll)
        
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
            if isinstance(layer, pytmx.TiledObjectGroup):
                for obj in layer:
                    image = self.tmx_data.get_tile_image_by_gid(obj.gid)
                    obj_type = getattr(obj, "type", None) or (obj.properties or {}).get("type")

                    if obj_type == "breakable":
                        continue
                    if image:
                        obj_x = obj.x - self.ground_scroll
                        if obj_x > -obj.width and obj_x < self.WIDTH:
                            self.screen.blit(image, (obj_x, obj.y))
                            
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
        # MEMORY LEAK FIX: More efficient enemy list management
        for enemy in self.enemies:
            if enemy.alive:  # Only update alive enemies
                if hasattr(enemy, '__class__') and hasattr(enemy.__class__, '__bases__') and Level1Enemy in enemy.__class__.__bases__:
                    enemy.update(self.player, dt=1.0, obstacles=self.obstacles, scroll_offset=self.ground_scroll)
                else:
                    enemy.update(self.player)
                
                enemy.draw(self.screen)
        
        # Remove dead enemies after all updates
        alive_enemies = [e for e in self.enemies if e.alive]
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
        
        # Initialize delta time properly
        self.clock.tick()  # Prime the clock
        
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
            self.update_particles()
            alive_enemies = self.update_enemies()
            
            # MEMORY LEAK FIX: More efficient arrow cleanup
            active_arrows = []
            for arrow in self.arrows:
                if not arrow.alive:
                    continue

                arrow.update(self.obstacles)
                arrow.collide(self.player, scroll_offset=self.ground_scroll)

                if arrow.alive:
                    active_arrows.append(arrow)

            self.arrows = active_arrows

            for arrow in self.arrows:
                arrow.draw(self.screen, scroll_offset=self.ground_scroll)
            
            
            self.handle_pickup_collection()
            
            keys = pygame.key.get_pressed()
            self.handle_input(keys)
            
            if self.player:
                # Calculate delta time AFTER the previous tick
                # Get milliseconds since last frame and normalize to 60 FPS baseline
                dt = min(self.clock.get_time() / (1000.0 / 60.0), 3.0)  # Cap at 3x to prevent huge jumps
                
                self.player.update(keys, self.obstacles, alive_enemies, dt)
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
        self.start_position = (0, 100)
        
        objectLayer = self.tmx_data.get_layer_by_name("Object Layer 1")
        tile_layer = self.tmx_data.get_layer_by_name("Tile Layer 1")
        if isinstance(tile_layer, pytmx.TiledTileLayer):
            for x, y, gid in tile_layer.iter_data():
                if not gid:
                    continue

                props = self.tmx_data.get_tile_properties_by_gid(gid) or {}
                typ = props.get("type")
                if typ == "tombstone":
                    self.obstacles.append(Spikes(x * TILE_SIZE, y * TILE_SIZE))
                elif typ == "ice":
                    self.obstacles.append(Ice(x * TILE_SIZE, y * TILE_SIZE))
                else:
                    self.obstacles.append(block(x * TILE_SIZE, y * TILE_SIZE))
        
        
        if isinstance(objectLayer, pytmx.TiledObjectGroup):
            self.enemies = []
            
            for obj in objectLayer:
                typ = getattr(obj, "type", None) or (obj.properties or {}).get("type")
                if typ == "end":
                    self.obstacles.append(end(obj.x, obj.y))
                if typ == "breakable":
                    block_image = self.tmx_data.get_tile_image_by_gid(obj.gid)
                    new_block = BreakableBlock(obj.x, obj.y, block_image)
                    self.enemies.append(new_block)
                elif typ == "start":
                    self.obstacles.append(start(obj.x, obj.y))
                    self.start_position = (obj.x + 30, obj.y - 70)
                elif typ == "archer":
                    enemy = Archer(obj.x, obj.y - 32)
                    enemy.level = self
                    self.enemies.append(enemy)
                elif typ == "warrior":
                    enemy = Warrior(obj.x, obj.y - 32)
                    enemy.level = self
                    self.enemies.append(enemy)
        print(f"Level 1 - Number of obstacles created: {len(self.obstacles)}")
        print(f"Level 1 - Number of enemies spawned: {len(self.enemies)}")
        
    def initialize_game_objects(self):
        self.player = MainCharacter(self.start_position[0], self.start_position[1])
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

#class Level2(Game):
#    def __init__(self, width=960, height=640):
#       super().__init__(width, height)


    
class BossLevel1(Game):
    def __init__(self, width=960, height=640):
        super().__init__(width, height)
        self.doScroll = False
        
        self.load_background('assets/BossBGL', 5)
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
        self.player = MainCharacter(self.start_position[0], self.start_position[1])
        self.player.level = self
        self.player.enemies = self.enemies
        
        self.coin = Coin(400, 300)
        self.meat = Meat(200, 300)
        self.pickups = [self.coin, self.meat]
        
        if not hasattr(self, 'enemies') or self.enemies is None:
            self.enemies = []
    
        