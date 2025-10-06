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
from entities import mainCharacter, Enemy, Powerup


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
        
        # AI cycling
        self.ai_types = ["idle", "patrol", "chase", "ranged", "boss"]
        self.current_ai_index = 0
        
        # Entity lists
        self.enemies = []
        self.powerups = []
        self.obstacles = []
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        
        # UI
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        
        # Initialize sandbox
        self.init_sandbox()
        
    def init_sandbox(self):
        """Setup window, background, and player"""
        print("🎮 Initializing Sandbox Mode...")
        
        # Create player
        self.player = mainCharacter(100, 500)
        
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
        
        print("✅ Sandbox initialized successfully!")
    
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
                    spawn_pos = mouse_pos if self.mouse_mode else (self.player.rect.x + 100, 530)
                    self.spawn_enemy(spawn_pos[0], spawn_pos[1])
                
                elif event.key == pygame.K_p:  # Spawn powerup
                    spawn_pos = mouse_pos if self.mouse_mode else (self.player.rect.x + 50, 550)
                    self.spawn_powerup(spawn_pos[0], spawn_pos[1])
                
                elif event.key == pygame.K_d:  # Delete nearest entity
                    self.delete_nearest_entity(mouse_pos if self.mouse_mode else self.player.rect.center)
                
                elif event.key == pygame.K_r:  # Reset sandbox
                    self.reset_sandbox()
                
                # AI and behavior toggles
                elif event.key == pygame.K_TAB:  # Cycle AI behavior
                    self.cycle_ai_behavior()
                
                elif event.key == pygame.K_f:  # Toggle slow motion
                    self.slow_motion = not self.slow_motion
                    print(f"🐌 Slow motion: {'ON' if self.slow_motion else 'OFF'}")
                
                elif event.key == pygame.K_g:  # Toggle gravity
                    self.gravity_enabled = not self.gravity_enabled
                    print(f"🌍 Gravity: {'ON' if self.gravity_enabled else 'OFF'}")
                
                elif event.key == pygame.K_m:  # Toggle mouse mode
                    self.mouse_mode = not self.mouse_mode
                    print(f"🖱️ Mouse spawn mode: {'ON' if self.mouse_mode else 'OFF'}")
                
                # State management
                elif event.key == pygame.K_s:  # Save state
                    filename = f"sandbox_save_{len(os.listdir('.'))}.json"
                    self.save_state(filename)
                    print(f"💾 Saved to {filename}")
                
                elif event.key == pygame.K_l:  # Load state
                    self.load_state("autosave.json")
                    print("📁 Loaded autosave.json")
                
                # Debug toggle
                elif event.key == pygame.K_b:  # Toggle debug mode
                    self.debug_mode = not self.debug_mode
                    print(f"🐛 Debug mode: {'ON' if self.debug_mode else 'OFF'}")
        
        return None
    
    def spawn_enemy(self, x, y):
        """Spawn enemy at specified position"""
        current_ai = self.ai_types[self.current_ai_index]
        enemy = Enemy(x, y, current_ai)
        self.enemies.append(enemy)
        print(f"👹 Spawned {current_ai} enemy at ({x}, {y})")
    
    def spawn_powerup(self, x, y):
        """Spawn powerup at specified position"""
        powerup_types = ["health", "speed", "damage", "shield", "ammo"]
        import random
        powerup_type = random.choice(powerup_types)
        powerup = Powerup(x, y, powerup_type)
        self.powerups.append(powerup)
        print(f"⭐ Spawned {powerup_type} powerup at ({x}, {y})")
    
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
            print(f"🗑️ Deleted enemy at ({nearest_enemy.rect.x}, {nearest_enemy.rect.y})")
        elif nearest_powerup:
            self.powerups.remove(nearest_powerup)
            print(f"🗑️ Deleted powerup at ({nearest_powerup.rect.x}, {nearest_powerup.rect.y})")
    
    def reset_sandbox(self):
        """Reset/clear sandbox"""
        self.enemies.clear()
        self.powerups.clear()
        self.player.rect.x = 100
        self.player.rect.y = 500
        self.player.lives = 10
        print("🔄 Sandbox reset!")
    
    def cycle_ai_behavior(self):
        """Cycle through enemy AI behaviors"""
        self.current_ai_index = (self.current_ai_index + 1) % len(self.ai_types)
        new_ai = self.ai_types[self.current_ai_index]
        
        # Update all existing enemies
        for enemy in self.enemies:
            enemy.set_ai_type(new_ai)
        
        print(f"🧠 AI behavior changed to: {new_ai}")
    
    def update_entities(self, dt):
        """Update all game objects based on delta time"""
        # Apply slow motion
        effective_dt = dt * 0.5 if self.slow_motion else dt
        
        # Set enemies list for weapon collision detection
        self.player.enemies = self.enemies
        
        # Update player (with or without gravity)
        if self.gravity_enabled:
            self.player.update(pygame.key.get_pressed(), self.obstacles)
        else:
            # Manual movement without gravity
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.player.rect.x -= 5 * effective_dt
            if keys[pygame.K_RIGHT]:
                self.player.rect.x += 5 * effective_dt
            if keys[pygame.K_UP]:
                self.player.rect.y -= 5 * effective_dt
            if keys[pygame.K_DOWN]:
                self.player.rect.y += 5 * effective_dt
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update(self.player, effective_dt)
            
            # Check weapon collision with enemies
            if hasattr(self.player, 'projectile_manager'):
                for projectile in self.player.projectile_manager.projectiles[:]:
                    if hasattr(projectile, 'rect') and projectile.rect.colliderect(enemy.rect):
                        enemy.take_damage(20)
                        self.player.projectile_manager.projectiles.remove(projectile)
                        print(f"Player projectile hit enemy for 20 damage!")
            
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
        
        # Draw boundaries
        border_color = (100, 100, 100)
        floor_color = (80, 160, 80)
        
        pygame.draw.rect(self.screen, border_color, (0, 0, 960, 10))  # Top
        pygame.draw.rect(self.screen, floor_color, (0, 580, 960, 60))  # Floor
        pygame.draw.rect(self.screen, border_color, (0, 0, 10, 640))  # Left
        pygame.draw.rect(self.screen, border_color, (950, 0, 10, 640))  # Right
        
        # Draw player
        if self.player.visible:
            self.screen.blit(self.player.image, self.player.rect)
        
        # Draw enemies
        for enemy in self.enemies:
            enemy.draw(self.screen, self.debug_mode)
        
        # Draw powerups
        for powerup in self.powerups:
            powerup.draw(self.screen)
        
        # Draw weapon effects
        if hasattr(self.player, 'draw_weapon_effects'):
            self.player.draw_weapon_effects(self.screen, (0, 0))
        
        # Draw projectiles
        if hasattr(self.player, 'projectile_manager'):
            self.player.projectile_manager.draw(self.screen)
    
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
        status_lines = [
            f"🧠 AI Behavior: {self.ai_types[self.current_ai_index]}",
            f"👹 Enemies: {len(self.enemies)} | ⭐ Powerups: {len(self.powerups)}",
            f"🌍 Gravity: {'ON' if self.gravity_enabled else 'OFF'} | 🐌 Slow-Mo: {'ON' if self.slow_motion else 'OFF'}",
            f"🖱️ Mouse Mode: {'ON' if self.mouse_mode else 'OFF'} | 🐛 Debug: {'ON' if self.debug_mode else 'OFF'}",
            f"❤️ Player Lives: {self.player.lives}",
            "",
            "🎮 SANDBOX CONTROLS:",
            "E - Spawn Enemy | P - Spawn Powerup | D - Delete Nearest",
            "R - Reset | TAB - Cycle AI | F - Slow Motion",
            "G - Toggle Gravity | M - Mouse Mode | B - Debug Mode",
            "S - Save State | L - Load State | ESC - Exit",
            "",
            "⚔️ COMBAT CONTROLS:",
            "A - Melee Attack | W - Straight Projectile | C - Aimed Projectile"
        ]
        
        for i, line in enumerate(status_lines):
            color = (255, 255, 255) if not line.startswith("🎮") else (255, 255, 0)
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
            
            print(f"💾 State saved to {filename}")
            
        except Exception as e:
            print(f"❌ Failed to save state: {e}")
    
    def load_state(self, filename):
        """Load sandbox state from file"""
        try:
            if not os.path.exists(filename):
                print(f"📁 No save file found: {filename}")
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
            
            # Load enemies
            for enemy_data in state.get("enemies", []):
                enemy = Enemy(enemy_data["x"], enemy_data["y"], enemy_data["ai_type"])
                enemy.health = enemy_data.get("health", 100)
                self.enemies.append(enemy)
            
            # Load powerups
            for powerup_data in state.get("powerups", []):
                powerup = Powerup(powerup_data["x"], powerup_data["y"], powerup_data["type"])
                self.powerups.append(powerup)
            
            # Load settings
            settings = state.get("settings", {})
            self.current_ai_index = settings.get("current_ai_index", 0)
            self.gravity_enabled = settings.get("gravity_enabled", True)
            self.debug_mode = settings.get("debug_mode", True)
            
            print(f"📁 State loaded from {filename}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load state: {e}")
            return False
    
    def run(self):
        """Main sandbox loop"""
        print("🚀 Starting Sandbox Mode...")
        
        while self.running:
            self.dt = self.clock.tick(60) / 16.67  # Normalize to 60fps
            
            # Handle input
            result = self.handle_input()
            if result:
                return result
            
            # Update entities
            self.update_entities(self.dt)
            
            # Draw everything
            self.draw_entities()
            self.draw_ui()
            
            pygame.display.flip()
        
        return "quit"


def sandbox_mode():
    """Entry point for sandbox mode"""
    screen = pygame.display.get_surface()
    if not screen:
        screen = pygame.display.set_mode((960, 640))
    
    sandbox = SandboxMode(screen)
    return sandbox.run()