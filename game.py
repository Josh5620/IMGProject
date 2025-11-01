import pygame
import pytmx
from entities import mainCharacter
from Level1Enemies import BreakableBlock, Level1Enemy, Archer, Warrior, Mushroom
from Level2Enemies import MushroomPickup, MutatedMushroom, Skeleton, FlyingEye
from Level2Boss import EasyDungeonBoss, HardDungeonBoss
from blocks import block, Spikes, start, end, Ice, AnimatedTrap, LightningTrap, FireTrap
from particles import LeafParticle
from level2_powerup_loader import load_mushroom_sprites, create_level2_powerup_with_sprite, TILED_OBJECT_TO_POWERUP
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
        
        self.bg_images = []
        self.bg_width = 0
        self.tmx_data = None
        self.obstacles = []
        self.animated_traps = []
        self.spatial_hash = {}
        self.start_position = (300, 300)

        self.debug_mode = False # Start with debug mode off
        
        self.font = pygame.font.Font(None, 36)
        self.heart = None
        self.mushroom_icon = None
        self.mushroomCount = 0
        
        self.player = None
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
        
        mushroom_icon = pygame.image.load('assets/mushroom.png').convert_alpha()
        self.mushroom_icon = pygame.transform.scale(mushroom_icon, (30, 30))
        
    def reset_game(self):
        if self.player:
            self.player.lives = 3
            self.player.x = self.start_position[0]
            self.player.y = self.start_position[1]
            self.player.rect.x = self.start_position[0]
            self.player.rect.y = self.start_position[1]
            self.player.won = False
        self.scroll = 0
        self.ground_scroll = 0
        
    def draw_bg(self):
        start_bg_x = int(self.scroll // self.bg_width) - 1
        end_bg_x = int((self.scroll + self.WIDTH) // self.bg_width) + 2
        
        for x in range(start_bg_x, end_bg_x):
            speed = 1
            for i in self.bg_images:
                if self.doScroll:
                    bg_pos_x = (x * self.bg_width) - self.scroll * speed
                else:
                    bg_pos_x = x * self.bg_width
                if bg_pos_x > -self.bg_width and bg_pos_x < self.WIDTH:
                    self.screen.blit(i, (bg_pos_x, 0))
                speed += 0.1
            
        for particle in self.leaf_particles:
            particle.draw(self.screen, self.scroll if self.doScroll else 0)
                
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
    
    def draw_mushroom_count(self):
        self.screen.blit(self.mushroom_icon, (self.WIDTH - 150, 50))
        mushroom_text = self.font.render(f"x {self.mushroomCount}", True, (255, 255, 255))
        self.screen.blit(mushroom_text, (self.WIDTH - 110, 55))
        
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

                    if obj_type == "breakable" or obj_type == "mushroom":
                        continue
                    if image:
                        obj_x = obj.x - self.ground_scroll
                        if obj_x > -obj.width and obj_x < self.WIDTH:
                            self.screen.blit(image, (obj_x, obj.y))

    def build_spatial_hash(self):
        """Organizes all static obstacles into a spatial hash for efficient collision detection."""
        print("Building spatial hash...")
        TILE_SIZE = 32
        self.spatial_hash.clear()
        for obstacle in self.obstacles:
            # Determine which grid cell(s) the obstacle overlaps with.
            # For simplicity, we'll use its top-left corner.
            key = (int(obstacle.rect.x // TILE_SIZE), int(obstacle.rect.y // TILE_SIZE))
            if key not in self.spatial_hash:
                self.spatial_hash[key] = []
            self.spatial_hash[key].append(obstacle)
                            
    def update_obstacles(self):
        for obstacle in self.obstacles:
            obstacle.update_position(self.ground_scroll)
            obstacle.update()
            obstacle.draw(self.screen)
            
    def update_enemies(self):
        for enemy in self.enemies:
            if enemy.alive:
                # Level 1 and Level 2 enemies both use the same update signature
                if isinstance(enemy, Level1Enemy) or hasattr(enemy, 'scroll_offset'):
                    enemy.update(self.player, dt=1.0, obstacles=self.obstacles, scroll_offset=self.ground_scroll)
                else:
                    # Fallback for other enemy types
                    enemy.update(self.player)
                
                enemy.draw(self.screen)
        
        self.enemies = [e for e in self.enemies if e.alive]
    
    def check_mushroom_collection(self):
        if not self.player:
            return
        
        for enemy in self.enemies[:]:
            if hasattr(enemy, 'is_collectible') and enemy.is_collectible:
                if enemy.check_player_collision(self.player, self.ground_scroll):
                    enemy.collect()
                    self.mushroomCount += 1
            
    def handle_input(self, keys):
        if keys[pygame.K_w]:
            if self.player and not self.player.invulnerable:
                self.player.take_damage()
        
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b: # 'B' for Boxes
                    self.debug_mode = not self.debug_mode
                    print(f"Debug Mode: {'ON' if self.debug_mode else 'OFF'}")
                

    def draw_debug_info(self):
        """Draws collision boxes if debug mode is active."""
        if not self.debug_mode:
            return

        # Draw player's collision box in blue
        if self.player:
            player_screen_rect = self.player.rect.copy()
            player_screen_rect.x -= self.ground_scroll
            pygame.draw.rect(self.screen, (0, 0, 255), player_screen_rect, 2)

        # Draw all obstacle collision boxes in red
        for obstacle in self.obstacles:
            obstacle_screen_rect = obstacle.rect.copy()
            obstacle_screen_rect.x -= self.ground_scroll
            pygame.draw.rect(self.screen, (255, 0, 0), obstacle_screen_rect, 1)
                

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
        esc_was_pressed = False  # Track ESC key state to avoid multiple triggers
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                
                # Check for pause key (ESC only)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if not esc_was_pressed:  # Only trigger once per press
                            esc_was_pressed = True
                            # Import here to avoid circular import
                            from menus import pause_menu
                            
                            # Capture current game state
                            game_surface = self.screen.copy()
                            
                            # Show pause menu
                            pause_action = pause_menu(self.WIDTH, self.HEIGHT, self.screen, game_surface)
                            
                            if pause_action == 'restart':
                                self.reset_game()
                            elif pause_action == 'main_menu':
                                return "start"
                            elif pause_action == 'quit':
                                return "quit"
                            # If 'resume', just continue the game loop
                
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_ESCAPE:
                        esc_was_pressed = False  # Reset when key is released
                    
            self.screen.fill((0, 0, 0))
            self.draw_bg()
            
            self.update_obstacles()
            self.draw_tilemap()
            self.update_particles()
            self.update_enemies()
            
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
            
            # Check for mushroom collection
            self.check_mushroom_collection()
            self.draw_debug_info()

            keys = pygame.key.get_pressed()
            self.handle_input(keys)
            
            # For damage with animated traps
            if self.player:
                for trap in self.animated_traps:
                    trap.update(self.player, scroll_offset=self.ground_scroll)
                    self.screen.blit(trap.image, (trap.rect.x - self.ground_scroll, trap.rect.y))

            if self.player:
                self.player.update(keys, self.obstacles, self.enemies)
                self.player.draw(self.screen)
            
            self.handle_scrolling()
            
            self.update_lives()
            self.draw_mushroom_count()
            self.draw_debug_info()
            
            game_state = self.check_win_lose_conditions()
            if game_state != "playing":
                return game_state
            
            pygame.display.flip()
            self.clock.tick(60)
            
        return "menu"

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
        self.enemies = []
        self.start_position = (0, 100)
        
        objectLayer = self.tmx_data.get_layer_by_name("Object Layer 1")
        tile_layer = self.tmx_data.get_layer_by_name("Tile Layer 1")
        if isinstance(tile_layer, pytmx.TiledTileLayer):
            for x, y, gid in tile_layer.iter_data():
                if not gid:
                    continue

                props = self.tmx_data.get_tile_properties_by_gid(gid) or {}
                typ = props.get("type")
                
                # Handle different obstacle types
                if typ == "tombstone":
                    self.obstacles.append(Spikes(x * TILE_SIZE, y * TILE_SIZE))
                elif typ == "ice":
                    self.obstacles.append(Ice(x * TILE_SIZE, y * TILE_SIZE))
                else:
                    # Default block
                    self.obstacles.append(block(x * TILE_SIZE, y * TILE_SIZE))
        
        
        if isinstance(objectLayer, pytmx.TiledObjectGroup):
            for obj in objectLayer:
                typ = getattr(obj, "type", None) or (obj.properties or {}).get("type")
                block_image = self.tmx_data.get_tile_image_by_gid(obj.gid)
                
                if typ == "end":
                    self.obstacles.append(end(obj.x, obj.y))
                elif typ == "start":
                    self.obstacles.append(start(obj.x, obj.y))
                    self.start_position = (obj.x + 30, obj.y - 70)
                elif typ == "breakable":
                    self.enemies.append(BreakableBlock(obj.x, obj.y, block_image))
                elif typ == "mushroom":
                    self.enemies.append(Mushroom(obj.x, obj.y, block_image))
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
        self.player = mainCharacter(self.start_position[0], self.start_position[1])
        self.player.level = self
        self.player.current_level = 1  # Level 1
        self.player.enemies = self.enemies

class Level2(Game):
    def __init__(self, width=960, height=640):
       super().__init__(width, height)

       #--- Assets loading ---
       self.load_background('assets/BGL2', 5)
       self.load_tilemap("DungeonMapActual.tmx")
       self.load_ui_assets()
       self.animated_traps = []
       self.powerups = []  # Level 2 powerups
       
       # Load mushroom sprites for powerups
       self.mushroom_sprites = load_mushroom_sprites()
       print(f"✅ Loaded {len(self.mushroom_sprites)} mushroom powerup sprites")

       self.process_tilemap()
       self.initialize_game_objects()

    def process_tilemap(self):
        TILE_SIZE = 32
        self.obstacles = []
        self.enemies = []
        self.start_position = (0, 100)
        
        objectLayer = self.tmx_data.get_layer_by_name("Object Layer 1")
        tile_layer = self.tmx_data.get_layer_by_name("Tile Layer 1")
        if isinstance(tile_layer, pytmx.TiledTileLayer):
            for x, y, gid in tile_layer.iter_data():

                if not gid:
                    continue

                props = self.tmx_data.get_tile_properties_by_gid(gid) or {}
                typ = props.get("type")
                
                # Handle different obstacle types
                if typ == "tombstone":
                    self.obstacles.append(Spikes(x * TILE_SIZE, y * TILE_SIZE))
                elif typ == "ice":
                    self.obstacles.append(Ice(x * TILE_SIZE, y * TILE_SIZE))
                else:
                    # Default block
                    self.obstacles.append(block(x * TILE_SIZE, y * TILE_SIZE))
        
        
        if isinstance(objectLayer, pytmx.TiledObjectGroup):
            for obj in objectLayer:
                typ = getattr(obj, "type", None) or (obj.properties or {}).get("type")
                
                if typ == "end":
                    self.obstacles.append(end(obj.x, obj.y))
                elif typ == "start":
                    self.obstacles.append(start(obj.x, obj.y))
                    self.start_position = (obj.x , obj.y - 70)
                    continue
                
                # === LEVEL 2 ENEMY SPAWNING ===
                elif typ == "skeleton":
                    # Spawn at ground level - obj.y is bottom of object in Tiled
                    enemy = Skeleton(obj.x, obj.y - 96)  # Adjusted for 128px sprite + centering
                    enemy.level = self
                    self.enemies.append(enemy)
                    print(f"Spawned Skeleton at ({obj.x}, {obj.y - 96})")
                    continue
                
                elif typ == "mushroom_enemy":
                    # Spawn at ground level
                    enemy = MutatedMushroom(obj.x, obj.y - 96)  # Adjusted for 128px sprite + centering
                    enemy.level = self
                    self.enemies.append(enemy)
                    print(f"Spawned Mutated Mushroom at ({obj.x}, {obj.y - 96})")
                    continue
                
                elif typ == "flyingeye":
                    # Flying enemy - spawn in air
                    enemy = FlyingEye(obj.x, obj.y - 64)  # Different offset for flying
                    enemy.level = self
                    self.enemies.append(enemy)
                    print(f"Spawned Flying Eye at ({obj.x}, {obj.y - 64})")
                    continue
                
                # === BOSSES ===
                elif typ == "boss_easy":
                    boss = EasyDungeonBoss(obj.x, obj.y - 96)
                    boss.level = self
                    self.enemies.append(boss)
                    print(f"Spawned EASY BOSS at ({obj.x}, {obj.y - 96})")
                    continue
                
                elif typ == "boss_hard":
                    boss = HardDungeonBoss(obj.x, obj.y - 96)
                    boss.level = self
                    self.enemies.append(boss)
                    print(f"Spawned HARD BOSS at ({obj.x}, {obj.y - 96})")
                    continue
                
                # === TRAPS ===
                elif typ == "sawtrap":
                    anchor_x = obj.x + obj.width / 2
                    anchor_y = obj.y 
                    trap = AnimatedTrap(anchor_x, anchor_y, 'assets/Level2/Traps/SawTrap.png', 64, 32)
                    trap.level = self
                    self.animated_traps.append(trap)
                    continue
                
                elif typ == "lightningtrap":
                    anchor_x = obj.x + obj.width / 2
                    anchor_y = obj.y
                    trap = LightningTrap(anchor_x, anchor_y, damage=1, cooldown=2000)
                    trap.level = self
                    self.animated_traps.append(trap)
                    continue
                
                elif typ == "firetrap":
                    anchor_x = obj.x + obj.width / 2
                    anchor_y = obj.y
                    trap = FireTrap(anchor_x, anchor_y, damage=1, cooldown=3000)
                    trap.level = self
                    self.animated_traps.append(trap)
                    continue
                
                # === COLLECTIBLES ===
                elif typ == "mushroom4":
                    # Get the mushroom image directly from the tile object's gid
                    # (since it's placed as a tile from the sprite sheet in Tiled)
                    mushroom_image = self.tmx_data.get_tile_image_by_gid(obj.gid)
                    
                    if mushroom_image:
                        # The image is already the right sprite from your Level 2 mushroom sheet!
                        # Scale it if needed
                        mushroom_image = pygame.transform.scale(mushroom_image, (32, 32))
                        mushroom = MushroomPickup(obj.x, obj.y, mushroom_image)
                        self.enemies.append(mushroom)
                    else:
                        print(f"Warning: Could not load mushroom image for object at ({obj.x}, {obj.y})")
                    continue
                
                # === LEVEL 2 POWERUPS ===
                elif typ in TILED_OBJECT_TO_POWERUP:
                    # Map Tiled object name to powerup type
                    powerup_type = TILED_OBJECT_TO_POWERUP[typ]
                    # Center the 60x60 collision box on the Tiled object position
                    # Subtract 30 (half of 60) to center it
                    powerup = create_level2_powerup_with_sprite(
                        obj.x - 30, obj.y - 30, powerup_type, self.mushroom_sprites
                    )
                    self.powerups.append(powerup)
                    print(f"Spawned {powerup_type} powerup at ({obj.x - 30}, {obj.y - 30})")
                    continue
        
        print(f"Level 2 - Number of obstacles created: {len(self.obstacles)}")
        print(f"Level 2 - Number of enemies spawned: {len(self.enemies)}")
        print(f"Level 2 - Number of traps spawned: {len(self.animated_traps)}")
        print(f"Level 2 - Number of powerups spawned: {len(self.powerups)}")
        
        self.build_spatial_hash() # Build spatial hash after obstacles are created

    def initialize_game_objects(self):
        if self.start_position:
            self.player = mainCharacter(self.start_position[0], self.start_position[1])
            self.player.level = self
            self.player.current_level = 2  # Enable Level 2 abilities
        else:
            # Fallback if no start position is found
            self.player = mainCharacter(100, 100)
            self.player.level = self
            self.player.current_level = 2  # Enable Level 2 abilities
            print("Warning: No start position found in tilemap. Defaulting to (100, 100).")
    
    def update_powerups(self):
        """Update all Level 2 powerups"""
        for powerup in self.powerups[:]:
            if not powerup.collected:
                powerup.update(self.player, dt=1.0, scroll_offset=self.ground_scroll)
            else:
                # Keep updating until particles are gone
                powerup.update(self.player, dt=1.0, scroll_offset=self.ground_scroll)
                if not powerup.collection_particles:
                    self.powerups.remove(powerup)
    
    def draw_powerups(self):
        """Draw all Level 2 powerups with scroll offset"""
        for powerup in self.powerups:
            powerup.draw(self.screen, self.ground_scroll)
    
    def run(self, screen):
        """Override run method to include Level 2 powerup logic"""
        self.screen = screen
        self.reset_game()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                
                # Check for pause key (ESC or P)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        from menus import pause_menu
                        game_surface = self.screen.copy()
                        pause_action = pause_menu(self.WIDTH, self.HEIGHT, self.screen, game_surface)
                        
                        if pause_action == 'restart':
                            self.reset_game()
                        elif pause_action == 'main_menu':
                            return "start"
                        elif pause_action == 'quit':
                            return "quit"
                    
            self.screen.fill((0, 0, 0))
            self.draw_bg()
            
            self.update_obstacles()
            self.draw_tilemap()
            self.update_particles()
            self.update_enemies()
            
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
            
            # Check for mushroom collection
            self.check_mushroom_collection()
            
            # === LEVEL 2 SPECIFIC: Update and draw powerups ===
            self.update_powerups()
            self.draw_powerups()
            
            self.draw_debug_info()

            keys = pygame.key.get_pressed()
            self.handle_input(keys)
            
            # For damage with animated traps
            if self.player:
                for trap in self.animated_traps:
                    trap.update(self.player, scroll_offset=self.ground_scroll)
                    self.screen.blit(trap.image, (trap.rect.x - self.ground_scroll, trap.rect.y))

            if self.player:
                self.player.update(keys, self.obstacles, self.enemies)
                self.player.draw(self.screen)
            
            self.handle_scrolling()
            
            self.update_lives()
            self.draw_mushroom_count()
            self.draw_debug_info()
            
            game_state = self.check_win_lose_conditions()
            if game_state != "playing":
                return game_state
            
            pygame.display.flip()
            self.clock.tick(60)
            
        return "menu"


    
class BossLevel1(Game):
    def __init__(self, width=960, height=640):
        super().__init__(width, height)
        
        
        self.load_background('assets/BossBGL', 5)
        self.load_tilemap("forestBossMap.tmx")
        self.load_ui_assets()
        
        self.process_tilemap()
        self.initialize_game_objects()
        
        
    def process_tilemap(self):
        TILE_SIZE = 32
        self.obstacles = []
        self.enemies = []
        self.start_position = (0, 50)
        
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    if gid == 0:
                        continue
                        
                    props = self.tmx_data.get_tile_properties_by_gid(gid)
                    
                    # Handle enemy spawns - check if enemy property exists and get its AI type
                    if props and "enemy" in props:
                        ai_type = props.get("enemy")
                        enemy_x = x * TILE_SIZE
                        enemy_y = (y * TILE_SIZE) - 32
                        
                        # Use dictionary mapping for enemy types
                        enemy_map = {
                            "archer": Archer,
                            "warrior": Warrior
                        }
                        if ai_type in enemy_map:
                            enemy = enemy_map[ai_type](enemy_x, enemy_y)
                            enemy.level = self
                            self.enemies.append(enemy)
                            print(f"Spawned {ai_type} enemy at ({enemy_x}, {enemy_y})")
                    
                    # Handle obstacle types
                    elif props:
                        typ = props.get("type")
                        obstacle_map = {
                            "tombstone": Spikes,
                            "ice": Ice,
                            "start": start,
                            "end": end
                        }
                        
                        if typ in obstacle_map:
                            obstacle = obstacle_map[typ](x * TILE_SIZE, y * TILE_SIZE)
                            self.obstacles.append(obstacle)
                            
                            if typ == "start":
                                self.start_position = (x * TILE_SIZE + 30, y * TILE_SIZE - 70)
                        else:
                            # Regular block
                            self.obstacles.append(block(x * TILE_SIZE, y * TILE_SIZE))
                            
    def initialize_game_objects(self):
        self.player = mainCharacter(self.start_position[0], self.start_position[1])
        self.player.level = self
        self.player.current_level = 1  # Boss Level (Level 1 abilities)
        self.player.enemies = self.enemies
    
    def run(self, screen):
        self.doScroll = False
        return super().run(screen)
        