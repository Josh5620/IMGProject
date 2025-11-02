"""
🎮 SANDBOX MODE GENERATOR FOR 2D PLATFORMER GAME
===============================================

A comprehensive testing and debugging playground for developers.
Features enemy AI testing, powerup experimentation, physics toggles,
and state management.
"""

import pygame
import json
import os
import math
import random
import inspect
from entities import mainCharacter
from Level1Enemies import Level1Enemy
from Level2Enemies import MutatedMushroom, Skeleton, FlyingEye
from level2_powerups import Level2Powerup, LEVEL2_POWERUP_TYPES

# Powerup class definition for basic powerups (since it was incomplete in entities.py)
class Powerup:
    """Basic powerup class for sandbox mode"""
    def __init__(self, x, y, powerup_type="health"):
        self.rect = pygame.Rect(x, y, 40, 40)
        self.powerup_type = powerup_type
        self.collected = False
        self.bob_timer = 0
        self.original_y = y
    
    def update(self, player, dt=1.0):
        if self.collected:
            return
        self.bob_timer += dt * 0.15
        self.rect.y = self.original_y + int(math.sin(self.bob_timer) * 8)
        if self.rect.colliderect(player.rect):
            self.collected = True
            if self.powerup_type == "health":
                player.lives = min(player.lives + 1, 3)
            elif self.powerup_type == "speed":
                player.speed_boost = 1.5
            elif self.powerup_type == "ammo":
                player.current_ammo = min(player.current_ammo + 5, player.max_ammo)
    
    def draw(self, surface):
        if not self.collected:
            color = (255, 0, 0) if self.powerup_type == "health" else (0, 255, 0) if self.powerup_type == "speed" else (255, 255, 0)
            pygame.draw.circle(surface, color, self.rect.center, 20)


class SandboxMode:
    """Main sandbox class handling all sandbox functionality"""
    
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Game state
        self.dt = 1.0
        self.slow_motion = False
        self.gravity_enabled = True
        self.mouse_mode = False
        self.debug_mode = True
        self.unlimited_ammo = False
        self.ground_scroll = 0
        
        # AI cycling - Level 1 and Level 2 enemies
        self.level1_ai_types = ["idle", "patrol", "chase", "ranged"]
        self.level2_ai_types = ["basic", "hunter", "stealth", "boss"]
        self.ai_types = self.level1_ai_types  # Start with Level 1
        self.current_ai_index = 0
        self.current_level = 1  # 1 for Level 1, 2 for Level 2
        
        # Entity lists
        self.enemies = []
        self.powerups = []
        self.obstacles = []
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.screen_shake = 0
        self.screen_shake_intensity = 0
        
        # UI
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        
        # Initialize sandbox
        self.init_sandbox()
        
    def init_sandbox(self):
        """Setup window, background, and player"""
        print("Initializing Sandbox Mode...")
        
        # Create player
        self.player = mainCharacter(100, 500)
        self.player.level = self
        
        # Create simple floor obstacle
        class SimpleBlock:
            def __init__(self, x, y, width, height):
                self.rect = pygame.Rect(x, y, width, height)
            
            def get_rect(self):
                return self.rect
            
            def collideHurt(self, player):
                return 0
        
        # Create boundaries
        floor = SimpleBlock(0, 580, 960, 60)
        ceiling = SimpleBlock(0, 0, 960, 10)
        left_wall = SimpleBlock(0, 0, 10, 640)
        right_wall = SimpleBlock(950, 0, 10, 640)
        
        self.obstacles = [floor, ceiling, left_wall, right_wall]
        
        # Try to auto-load last session
        self.load_state("autosave.json")
        
        print("Sandbox initialized successfully!")
    
    def handle_input(self):
        """Process key and mouse inputs"""
        keys = pygame.key.get_pressed()
        mouse_pos = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.save_state("autosave.json")  # Auto-save on exit
                self.running = False
                return "quit"
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.save_state("autosave.json")
                    return "menu"
                
                # Entity spawning
                elif event.key == pygame.K_e:  # Spawn enemy
                    if self.mouse_mode:
                        spawn_pos = mouse_pos
                    else:
                        # Spawn enemy near player on the ground
                        spawn_x = self.player.rect.x + 100  # 100 pixels to the right of player
                        spawn_y = self.player.rect.bottom - 48  # On the ground level
                        spawn_pos = (spawn_x, spawn_y)
                    self.spawn_enemy(spawn_pos[0], spawn_pos[1])
                
                elif event.key == pygame.K_p:  # Spawn powerup
                    if self.mouse_mode:
                        spawn_pos = mouse_pos
                    else:
                        # Spawn powerup near player on the ground
                        spawn_x = self.player.rect.x + 50  # 50 pixels to the right of player
                        spawn_y = self.player.rect.bottom - 32  # On the ground level
                        spawn_pos = (spawn_x, spawn_y)
                    self.spawn_powerup(spawn_pos[0], spawn_pos[1])
                
                elif event.key == pygame.K_d:  # Delete nearest entity
                    self.delete_nearest_entity(mouse_pos if self.mouse_mode else self.player.rect.center)
                
                elif event.key == pygame.K_r:  # Reset sandbox
                    self.reset_sandbox()
                
                # AI and behavior toggles
                elif event.key == pygame.K_TAB:  # Cycle AI behavior
                    self.cycle_ai_behavior()
                
                elif event.key == pygame.K_1:  # Switch to Level 1
                    self.switch_level(1)
                
                elif event.key == pygame.K_2:  # Switch to Level 2
                    self.switch_level(2)
                
                
                elif event.key == pygame.K_f:  # Toggle slow motion
                    self.slow_motion = not self.slow_motion
                    print(f"Slow motion: {'ON' if self.slow_motion else 'OFF'}")
                
                elif event.key == pygame.K_g:  # Toggle gravity
                    self.gravity_enabled = not self.gravity_enabled
                    print(f"Gravity: {'ON' if self.gravity_enabled else 'OFF'}")
                
                elif event.key == pygame.K_m:  # Toggle mouse mode
                    self.mouse_mode = not self.mouse_mode
                    print(f"Mouse spawn mode: {'ON' if self.mouse_mode else 'OFF'}")
                
                # State management
                elif event.key == pygame.K_l:  # Save state
                    filename = f"sandbox_save_{len(os.listdir('.'))}.json"
                    self.save_state(filename)
                    print(f"Saved to {filename}")
                
                elif event.key == pygame.K_k:  # Load state
                    self.load_state("autosave.json")
                    print("Loaded autosave.json")
                
                elif event.key == pygame.K_u:  # Toggle unlimited ammo
                    self.unlimited_ammo = not self.unlimited_ammo
                    print(f"Unlimited ammo: {'ON' if self.unlimited_ammo else 'OFF'}")
                    if self.unlimited_ammo:
                        # Set ammo to max when enabling unlimited ammo
                        self.player.current_ammo = self.player.max_ammo
                
                # Debug toggle
                elif event.key == pygame.K_b:  # Toggle debug mode
                    self.debug_mode = not self.debug_mode
                    print(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        
        return None
    
    def spawn_enemy(self, x, y):
        """Spawn enemy at specified position"""
        current_ai = self.ai_types[self.current_ai_index]
        
        if self.current_level == 1:
            # Level 1 enemies
            enemy = Level1Enemy(x, y)
            enemy.ai_type = current_ai
            enemy.level = 1  # Add level attribute
            print(f"Spawned Level 1 {current_ai} enemy at ({x}, {y})")
        else:
            # Level 2 - NEW ENEMIES from entities.py
            if current_ai == "basic":
                # Spawn one of the 3 new enemies randomly
                enemy_type = random.choice(["mushroom", "skeleton", "flying"])
                if enemy_type == "mushroom":
                    enemy = MutatedMushroom(x, y)
                elif enemy_type == "skeleton":
                    enemy = Skeleton(x, y)
                elif enemy_type == "flying":
                    enemy = FlyingEye(x, y)
                else:
                    enemy = MutatedMushroom(x, y)  # Default
            elif current_ai == "hunter":
                # Hunter is also one of the 3 new enemies
                enemy = random.choice([MutatedMushroom(x, y), Skeleton(x, y), FlyingEye(x, y)])
            elif current_ai == "stealth":
                # Stealth is also one of the 3 new enemies
                enemy = random.choice([MutatedMushroom(x, y), Skeleton(x, y), FlyingEye(x, y)])
            elif current_ai == "boss":
                # Boss enemies removed - use random Level 2 enemy instead
                enemy = random.choice([MutatedMushroom(x, y), Skeleton(x, y), FlyingEye(x, y)])
            else:
                # Default to one of the 3 new enemies
                enemy = random.choice([MutatedMushroom(x, y), Skeleton(x, y), FlyingEye(x, y)])
            
            enemy.level = 2  # Add level attribute
            print(f"Spawned Level 2 {current_ai} enemy at ({x}, {y})")
        
        self.enemies.append(enemy)
    
    def switch_level(self, level):
        """Switch between Level 1 and Level 2 enemies"""
        self.current_level = level
        print(f"Switched to Level {level}")
        
        # Clear existing enemies
        self.enemies.clear()
        
        # Update AI types based on level
        if level == 1:
            self.ai_types = self.level1_ai_types
        else:
            self.ai_types = self.level2_ai_types
        
        self.current_ai_index = 0
        print(f"Available AI types: {', '.join(self.ai_types)}")
    
    def spawn_powerup(self, x, y):
        """Spawn powerup at specified position"""
        import random
        
        if self.current_level == 2:
            # Level 2 powerups - enhanced red riding hood themed
            powerup_type = random.choice(LEVEL2_POWERUP_TYPES)
            powerup = Level2Powerup(x, y, powerup_type)
            print(f"Spawned Level 2 {powerup_type} powerup at ({x}, {y})")
        else:
            # Level 1 powerups - standard
            powerup_types = ["health", "speed", "damage", "shield", "ammo"]
            powerup_type = random.choice(powerup_types)
            powerup = Powerup(x, y, powerup_type)
            print(f"Spawned {powerup_type} powerup at ({x}, {y})")
        
        self.powerups.append(powerup)
    
    def delete_nearest_entity(self, pos):
        """Delete nearest entity to specified position"""
        nearest_enemy = None
        nearest_powerup = None
        min_enemy_dist = float('inf')
        min_powerup_dist = float('inf')
        
        # Find nearest enemy
        for enemy in self.enemies:
            dist = math.sqrt((enemy.rect.centerx - pos[0])**2 + (enemy.rect.centery - pos[1])**2)
            if dist < min_enemy_dist:
                min_enemy_dist = dist
                nearest_enemy = enemy
        
        # Find nearest powerup
        for powerup in self.powerups:
            dist = math.sqrt((powerup.rect.centerx - pos[0])**2 + (powerup.rect.centery - pos[1])**2)
            if dist < min_powerup_dist:
                min_powerup_dist = dist
                nearest_powerup = powerup
        
        # Delete the nearest overall
        if min_enemy_dist < min_powerup_dist and nearest_enemy:
            self.enemies.remove(nearest_enemy)
            print(f"Deleted enemy at ({nearest_enemy.rect.x}, {nearest_enemy.rect.y})")
        elif nearest_powerup:
            self.powerups.remove(nearest_powerup)
            print(f"Deleted powerup at ({nearest_powerup.rect.x}, {nearest_powerup.rect.y})")
    
    def reset_sandbox(self):
        """Reset/clear sandbox"""
        self.enemies.clear()
        self.powerups.clear()
        self.player.rect.x = 100
        self.player.rect.y = 500
        self.player.lives = 10
        print("Sandbox reset!")
    
    def cycle_ai_behavior(self):
        """Cycle through enemy AI behaviors"""
        self.current_ai_index = (self.current_ai_index + 1) % len(self.ai_types)
        new_ai = self.ai_types[self.current_ai_index]
        
        # Update all existing enemies
        for enemy in self.enemies:
            if hasattr(enemy, 'ai_type'):
                enemy.ai_type = new_ai
        
        print(f"AI behavior changed to: {new_ai} (Level {self.current_level})")
    
    def update_entities(self, dt):
        """Update all game objects based on delta time"""
        # Apply slow motion
        effective_dt = dt * 0.5 if self.slow_motion else dt
        
        # Set enemies list for weapon collision detection
        self.player.enemies = self.enemies
        
        # Get keys for all updates
        keys = pygame.key.get_pressed()
        
        # Update player (with or without gravity)
        # Pass current level for Level 2 features
        self.player.current_level = self.current_level
        if self.gravity_enabled:
            self.player.update(keys, self.obstacles, self.enemies)
        else:
            # Manual movement without gravity
            if keys[pygame.K_LEFT]:
                self.player.rect.x -= 5 * effective_dt
            if keys[pygame.K_RIGHT]:
                self.player.rect.x += 5 * effective_dt
            if keys[pygame.K_UP]:
                self.player.rect.y -= 5 * effective_dt
            if keys[pygame.K_DOWN]:
                self.player.rect.y += 5 * effective_dt
        
        # Handle unlimited ammo
        if self.unlimited_ammo:
            self.player.current_ammo = self.player.max_ammo
        
        # Update enemies
        for enemy in self.enemies[:]:
            if hasattr(enemy, 'level') and enemy.level == 2:  # Level 2 enemies
                # Check if enemy is from entities.py (has obstacles parameter in update)
                sig = inspect.signature(enemy.update)
                if len(sig.parameters) >= 4:  # Has obstacles parameter
                    enemy.update(self.player, effective_dt, self.obstacles)
                else:
                    enemy.update(self.player, effective_dt)
            else:  # Level 1 enemies
                enemy.update(self.player, effective_dt)
            
            # Check weapon collision with enemies
            if hasattr(self.player, 'projectile_manager'):
                for projectile in self.player.projectile_manager.projectiles[:]:
                    if projectile.active and projectile.get_rect().colliderect(enemy.rect):
                        if hasattr(enemy, 'level'):  # Level 2 enemies
                            damage = 20 if enemy.level == 1 else 15  # More damage to Level 2
                        else:  # Level 1 enemies
                            damage = 20
                        
                        enemy.take_damage(damage)
                        self.player.projectile_manager.projectiles.remove(projectile)
                        print(f"Player projectile hit Level {getattr(enemy, 'level', 1)} enemy for {damage} damage!")
            
            # Check enemy projectiles hitting player (Level 2 special attacks)
            if hasattr(enemy, 'bone_projectiles'):  # Skeleton bones
                for bone in enemy.bone_projectiles[:]:
                    bone_rect = pygame.Rect(bone['x'] - 5, bone['y'] - 5, 10, 10)
                    if bone_rect.colliderect(self.player.rect):
                        self.player.take_damage(2)
                        enemy.bone_projectiles.remove(bone)
                        print("Hit by bone!")
                        break
            
            if hasattr(enemy, 'poison_clouds'):  # Mutated Mushroom poison
                # Only check if player hasn't been damaged recently by this cloud
                if not hasattr(self.player, 'last_poison_damage_time'):
                    self.player.last_poison_damage_time = 0
                
                current_time = pygame.time.get_ticks()
                for cloud in enemy.poison_clouds:
                    cloud_rect = pygame.Rect(cloud['x'] - cloud['radius'], cloud['y'] - cloud['radius'], 
                                            cloud['radius'] * 2, cloud['radius'] * 2)
                    # Only damage every 500ms (50 frames) to avoid massive damage
                    if cloud_rect.colliderect(self.player.rect) and current_time - self.player.last_poison_damage_time > 500:
                        self.player.take_damage(1)
                        self.player.last_poison_damage_time = current_time
                        print("Poisoned by cloud!")
                        break
            
            if not enemy.alive:
                self.enemies.remove(enemy)
        
        # Update powerups
        for powerup in self.powerups[:]:
            powerup.update(self.player, effective_dt)
            if powerup.collected:
                self.powerups.remove(powerup)
    
    def draw_entities(self):
        """Draw all current entities"""
        # Clear screen
        self.screen.fill((50, 100, 150))  # Blue sky
        
        # Apply screen shake
        shake_x = 0
        shake_y = 0
        if self.screen_shake > 0:
            import random
            shake_x = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
            shake_y = random.randint(-self.screen_shake_intensity, self.screen_shake_intensity)
        
        # Draw boundaries
        border_color = (100, 100, 100)
        floor_color = (80, 160, 80)
        
        pygame.draw.rect(self.screen, border_color, (0, 0, 960, 10))  # Top
        pygame.draw.rect(self.screen, floor_color, (0, 580, 960, 60))  # Floor
        pygame.draw.rect(self.screen, border_color, (0, 0, 10, 640))  # Left
        pygame.draw.rect(self.screen, border_color, (950, 0, 10, 640))  # Right
        
        # Draw player with powerup effects
        if self.player.visible:
            # Apply shake to player
            original_x = self.player.rect.x
            original_y = self.player.rect.y
            self.player.rect.x += shake_x
            self.player.rect.y += shake_y
            
            self.draw_player_with_effects()
            self.draw_player_health_bar()
            
            # Restore original position
            self.player.rect.x = original_x
            self.player.rect.y = original_y
        
        # Draw enemies
        for enemy in self.enemies:
            # Apply shake to enemies
            original_x = enemy.rect.x
            original_y = enemy.rect.y
            enemy.rect.x += shake_x
            enemy.rect.y += shake_y
            
            enemy.draw(self.screen)
            
            # Restore original position
            enemy.rect.x = original_x
            enemy.rect.y = original_y
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        # Draw weapon effects
        if hasattr(self.player, 'draw_weapon_effects'):
            self.player.draw_weapon_effects(self.screen, (0, 0))
        
        # Draw projectiles
        if hasattr(self.player, 'projectile_manager'):
            self.player.projectile_manager.draw(self.screen)
    
    def draw_player_with_effects(self):
        """Draw player with enhanced powerup visual effects"""
        self.player.draw_with_effects(self.screen)
    
    def draw_player_health_bar(self):
        """Draw player health bar above the cat"""
        if not hasattr(self.player, 'lives'):
            return
            
        # Health bar dimensions
        bar_width = 60
        bar_height = 8
        bar_x = self.player.rect.x + (self.player.rect.width - bar_width) // 2
        bar_y = self.player.rect.y - 15
        
        # Background
        pygame.draw.rect(self.screen, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Health
        max_lives = 10  # Assuming max lives is 10
        health_width = int((self.player.lives / max_lives) * bar_width)
        health_color = (0, 255, 0) if self.player.lives > max_lives * 0.5 else (255, 255, 0) if self.player.lives > max_lives * 0.25 else (255, 0, 0)
        pygame.draw.rect(self.screen, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Health text
        font = pygame.font.Font(None, 16)
        health_text = font.render(f"Cat: {self.player.lives}/{max_lives}", True, (255, 255, 255))
        self.screen.blit(health_text, (bar_x, bar_y - 18))
    
    def add_screen_shake(self, intensity, duration):
        """Add screen shake effect"""
        self.screen_shake = duration
        self.screen_shake_intensity = intensity
    
    def update_screen_shake(self, dt):
        """Update screen shake effect"""
        if self.screen_shake > 0:
            self.screen_shake -= dt
            if self.screen_shake <= 0:
                self.screen_shake = 0
                self.screen_shake_intensity = 0
    
    def draw_ui(self):
        """Render on-screen debug info and controls"""
        y_offset = 10
        line_height = 25
        
        # Background for UI
        ui_bg = pygame.Surface((400, 300))
        ui_bg.set_alpha(180)
        ui_bg.fill((0, 0, 0))
        self.screen.blit(ui_bg, (10, 10))
        
        # Current status
        combo_text = ""
        dash_text = ""
        if self.current_level == 2:
            # Level 2 features
            combo_text = f" | Combo: {self.player.combo_count}x ({self.player.combo_timer//60}s left)"
            dash_status = "READY" if self.player.dash_cooldown <= 0 else f"{self.player.dash_cooldown//60}s"
            dash_text = f" | Dash: {dash_status}"
        
        status_lines = [
            f"Level: {self.current_level} | AI: {self.ai_types[self.current_ai_index]} {'[L2 POWERUPS]' if self.current_level == 2 else ''}",
            f"Enemies: {len(self.enemies)} | Powerups: {len(self.powerups)}{combo_text}",
            f"Gravity: {'ON' if self.gravity_enabled else 'OFF'} | Slow-Mo: {'ON' if self.slow_motion else 'OFF'}{dash_text}",
            f"Mouse Mode: {'ON' if self.mouse_mode else 'OFF'} | Debug: {'ON' if self.debug_mode else 'OFF'}",
            f"Player Lives: {self.player.lives} | Ammo: {'∞' if self.unlimited_ammo else f'{self.player.current_ammo}/{self.player.max_ammo}'}",
            f"Score: {self.player.total_score} | Multiplier: {self.player.score_multiplier:.1f}x",
            self.get_powerup_status_text(),
            "",
            "SANDBOX CONTROLS:",
            "E - Spawn Enemy | P - Spawn Powerup | D - Delete Nearest",
            "1/2 - Switch Level | TAB - Cycle AI | F - Slow Motion",
            "G - Toggle Gravity | M - Mouse Mode | B - Debug Mode",
            "U - Unlimited Ammo | L - Save State | K - Load State | ESC - Exit",
            "",
            "COMBAT CONTROLS:",
            "A - Melee Attack | S - Straight Projectile | C - Aimed Projectile",
            "UP - Jump | SPACE - Double Jump",
            "SHIFT - Dash (Level 2 only)" if self.current_level == 2 else ""
        ]
        
        for i, line in enumerate(status_lines):
            color = (255, 255, 255) if not line.startswith("SANDBOX") else (255, 255, 0)
            text = self.small_font.render(line, True, color)
            self.screen.blit(text, (20, y_offset + i * (line_height - 5)))
        
        # FPS counter
        fps = self.clock.get_fps()
        fps_text = self.small_font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
        self.screen.blit(fps_text, (850, 10))
        
        # Mouse position in mouse mode
        if self.mouse_mode:
            mouse_pos = pygame.mouse.get_pos()
            mouse_text = self.small_font.render(f"Mouse: ({mouse_pos[0]}, {mouse_pos[1]})", True, (255, 255, 0))
            self.screen.blit(mouse_text, (850, 35))
    
    def get_powerup_status_text(self):
        """Get formatted text showing active powerup status"""
        status_parts = []
        
        if hasattr(self.player, 'powerup_timers'):
            for effect, timer in self.player.powerup_timers.items():
                if timer > 0:
                    seconds_left = timer // 60  # Assuming 60 FPS
                    if effect == "speed" and getattr(self.player, 'speed_boost', 1.0) > 1.0:
                        status_parts.append(f"Speed({seconds_left}s)")
                    elif effect == "damage" and getattr(self.player, 'damage_boost', 1.0) > 1.0:
                        status_parts.append(f"Damage({seconds_left}s)")
                    elif effect == "shield" and getattr(self.player, 'shield_active', False):
                        status_parts.append(f"Shield({seconds_left}s)")
                    elif effect == "invincibility" and getattr(self.player, 'invulnerable', False):
                        status_parts.append(f"Invincible({seconds_left}s)")
        
        if status_parts:
            return "Active Powerups: " + " | ".join(status_parts)
        else:
            return "No active powerups"
        
        # Active powerup effects display
        powerup_y = 60
        for effect, timer in self.player.powerup_timers.items():
            if timer > 0:
                time_left = timer / 60
                effect_colors = {"speed": (0, 255, 0), "damage": (255, 255, 0), "shield": (0, 0, 255)}
                color = effect_colors.get(effect, (255, 255, 255))
                effect_text = self.small_font.render(f"{effect.title()}: {time_left:.1f}s", True, color)
                self.screen.blit(effect_text, (850, powerup_y))
                powerup_y += 20
    
    def save_state(self, filename):
        """Save sandbox setup to JSON"""
        try:
            state = {
                "player": {
                    "x": self.player.rect.x,
                    "y": self.player.rect.y,
                    "lives": self.player.lives
                },
                "enemies": [
                    {
                        "x": enemy.rect.x,
                        "y": enemy.rect.y,
                        "ai_type": enemy.ai_type,
                        "health": enemy.health,
                        "projectiles": len(enemy.projectiles)  # Just count for now
                    }
                    for enemy in self.enemies
                ],
                "powerups": [
                    {
                        "x": powerup.rect.x,
                        "y": powerup.rect.y,
                        "type": powerup.powerup_type
                    }
                    for powerup in self.powerups
                ],
                "settings": {
                    "current_ai_index": self.current_ai_index,
                    "gravity_enabled": self.gravity_enabled,
                    "debug_mode": self.debug_mode
                }
            }
            
            with open(filename, 'w') as f:
                json.dump(state, f, indent=2)
            
            print(f"State saved to {filename}")
            
        except Exception as e:
            print(f"Failed to save state: {e}")
    
    def load_state(self, filename):
        """Load sandbox state from file"""
        try:
            if not os.path.exists(filename):
                print(f"No save file found: {filename}")
                return False
            
            with open(filename, 'r') as f:
                state = json.load(f)
            
            # Clear current state
            self.enemies.clear()
            self.powerups.clear()
            
            # Load player
            if "player" in state:
                self.player.rect.x = state["player"]["x"]
                self.player.rect.y = state["player"]["y"]
                self.player.lives = state["player"]["lives"]
            
            # # Load enemies
            # for enemy_data in state.get("enemies", []):
            #     enemy = Enemy(enemy_data["x"], enemy_data["y"], enemy_data["ai_type"])
            #     enemy.health = enemy_data.get("health", 100)
            #     self.enemies.append(enemy)
            
            # Load powerups
            for powerup_data in state.get("powerups", []):
                powerup_type = powerup_data["type"]
                # Check if it's a Level 2 powerup type
                if powerup_type in LEVEL2_POWERUP_TYPES:
                    powerup = Level2Powerup(powerup_data["x"], powerup_data["y"], powerup_type)
                else:
                    powerup = Powerup(powerup_data["x"], powerup_data["y"], powerup_type)
                self.powerups.append(powerup)
            
            # Load settings
            settings = state.get("settings", {})
            self.current_ai_index = settings.get("current_ai_index", 0)
            self.gravity_enabled = settings.get("gravity_enabled", True)
            self.debug_mode = settings.get("debug_mode", True)
            
            print(f"State loaded from {filename}")
            return True
            
        except Exception as e:
            print(f"Failed to load state: {e}")
            return False
    
    def run(self):
        """Main sandbox loop"""
        print("Starting Sandbox Mode...")
        
        while self.running:
            self.dt = self.clock.tick(60) / 16.67  # Normalize to 60fps
            
            # Handle input
            result = self.handle_input()
            if result:
                return result
            
            # Update entities
            self.update_entities(self.dt)
            
            # Update screen shake
            self.update_screen_shake(self.dt)
            
            # Draw everything
            self.draw_entities()
            self.draw_ui()
            
            pygame.display.flip()
        
        return "quit"


def sandbox_mode(screen=None):
    """Entry point for sandbox mode"""
    if not screen:
        screen = pygame.display.get_surface()
        if not screen:
            screen = pygame.display.set_mode((960, 640))
    
    sandbox = SandboxMode(screen)
    return sandbox.run()


if __name__ == "__main__":
    """Run sandbox mode directly"""
    pygame.init()
    screen = pygame.display.set_mode((960, 640))
    pygame.display.set_caption("Sandbox Mode - AI Enemy Testing")
    
    sandbox = SandboxMode(screen)
    result = sandbox.run()
    
    pygame.quit()
    print(f"Sandbox mode ended with result: {result}")