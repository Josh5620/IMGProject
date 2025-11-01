import pygame
import pytmx
from entities import mainCharacter
from Level1Enemies import BreakableBlock, Level1Enemy, Archer, Warrior, Mushroom
from Level2Enemies import MushroomPickup, MutatedMushroom, Skeleton, FlyingEye
from BossEnemy import EasyDungeonBoss, HardDungeonBoss
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
                # Check if it's a boss enemy (from BossEnemy.py)
                if hasattr(enemy, 'projectiles') and hasattr(enemy, 'difficulty'):
                    # Boss enemies need obstacles for collision detection
                    enemy.update(self.player, dt=1.0, obstacles=self.obstacles, scroll_offset=self.ground_scroll)
                # Level 1 and Level 2 enemies both use the same update signature
                elif isinstance(enemy, Level1Enemy) or hasattr(enemy, 'scroll_offset'):
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
       self.boss_difficulty = "normal"  # Default difficulty
       self.mushroom_count = 0  # Track collected mushrooms
       self.min_mushrooms_for_boss = 10  # Minimum required for boss fight
       self.boss_gate_message_timer = 0  # Timer for showing message
       
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

                # ===BOSS FIGHT DIFFICULTIES===
                elif typ == "EasyEnd":
                    self.obstacles.append(end(obj.x, obj.y))
                    self.boss_difficulty = "easy"
                elif typ == "HardEnd":
                    self.obstacles.append(end(obj.x, obj.y))
                    self.boss_difficulty = "hard"
        
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
                was_collected = powerup.collected
                powerup.update(self.player, dt=1.0, scroll_offset=self.ground_scroll)
                # Check if powerup was just collected
                if not was_collected and powerup.collected:
                    self.mushroom_count += 1
                    print(f"Mushroom collected! Total: {self.mushroom_count}/{self.min_mushrooms_for_boss}")
            else:
                # Keep updating until particles are gone
                powerup.update(self.player, dt=1.0, scroll_offset=self.ground_scroll)
                if not powerup.collection_particles:
                    self.powerups.remove(powerup)
    
    def draw_powerups(self):
        """Draw all Level 2 powerups with scroll offset"""
        for powerup in self.powerups:
            powerup.draw(self.screen, self.ground_scroll)
    
    def draw_mushroom_count(self):
        """Draw mushroom counter on the right side of screen"""
        # Load mushroom sprite icon
        try:
            mushroom_icon = pygame.image.load("assets/mushroom.png").convert_alpha()
            mushroom_icon = pygame.transform.scale(mushroom_icon, (40, 40))
        except Exception as e:
            print(f"Error loading mushroom icon: {e}")
            # Fallback: create a simple surface
            mushroom_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(mushroom_icon, (220, 80, 80), (20, 20), 18)
        
        # Position on right side of screen
        icon_x = self.WIDTH - 180  # More space for text
        icon_y = 80
        
        # Draw mushroom icon
        self.screen.blit(mushroom_icon, (icon_x, icon_y))
        
        # Draw count text with pixel font
        try:
            font = pygame.font.Font("assets/yoster.ttf", 36)
        except:
            font = pygame.font.Font(None, 48)
        count_text = f"x {self.mushroom_count}"
        text_surf = font.render(count_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(left=icon_x + 40, centery=icon_y + 16)
        
        # Draw text with shadow for readability
        shadow_surf = font.render(count_text, True, (0, 0, 0))
        shadow_rect = text_surf.get_rect(left=icon_x + 42, centery=icon_y + 18)
        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(text_surf, text_rect)
        
        # Draw requirement indicator if needed
        if self.mushroom_count < self.min_mushrooms_for_boss:
            try:
                small_font = pygame.font.Font("assets/yoster.ttf", 14)
            except:
                small_font = pygame.font.Font(None, 16)
            req_text = f"Need {self.min_mushrooms_for_boss} for boss"
            req_surf = small_font.render(req_text, True, (255, 200, 100))
            req_rect = req_surf.get_rect(left=icon_x, top=icon_y + 40)
            self.screen.blit(req_surf, req_rect)
        else:
            # Player has enough mushrooms - show "READY!"
            try:
                small_font = pygame.font.Font("assets/yoster.ttf", 18)
            except:
                small_font = pygame.font.Font(None, 20)
            ready_text = "BOSS READY!"
            ready_surf = small_font.render(ready_text, True, (100, 255, 100))
            ready_rect = ready_surf.get_rect(left=icon_x, top=icon_y + 40)
            self.screen.blit(ready_surf, ready_rect)
        
        # Draw warning message if player tried to enter boss without enough mushrooms
        if self.boss_gate_message_timer > 0:
            self.boss_gate_message_timer -= 1
            try:
                warning_font = pygame.font.Font("assets/yoster.ttf", 32)
            except:
                warning_font = pygame.font.Font(None, 36)
            warning_text = f"Need {self.min_mushrooms_for_boss} mushrooms to fight boss!"
            warning_surf = warning_font.render(warning_text, True, (255, 100, 100))
            warning_rect = warning_surf.get_rect(center=(self.WIDTH // 2, 100))
            
            # Draw with pulsing effect
            pulse = abs(int(self.boss_gate_message_timer % 30 - 15)) + 10
            for i in range(3):
                glow_surf = warning_font.render(warning_text, True, (255, 50, 50, pulse * (3 - i)))
                glow_rect = warning_surf.get_rect(center=(self.WIDTH // 2 + i, 100 + i))
                self.screen.blit(glow_surf, glow_rect)
            
            self.screen.blit(warning_surf, warning_rect)
    
    def run(self, screen):
        """Override run method to include Level 2 powerup logic"""
        self.screen = screen
        self.reset_game()
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                
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
                            pygame.quit()
                            exit()
                    
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
    
    def check_win_lose_conditions(self):
        """Override to handle boss level transition with difficulty"""
        if self.player.lives <= 0:
            return "game_over"
        if self.player.won:
            # Check if player has enough mushrooms for boss fight
            if self.mushroom_count < self.min_mushrooms_for_boss:
                # Block player from progressing - reset their position back
                print(f"Not enough mushrooms! {self.mushroom_count}/{self.min_mushrooms_for_boss}")
                self.player.won = False
                # Push player back
                self.player.rect.x -= 50
                # Show warning message
                self.boss_gate_message_timer = 180  # 3 seconds at 60fps
                return "playing"
            
            # Player has enough mushrooms - allow boss fight
            print(f"Boss fight unlocked! Mushrooms collected: {self.mushroom_count}")
            # Return boss level with appropriate difficulty
            if self.boss_difficulty == "easy":
                return "boss_level_easy"
            elif self.boss_difficulty == "hard":
                return "boss_level_hard"
            else:
                return "boss_level_normal"
        return "playing"

class FinalBossLevel(Game):
    """Final boss level with Level 2 mushrooms, traps, and boss fight"""
    
    def __init__(self, width=960, height=640, difficulty="normal"):
        super().__init__(width, height)
        self.difficulty = difficulty
        self.boss = None
        self.boss_defeated = False
        self.boss_summoned_minions = []
        self.animated_traps = []
        self.powerups = []
        
        # Track level completion
        self.level_complete = False
        self.victory_timer = 0
        
        # Mushroom tracking for boss level
        self.mushroom_count = 0
        self.min_mushrooms_for_boss = 10  # Not required for boss fight, but track anyway
        self.boss_gate_message_timer = 0
        
        # Load Level 2 powerups
        from level2_powerup_loader import load_mushroom_sprites
        self.mushroom_sprites = load_mushroom_sprites()
        print(f'Boss Level - Loaded {len(self.mushroom_sprites)} mushroom powerup sprites')

        # Load boss level assets
        self.load_background('assets/BossBGL', 7)
        self.load_tilemap("FinalBossMap.tmx")
        self.load_ui_assets()
        self.process_tilemap()
        self.initialize_game_objects()
        
        print(f"Final Boss Level initialized with difficulty: {self.difficulty}")

    def process_tilemap(self):
        """Process tilemap to spawn boss, Level 2 mushrooms and traps"""
        TILE_SIZE = 32
        self.obstacles = []
        self.enemies = []
        self.start_position = (0, 100)
        
        # Process tile layer for solid blocks
        tile_layer = self.tmx_data.get_layer_by_name("Tile Layer 1")
        if isinstance(tile_layer, pytmx.TiledTileLayer):
            for x, y, gid in tile_layer.iter_data():
                if not gid:
                    continue

                props = self.tmx_data.get_tile_properties_by_gid(gid) or {}
                typ = props.get("type")
                
                # Create solid blocks
                self.obstacles.append(block(x * TILE_SIZE, y * TILE_SIZE))
        
        # Process object layer for entities
        objectLayer = self.tmx_data.get_layer_by_name("Object Layer 1")
        if isinstance(objectLayer, pytmx.TiledObjectGroup):
            for obj in objectLayer:
                typ = getattr(obj, "type", None) or (obj.properties or {}).get("type")
                
                # === LEVEL MARKERS ===
                if typ == "end":
                    self.obstacles.append(end(obj.x, obj.y))
                elif typ == "start":
                    self.obstacles.append(start(obj.x, obj.y))
                    self.start_position = (obj.x, obj.y - 70)
                    continue
                
                # === BOSS SPAWNING ===
                elif typ == "final_boss" or typ == "boss_spawn":
                    if self.difficulty == "easy":
                        self.boss = EasyDungeonBoss(obj.x, obj.y - 128)
                    elif self.difficulty == "hard":
                        self.boss = HardDungeonBoss(obj.x, obj.y - 128)
                    else:  # normal difficulty defaults to easy
                        self.boss = EasyDungeonBoss(obj.x, obj.y - 128)
                    
                    self.boss.level = self
                    self.enemies.append(self.boss)
                    print(f"Spawned {self.difficulty.upper()} Boss at ({obj.x}, {obj.y - 128})")
                    continue
                
                # === LEVEL 2 MUSHROOM MINIONS ===
                elif typ == "mushroom_enemy" or typ == "mushroom_minion":
                    from Level2Enemies import MutatedMushroom
                    enemy = MutatedMushroom(obj.x, obj.y - 96)
                    enemy.level = self
                    enemy.max_hp = 50  # Reduced HP for boss level
                    enemy.current_hp = 50
                    self.enemies.append(enemy)
                    print(f"Spawned Mushroom Minion at ({obj.x}, {obj.y - 96})")
                    continue
                
                # === COLLECTIBLE MUSHROOMS ===
                elif typ == "mushroom4":
                    mushroom_image = self.tmx_data.get_tile_image_by_gid(obj.gid)
                    
                    if mushroom_image:
                        mushroom_image = pygame.transform.scale(mushroom_image, (32, 32))
                        mushroom = MushroomPickup(obj.x, obj.y, mushroom_image)
                        self.enemies.append(mushroom)
                        print(f"Spawned collectible mushroom at ({obj.x}, {obj.y})")
                    else:
                        print(f"Warning: Could not load mushroom image for object at ({obj.x}, {obj.y})")
                    continue

                # === LEVEL 2 POWERUPS ===
                elif typ in TILED_OBJECT_TO_POWERUP:
                    powerup_type = TILED_OBJECT_TO_POWERUP[typ]
                    powerup = create_level2_powerup_with_sprite(
                        obj.x - 30, obj.y - 30, powerup_type, self.mushroom_sprites
                    )
                    self.powerups.append(powerup)
                    print(f"Spawned {powerup_type} powerup at ({obj.x - 30}, {obj.y - 30})")
                    continue
                
                # === LEVEL 2 TRAPS ===
                elif typ == "firetrap":
                    anchor_x = obj.x + obj.width / 2
                    anchor_y = obj.y
                    trap = FireTrap(anchor_x, anchor_y, damage=2, cooldown=2000)  # Increased damage for boss level
                    trap.level = self
                    self.animated_traps.append(trap)
                    print(f"Spawned Fire Trap at ({anchor_x}, {anchor_y})")
                    continue
                
                elif typ == "lightningtrap":
                    anchor_x = obj.x + obj.width / 2
                    anchor_y = obj.y
                    trap = LightningTrap(anchor_x, anchor_y, damage=2, cooldown=1500)  # Increased damage
                    trap.level = self
                    self.animated_traps.append(trap)
                    print(f"Spawned Lightning Trap at ({anchor_x}, {anchor_y})")
                    continue
                
                elif typ == "sawtrap":
                    anchor_x = obj.x + obj.width / 2
                    anchor_y = obj.y
                    trap = AnimatedTrap(anchor_x, anchor_y, 'assets/Level2/Traps/SawTrap.png', 64, 32)
                    trap.level = self
                    self.animated_traps.append(trap)
                    print(f"Spawned Saw Trap at ({anchor_x}, {anchor_y})")
                    continue
                
        # If no boss was spawned from tilemap, create one manually
        if not self.boss:
            if self.difficulty == "easy":
                self.boss = EasyDungeonBoss(400, 300)  # Center of screen
            elif self.difficulty == "hard":
                self.boss = HardDungeonBoss(400, 300)
            else:  # normal difficulty defaults to easy
                self.boss = EasyDungeonBoss(400, 300)
            
            self.boss.level = self
            self.enemies.append(self.boss)
            print(f"Manually spawned {self.difficulty.upper()} Boss at (400, 300)")
        
        print(f"Boss Level - Obstacles: {len(self.obstacles)}")
        print(f"Boss Level - Enemies: {len(self.enemies)} (Boss: {'Yes' if self.boss else 'No'})")
        print(f"Boss Level - Traps: {len(self.animated_traps)}")
        print(f"Boss Level - Powerups: {len(self.powerups)}")
        self.build_spatial_hash()

    def initialize_game_objects(self):
        """Initialize player with full abilities for boss fight"""
        if self.start_position:
            self.player = mainCharacter(self.start_position[0], self.start_position[1])
            self.player.level = self
            self.player.current_level = 3  # Enable all abilities for boss fight
            
            # Give player some health advantage for boss fight
            if self.difficulty == "hard":
                self.player.max_hp = 8  # Extra HP for hard mode
                self.player.current_hp = 8
            else:
                self.player.max_hp = 6
                self.player.current_hp = 6
                
        else:
            self.player = mainCharacter(0, 100)
            self.player.level = self
            self.player.current_level = 3
            print("Warning: No start position found in tilemap. Defaulting to (0, 100).")

    def update(self, dt):
        """Update boss level with special boss mechanics"""
        if self.level_complete:
            self.victory_timer += dt
            if self.victory_timer > 180:  # 3 seconds
                return "victory"  # Signal victory to main game
            return
        
        # Update player (get current key state)
        keys = pygame.key.get_pressed()
        self.player.update(keys, self.obstacles, self.enemies)
        
        # Update enemies (including boss) using proper method
        for enemy in self.enemies[:]:  # Copy list to avoid modification issues
            if enemy.alive:
                # Check if it's a boss enemy (from BossEnemy.py)
                if hasattr(enemy, 'projectiles') and hasattr(enemy, 'difficulty'):
                    # Boss enemies need obstacles for collision detection
                    enemy.update(self.player, dt=dt, obstacles=self.obstacles, scroll_offset=self.ground_scroll)
                # Level 1 and Level 2 enemies both use the same update signature
                elif isinstance(enemy, Level1Enemy) or hasattr(enemy, 'scroll_offset'):
                    enemy.update(self.player, dt=dt, obstacles=self.obstacles, scroll_offset=self.ground_scroll)
                else:
                    # Fallback for other enemy types
                    enemy.update(self.player)
            
            # Remove dead enemies
            if hasattr(enemy, 'alive') and not enemy.alive:
                if enemy == self.boss:
                    self.boss_defeated = True
                    self.level_complete = True
                    print("BOSS DEFEATED! Victory!")
                self.enemies.remove(enemy)
        
        # Handle boss summoning minions (hard mode)
        if self.boss and hasattr(self.boss, 'summon_event') and self.boss.summon_event:
            self.spawn_boss_minions(self.boss.summon_event)
            self.boss.summon_event = None
        
        # Update traps
        for trap in self.animated_traps:
            trap.update(self.player, scroll_offset=self.ground_scroll)
        
        # Update powerups
        for powerup in self.powerups[:]:
            if not powerup.collected:
                was_collected = powerup.collected
                powerup.update(self.player, dt=dt, scroll_offset=self.ground_scroll)
                # Check if powerup was just collected
                if not was_collected and powerup.collected:
                    self.mushroom_count += 1
                    print(f"Mushroom collected! Total: {self.mushroom_count}/{self.min_mushrooms_for_boss}")
            else:
                # Keep updating until particles are gone
                powerup.update(self.player, dt=dt, scroll_offset=self.ground_scroll)
                if not powerup.collection_particles:
                    self.powerups.remove(powerup)
        
        # Handle scrolling
        self.handle_scrolling()
        
        # Update particles
        self.update_particles()
        
        # Check if player died
        if self.player.lives <= 0:
            return "game_over"
    
    def spawn_boss_minions(self, summon_event):
        """Spawn minions when boss summons them (hard mode)"""
        from Level2Enemies import Skeleton
        
        count = summon_event.get('count', 2)
        positions = summon_event.get('positions', [])
        
        for i in range(min(count, len(positions))):
            pos_x, pos_y = positions[i]
            minion = Skeleton(pos_x, pos_y)
            minion.level = self
            minion.max_hp = 30  # Weaker minions
            minion.current_hp = 30
            minion.speed = 1.5  # Faster minions
            self.enemies.append(minion)
            self.boss_summoned_minions.append(minion)
            print(f"Boss summoned minion {i+1} at ({pos_x}, {pos_y})")

    def draw(self, surface):
        """Draw boss level with enhanced effects"""
        # Draw background
        self.draw_bg()
        
        # Draw obstacles
        self.update_obstacles()
        
        # Draw tilemap
        self.draw_tilemap()
        
        # Draw traps
        for trap in self.animated_traps:
            surface.blit(trap.image, (trap.rect.x - self.ground_scroll, trap.rect.y))
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(surface, self.ground_scroll)
        
        # Draw enemies (boss will have special effects)
        for enemy in self.enemies:
            enemy.draw(surface)
        
        # Draw player
        self.player.draw(surface)
        
        # Draw particles
        self.update_particles()
        
        # Draw UI elements
        self.update_lives()
        self.draw_mushroom_count()
        self.draw_debug_info()
        
        # Draw boss-specific UI elements
        if self.boss and self.boss.alive:
            self.draw_boss_ui(surface)
        
        # Draw victory message
        if self.level_complete:
            self.draw_victory_message(surface)
    
    def draw_boss_ui(self, surface):
        """Draw boss-specific UI elements"""
        if not self.boss:
            return
        
        # Boss name and difficulty - using pixelated font
        try:
            font = pygame.font.Font("assets/yoster.ttf", 32)
        except:
            font = pygame.font.Font(None, 36)
        boss_name = f"FINAL BOSS - {self.difficulty.upper()} MODE"
        text_surf = font.render(boss_name, True, (255, 215, 0))  # Gold color
        text_rect = text_surf.get_rect(center=(surface.get_width() // 2, 30))
        
        # Text shadow
        shadow_surf = font.render(boss_name, True, (0, 0, 0))
        surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
        surface.blit(text_surf, text_rect)
        
        # Phase indicator
        if hasattr(self.boss, 'phase') and self.boss.phase == 2:
            try:
                phase_font = pygame.font.Font("assets/yoster.ttf", 24)
            except:
                phase_font = pygame.font.Font(None, 28)
            phase_text = phase_font.render("PHASE 2 - ENRAGED", True, (255, 100, 100))
            phase_rect = phase_text.get_rect(center=(surface.get_width() // 2, 60))
            surface.blit(phase_text, phase_rect)
    
    def draw_victory_message(self, surface):
        """Draw victory message when boss is defeated"""
        # Victory background
        victory_surf = pygame.Surface((400, 200), pygame.SRCALPHA)
        victory_surf.fill((0, 0, 0, 180))
        victory_rect = victory_surf.get_rect(center=(surface.get_width() // 2, surface.get_height() // 2))
        surface.blit(victory_surf, victory_rect)
        
        # Victory text - using pixelated font
        try:
            font = pygame.font.Font("assets/yoster.ttf", 48)
        except:
            font = pygame.font.Font(None, 48)
        victory_text = font.render("VICTORY!", True, (255, 215, 0))
        text_rect = victory_text.get_rect(center=victory_rect.center)
        text_rect.y -= 30
        
        # Text glow effect
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_surf = font.render("VICTORY!", True, (255, 255, 100))
            surface.blit(glow_surf, (text_rect.x + offset[0], text_rect.y + offset[1]))
        
        surface.blit(victory_text, text_rect)
        
        # Difficulty completed text
        try:
            diff_font = pygame.font.Font("assets/yoster.ttf", 28)
        except:
            diff_font = pygame.font.Font(None, 32)
        diff_text = diff_font.render(f"{self.difficulty.upper()} MODE COMPLETED", True, (255, 255, 255))
        diff_rect = diff_text.get_rect(center=(victory_rect.centerx, victory_rect.centery + 20))
        surface.blit(diff_text, diff_rect)
    
    def check_win_lose_conditions(self):
        """Check if boss is defeated or player died"""
        if self.boss_defeated:
            return "victory"
        elif self.player.lives <= 0:
            return "game_over"
        return None
    
    def run(self, screen):
        """Run the boss level game loop"""
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
            
            # Clear screen and draw background
            self.screen.fill((0, 0, 0))
            self.draw_bg()
            
            # Update and draw obstacles and tilemap
            self.update_obstacles()
            self.draw_tilemap()
            self.update_particles()
            self.update_enemies()
            
            # Update boss level specific elements
            dt = 1.0
            result = self.update(dt)
            
            # Check for level completion or game over
            if result == "victory":
                return "victory"
            elif result == "game_over":
                return "game_over"
            
            # Draw traps and powerups
            for trap in self.animated_traps:
                self.screen.blit(trap.image, (trap.rect.x - self.ground_scroll, trap.rect.y))
            
            for powerup in self.powerups:
                powerup.draw(self.screen, self.ground_scroll)
            
            # Draw player
            if self.player:
                self.player.draw(self.screen)
            
            # Handle scrolling and UI
            self.handle_scrolling()
            self.update_lives()
            self.draw_mushroom_count()
            self.draw_debug_info()
            
            # Draw boss-specific UI elements
            if self.boss and self.boss.alive:
                self.draw_boss_ui(self.screen)
            
            # Draw victory message
            if self.level_complete:
                self.draw_victory_message(self.screen)
            
            pygame.display.flip()
            self.clock.tick(60)
        
        return "menu"
    
    def draw_mushroom_count(self):
        """Draw mushroom counter on the right side of screen for boss level"""
        # Load mushroom sprite icon
        try:
            mushroom_icon = pygame.image.load("assets/mushroom.png").convert_alpha()
            mushroom_icon = pygame.transform.scale(mushroom_icon, (40, 40))
        except Exception as e:
            print(f"Error loading mushroom icon: {e}")
            # Fallback: create a simple surface
            mushroom_icon = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(mushroom_icon, (220, 80, 80), (20, 20), 18)
        
        # Position on right side of screen
        icon_x = self.WIDTH - 180  # More space for text
        icon_y = 80
        
        # Draw mushroom icon
        self.screen.blit(mushroom_icon, (icon_x, icon_y))
        
        # Draw count text with pixel font
        try:
            font = pygame.font.Font("assets/yoster.ttf", 36)
        except:
            font = pygame.font.Font(None, 48)
        count_text = f"x {self.mushroom_count}"
        text_surf = font.render(count_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(left=icon_x + 40, centery=icon_y + 16)
        
        # Draw text with shadow for readability
        shadow_surf = font.render(count_text, True, (0, 0, 0))
        shadow_rect = text_surf.get_rect(left=icon_x + 42, centery=icon_y + 18)
        self.screen.blit(shadow_surf, shadow_rect)
        self.screen.blit(text_surf, text_rect)

        