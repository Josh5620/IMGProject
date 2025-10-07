import pygame
import math
import random
from weapons.projectiles import ProjectileManager, EnemyProjectile, ChargedProjectile


class Level2Enemy:
    
    def __init__(self, x, y, width=48, height=48):
        # Main
        self.rect        = pygame.Rect(x, y, width, height)
        self.original_x  = x
        self.original_y  = y
        self.name        = "Level2Enemy"

        # Lifecycle and visibility
        self.alive       = True
        self.visible     = True
        
        # Try to load enemy sprite, fallback to colored rectangle
        try:
            self.image = pygame.image.load('assets/enemy2.png').convert_alpha()
            self.image = pygame.transform.scale(self.image, (width, height))
            print("Loaded enemy2.png sprite")
        except (pygame.error, FileNotFoundError):
            # Fallback to colored rectangle if sprite not found
            self.image = pygame.Surface((width, height))
            self.image.fill((255, 50, 50))  # Darker red for Level 2
            print("enemy2.png not found, using colored rectangle")

        # Movement and physics (BOSS LEVEL - Much harder!)
        self.speed       = 4.5  # Much faster than Level 1
        self.direction   = 1
        self.facing_right = (self.direction > 0)
        self.y_velocity  = 0
        self.gravity     = 0.7  # Higher gravity for more aggressive movement
        self.on_ground   = False
        self.isIdle = False
        self.player_world_rect = None
        
        # BOSS jumping capabilities - Much more aggressive
        self.jump_power = 12.0  # Higher jump than Level 1
        self.can_jump = True
        self.jump_cooldown = 0
        self.max_jump_cooldown = 20  # Shorter cooldown for boss
        self.jump_timer = 0
        self.double_jump = True  # Boss can double jump
        self.double_jump_used = False

        # BOSS AI state - More complex and aggressive
        self.ai_state    = "idle"
        self.ai_timer    = 0
        self.last_known_player_pos = None
        self.player_visible = False
        self.search_timer = 0
        self.rage_mode = False  # Boss gets more aggressive when low health
        self.attack_pattern = 0  # Different attack patterns
        self.pattern_timer = 0

        # Patrol configuration (more complex)
        self.patrol_start = x
        self.patrol_range = 200  # Larger patrol range
        self.patrol_points = []
        self.current_patrol_target = 0
        self._generate_patrol_points()

        # BOSS sight cone settings - Much more aggressive
        self.sight_range  = 350  # Much better vision
        self.sight_width  = 120  # Much wider field of view
        self.sight_color = (255, 0, 0, 150)  # Red for boss level
        self.player_spotted = False

        # Debug
        self.debug_mode = True

        # BOSS attack setup - Much more dangerous
        self.attack_range     = pygame.Vector2(100, 100)   # Even larger attack range
        self.player_in_attack = False
        self.attack_cooldown  = 0
        self.attack_damage    = 5  # Much more damage than Level 1
        self.combo_attacks = 0  # Combo attack counter
        self.max_combo = 5  # More combo attacks
        self.attack_knockback = 15  # Knockback force
        
        # Attack visual feedback
        self.attacking = False
        self.attack_animation_timer = 0
        self.attack_flash_until = 0
        self.attack_flash_time = 1000  # 1 second flash
        
        # Particle effects
        self.particles = []

        # Projectile system
        self.projectile_manager = ProjectileManager()
        self.projectile_cooldown = 0
        self.can_shoot = True

        # BOSS health system - Much more health
        self.health = 500  # Even more health for a real boss
        self.max_health = 500
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.health_thresholds = [0.8, 0.6, 0.4, 0.2]  # More phase changes
        self.current_phase = 1
        self.phase_transition = False
        self.phase_transition_timer = 0

        # BOSS special abilities - More powerful
        self.special_ability_cooldown = 0
        self.ability_type = random.choice(["dash", "multi_shot", "shield", "teleport", "summon", "berserker", "charge"])
        self.teleport_cooldown = 0
        self.summon_cooldown = 0
        self.berserker_mode = False
        self.berserker_timer = 0
        self.charge_attack_timer = 0
        self.charging = False
        
        # Advanced learning system for boss
        self.player_patterns = []
        self.prediction_accuracy = 0.7  # Better prediction
        self.adaptation_level = 0
        self.learned_attacks = []  # Track what attacks work
        self.player_dodge_patterns = []  # Learn player dodge patterns
        

    def _generate_patrol_points(self):
        """Generate multiple patrol points for more complex patrolling"""
        for i in range(3):
            angle = (i * 120) * math.pi / 180
            px = self.original_x + math.cos(angle) * self.patrol_range
            py = self.original_y + math.sin(angle) * self.patrol_range
            self.patrol_points.append((px, py))

    def update(self, player, obstacles, dt=1.0):
        """Main update loop with advanced AI"""
        if not self.alive:
            return

        # Update timers
        self.ai_timer += dt
        self.attack_cooldown = max(0, self.attack_cooldown - dt)
        self.projectile_cooldown = max(0, self.projectile_cooldown - dt)
        self.special_ability_cooldown = max(0, self.special_ability_cooldown - dt)
        self.invulnerable_timer = max(0, self.invulnerable_timer - dt)
        self.jump_cooldown = max(0, self.jump_cooldown - dt)
        
        # Update particles
        self._update_particles(dt)
        self.jump_timer += dt

        # Update invulnerability
        if self.invulnerable_timer <= 0:
            self.invulnerable = False

        # Store player world position
        if player:
            self.player_world_rect = player.rect.copy()

        # Advanced AI decision making
        self._update_ai_state(player, obstacles)
        self._execute_ai_behavior(player, obstacles, dt)

        # Update projectiles
        self.projectile_manager.update()

        # Apply physics
        self._apply_physics(obstacles, dt)

        # Update special abilities
        self._update_special_abilities(player, dt)

    def _update_ai_state(self, player, obstacles):
        """BOSS AI state management - Much more aggressive and intelligent"""
        if not player:
            return

        # Update boss phase based on health
        self._update_boss_phase()

        distance_to_player = self._get_distance_to_player(player)
        can_see_player = self._can_see_player(player, obstacles)

        # Update player visibility and learning
        if can_see_player:
            self.player_visible = True
            self.last_known_player_pos = (player.rect.centerx, player.rect.centery)
            self.search_timer = 0
            
            # Learn from player movement
            self._learn_from_player(player)
        else:
            self.player_visible = False

        # BOSS state transitions - Much more aggressive
        if can_see_player:
            if distance_to_player <= self.attack_range.length():
                # In attack range - choose attack pattern
                self.ai_state = "attack"
                self._choose_attack_pattern(player)
            elif distance_to_player <= self.sight_range:
                # In sight range - aggressive chase
                self.ai_state = "chase"
                if self.rage_mode:
                    self.ai_state = "rage_chase"  # Special rage mode
            else:
                # Far away - use special abilities
                self.ai_state = "hunt"
        else:
            # Player not visible - use advanced search
            if self.ai_state == "chase" and self.last_known_player_pos:
                self.ai_state = "search"
            elif self.ai_state == "search" and self.search_timer > 180:  # Shorter search time
                self.ai_state = "patrol"
            elif self.ai_state == "idle" and self.ai_timer > 60:  # Shorter idle time
                self.ai_state = "patrol"

    def _execute_ai_behavior(self, player, obstacles, dt):
        """Execute current AI behavior - BOSS level behaviors"""
        if self.ai_state == "idle":
            self._behavior_idle(player, dt)
        elif self.ai_state == "patrol":
            self._behavior_patrol(player, obstacles, dt)
        elif self.ai_state == "chase":
            self._behavior_chase(player, obstacles, dt)
        elif self.ai_state == "rage_chase":
            self._behavior_rage_chase(player, obstacles, dt)
        elif self.ai_state == "hunt":
            self._behavior_hunt(player, obstacles, dt)
        elif self.ai_state == "attack":
            self._behavior_attack(player, obstacles, dt)
        elif self.ai_state == "search":
            self._behavior_search(player, obstacles, dt)

    def _update_boss_phase(self):
        """Update boss phase based on health with transition effects"""
        health_percentage = self.health / self.max_health
        old_phase = self.current_phase
        
        if health_percentage > self.health_thresholds[0]:
            self.current_phase = 1
            self.rage_mode = False
        elif health_percentage > self.health_thresholds[1]:
            self.current_phase = 2
            self.rage_mode = False
        elif health_percentage > self.health_thresholds[2]:
            self.current_phase = 3
            self.rage_mode = True
        elif health_percentage > self.health_thresholds[3]:
            self.current_phase = 4
            self.rage_mode = True
        else:
            self.current_phase = 5  # Final desperate phase
            self.rage_mode = True
        
        # Phase transition effects
        if old_phase != self.current_phase:
            self.phase_transition = True
            self.phase_transition_timer = 120  # 2 seconds of transition
            print(f"BOSS PHASE TRANSITION! Entering Phase {self.current_phase}!")
            
            if self.current_phase >= 3:
                print("BOSS IS ENRAGED! Attacks are now faster and more powerful!")
            if self.current_phase == 5:
                print("BOSS IS IN FINAL DESPERATE PHASE! All attacks are devastating!")

    def _learn_from_player(self, player):
        """Learn from player movement patterns"""
        if hasattr(player, 'scroll_speed'):
            self.player_patterns.append({
                'x': player.rect.centerx,
                'y': player.rect.centery,
                'speed': player.scroll_speed,
                'time': pygame.time.get_ticks()
            })
            
            # Keep only recent patterns
            if len(self.player_patterns) > 100:
                self.player_patterns.pop(0)

    def _choose_attack_pattern(self, player):
        """Choose attack pattern based on boss phase and player behavior"""
        if self.current_phase == 1:
            self.attack_pattern = random.choice([0, 1])  # Basic attacks
        elif self.current_phase == 2:
            self.attack_pattern = random.choice([0, 1, 2, 5])  # Add combo and ground slam
        elif self.current_phase == 3:
            self.attack_pattern = random.choice([1, 2, 3, 5])  # More aggressive
        else:  # Phase 4 - Desperate
            self.attack_pattern = random.choice([2, 3, 4, 5])  # Most dangerous including ground slam

    def _behavior_rage_chase(self, player, obstacles, dt):
        """Rage mode chase - Much faster and more aggressive"""
        if not self.player_visible and self.last_known_player_pos:
            target_x, target_y = self.last_known_player_pos
        else:
            target_x, target_y = player.rect.centerx, player.rect.centery

        # Predict player movement more aggressively
        if hasattr(player, 'scroll_speed'):
            predicted_x = target_x + player.scroll_speed * 60  # Predict 1 second ahead
            target_x = predicted_x

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery

        # More aggressive jumping in rage mode
        if (self.on_ground and self.jump_cooldown <= 0 and 
            dy < -30):  # Jump even for smaller height differences
            self.jump()
        elif (not self.on_ground and self.double_jump and not self.double_jump_used and 
              dy < -20):  # More aggressive double jump
            self.double_jump_attack()
        
        if abs(dx) > 5:
            if dx > 0:
                self.direction = 1
                self.facing_right = True
            else:
                self.direction = -1
                self.facing_right = False
            
            # Much faster movement in rage mode
            self.rect.x += self.direction * self.speed * 1.5 * dt

    def _behavior_hunt(self, player, obstacles, dt):
        """Hunt behavior - Use special abilities to find player"""
        if self.ability_type == "teleport" and self.teleport_cooldown <= 0:
            self._teleport_to_player(player)
        elif self.ability_type == "summon" and self.summon_cooldown <= 0:
            self._summon_minions(player)
        else:
            # Regular chase but with special abilities
            self._behavior_chase(player, obstacles, dt)

    def _behavior_idle(self, player, dt):
        """Idle behavior with occasional movement"""
        if self.ai_timer > 180:  # 3 seconds
            self.direction *= -1
            self.ai_timer = 0

    def _behavior_patrol(self, player, obstacles, dt):
        """Advanced patrol behavior using multiple waypoints"""
        if not self.patrol_points:
            return

        target_x, target_y = self.patrol_points[self.current_patrol_target]
        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery
        distance = math.sqrt(dx*dx + dy*dy)

        if distance < 20:  # Close to waypoint
            self.current_patrol_target = (self.current_patrol_target + 1) % len(self.patrol_points)
        else:
            # Move towards current waypoint
            if dx > 0:
                self.direction = 1
                self.facing_right = True
            else:
                self.direction = -1
                self.facing_right = False
            
            self.rect.x += self.direction * self.speed * dt

    def _behavior_chase(self, player, obstacles, dt):
        """Chase behavior with pathfinding and prediction"""
        if not self.player_visible and self.last_known_player_pos:
            target_x, target_y = self.last_known_player_pos
        else:
            target_x, target_y = player.rect.centerx, player.rect.centery

        # Simple prediction based on player movement
        if hasattr(player, 'scroll_speed'):
            predicted_x = target_x + player.scroll_speed * 30  # Predict 0.5 seconds ahead
            target_x = predicted_x

        dx = target_x - self.rect.centerx
        dy = target_y - self.rect.centery

        # Jump to reach player if they're above
        if (self.on_ground and self.jump_cooldown <= 0 and 
            dy < -50):  # Player is significantly above
            self.jump()
        elif (not self.on_ground and self.double_jump and not self.double_jump_used and 
              dy < -30):  # Double jump if player is still above
            self.double_jump_attack()

        if abs(dx) > 5:  # Only move if not too close
            if dx > 0:
                self.direction = 1
                self.facing_right = True
            else:
                self.direction = -1
                self.facing_right = False
            
            self.rect.x += self.direction * self.speed * dt

    def _behavior_attack(self, player, obstacles, dt):
        """BOSS attack behavior - Much more dangerous and varied"""
        if self.attack_cooldown <= 0:
            # Execute attack pattern based on boss phase
            if self.attack_pattern == 0:
                self._basic_attack(player)
            elif self.attack_pattern == 1:
                self._combo_attack(player)
            elif self.attack_pattern == 2:
                self._multi_shot_attack(player)
            elif self.attack_pattern == 3:
                self._dash_attack(player)
            elif self.attack_pattern == 4:
                self._desperate_attack(player)
            elif self.attack_pattern == 5:
                self._ground_slam_attack(player)
            
            # Shorter cooldown in rage mode
            if self.rage_mode:
                self.attack_cooldown = 20  # Even faster in rage mode
            else:
                self.attack_cooldown = 35  # Faster attacks overall

    def _behavior_search(self, player, obstacles, dt):
        """Search behavior - move to last known player position"""
        self.search_timer += dt
        
        if self.last_known_player_pos:
            target_x, target_y = self.last_known_player_pos
            dx = target_x - self.rect.centerx
            
            if abs(dx) > 10:
                if dx > 0:
                    self.direction = 1
                    self.facing_right = True
                else:
                    self.direction = -1
                    self.facing_right = False
                
                self.rect.x += self.direction * self.speed * 0.7 * dt  # Slower when searching

    def _basic_attack(self, player):
        """Basic melee attack - BOSS level damage with knockback"""
        if hasattr(player, 'lives') and not getattr(player, 'invulnerable', False):
            damage = self.attack_damage
            if self.rage_mode:
                damage *= 2  # Double damage in rage mode
            
            # Apply damage
            player.lives -= damage
            
            # Apply knockback
            if hasattr(player, 'rect'):
                knockback_direction = 1 if self.facing_right else -1
                player.rect.x += knockback_direction * self.attack_knockback
                
                # Add vertical knockback
                if hasattr(player, 'y_velocity'):
                    player.y_velocity = -8  # Launch player up slightly
            
            if hasattr(player, 'iFrame'):
                player.iFrame()
            print(f"BOSS SMASH! Hit player for {damage} damage with knockback!")
            
        # Show attack visual feedback
        self.attack_flash_until = pygame.time.get_ticks() + self.attack_flash_time
        self.attacking = True
        
        # Trigger screen shake
        self._trigger_screen_shake(8, 300)  # Stronger shake
        
        # Create particles
        self._create_attack_particles("basic")

    def _trigger_screen_shake(self, intensity, duration):
        """Trigger screen shake effect"""
        # This will be handled by the sandbox when the enemy attacks
        pass
    
    
    def _create_attack_particles(self, particle_type="basic"):
        """Create particle effects for attacks"""
        import random
        
        if particle_type == "basic":
            # Basic attack particles
            for i in range(8):
                particle = {
                    'x': self.rect.centerx + random.randint(-20, 20),
                    'y': self.rect.centery + random.randint(-20, 20),
                    'dx': random.uniform(-3, 3),
                    'dy': random.uniform(-3, 3),
                    'life': 30,
                    'color': (255, 100, 100),
                    'size': random.randint(2, 4)
                }
                self.particles.append(particle)
        
        elif particle_type == "combo":
            # Combo attack particles
            for i in range(15):
                particle = {
                    'x': self.rect.centerx + random.randint(-30, 30),
                    'y': self.rect.centery + random.randint(-30, 30),
                    'dx': random.uniform(-5, 5),
                    'dy': random.uniform(-5, 5),
                    'life': 45,
                    'color': (255, 200, 0),
                    'size': random.randint(3, 6)
                }
                self.particles.append(particle)
        
        elif particle_type == "desperate":
            # Desperate attack particles
            for i in range(25):
                particle = {
                    'x': self.rect.centerx + random.randint(-40, 40),
                    'y': self.rect.centery + random.randint(-40, 40),
                    'dx': random.uniform(-8, 8),
                    'dy': random.uniform(-8, 8),
                    'life': 60,
                    'color': (255, 0, 0),
                    'size': random.randint(4, 8)
                }
                self.particles.append(particle)
    
    def _update_particles(self, dt):
        """Update particle effects"""
        for particle in self.particles[:]:
            particle['x'] += particle['dx'] * dt
            particle['y'] += particle['dy'] * dt
            particle['life'] -= dt
            
            if particle['life'] <= 0:
                self.particles.remove(particle)
    
    def _draw_particles(self, surface):
        """Draw particle effects"""
        for particle in self.particles:
            alpha = int(255 * (particle['life'] / 30))  # Fade out over time
            color = (*particle['color'], alpha)
            pygame.draw.circle(surface, particle['color'], 
                             (int(particle['x']), int(particle['y'])), 
                             particle['size'])

    def _combo_attack(self, player):
        """Combo attack - Multiple hits with devastating effects"""
        if hasattr(player, 'lives') and not getattr(player, 'invulnerable', False):
            combo_damage = self.attack_damage
            if self.rage_mode:
                combo_damage *= 1.5
            
            # Multiple hits with increasing damage
            total_damage = 0
            for i in range(5):  # More hits
                hit_damage = combo_damage + i  # Each hit does more damage
                player.lives -= hit_damage
                total_damage += hit_damage
                
                # Apply knockback on each hit
                if hasattr(player, 'rect'):
                    knockback_direction = 1 if self.facing_right else -1
                    player.rect.x += knockback_direction * (self.attack_knockback + i * 2)
                
                if hasattr(player, 'iFrame'):
                    player.iFrame()
            
            print(f"BOSS COMBO FURY! Hit player for {total_damage} total damage!")
            
        # Show attack visual feedback
        self.attack_flash_until = pygame.time.get_ticks() + self.attack_flash_time
        self.attacking = True
        
        # Trigger stronger screen shake for combo
        self._trigger_screen_shake(12, 500)  # Much stronger shake
        
        # Create combo particles
        self._create_attack_particles("combo")

    def _desperate_attack(self, player):
        """Desperate attack - Used when boss is very low on health"""
        if hasattr(player, 'lives') and not getattr(player, 'invulnerable', False):
            # MASSIVE damage - this is the boss's last resort
            desperate_damage = self.attack_damage * 6  # Even more damage
            player.lives -= desperate_damage
            
            # MASSIVE knockback
            if hasattr(player, 'rect'):
                knockback_direction = 1 if self.facing_right else -1
                player.rect.x += knockback_direction * (self.attack_knockback * 3)  # Triple knockback
                
                # Launch player high into the air
                if hasattr(player, 'y_velocity'):
                    player.y_velocity = -15  # High launch
            
            if hasattr(player, 'iFrame'):
                player.iFrame()
            
            print(f"BOSS DESPERATE RAGE! Hit player for {desperate_damage} MASSIVE damage!")
            
            # Longer cooldown for desperate attack
            self.attack_cooldown = 180  # 3 seconds
            
        # Show attack visual feedback
        self.attack_flash_until = pygame.time.get_ticks() + self.attack_flash_time
        self.attacking = True
        
        # Trigger massive screen shake for desperate attack
        self._trigger_screen_shake(15, 500)  # intensity 15, duration 500ms
        
        # Create desperate attack particles
        self._create_attack_particles("desperate")
    
    def _ground_slam_attack(self, player):
        """Ground slam attack - Creates shockwave"""
        if hasattr(player, 'lives') and not getattr(player, 'invulnerable', False):
            # Check if player is within shockwave range
            distance = abs(player.rect.centerx - self.rect.centerx)
            if distance <= 150:  # Shockwave range
                slam_damage = self.attack_damage * 3
                player.lives -= slam_damage
                
                # Knockback based on distance
                knockback_force = max(5, 20 - distance // 10)
                if hasattr(player, 'rect'):
                    knockback_direction = 1 if player.rect.centerx > self.rect.centerx else -1
                    player.rect.x += knockback_direction * knockback_force
                
                if hasattr(player, 'iFrame'):
                    player.iFrame()
                
                print(f"BOSS GROUND SLAM! Hit player for {slam_damage} damage!")
        
        # Show attack visual feedback
        self.attack_flash_until = pygame.time.get_ticks() + self.attack_flash_time
        self.attacking = True
        
        # Trigger massive screen shake
        self._trigger_screen_shake(20, 800)  # Massive shake
        
        # Create ground slam particles
        self._create_attack_particles("desperate")
    
    def _berserker_attack(self, player):
        """Berserker mode - Temporary invincibility with rapid attacks"""
        if not self.berserker_mode:
            # Activate berserker mode
            self.berserker_mode = True
            self.berserker_timer = 300  # 5 seconds of berserker mode
            self.invulnerable = True
            self.speed *= 2  # Double speed
            self.attack_cooldown = 0  # No cooldown during berserker
            print("BOSS ENTERED BERSERKER MODE! INVINCIBLE AND RAPID ATTACKS!")
        
        # Rapid fire attacks during berserker mode
        if self.berserker_timer > 0:
            self.berserker_timer -= 1
            if self.berserker_timer <= 0:
                # End berserker mode
                self.berserker_mode = False
                self.invulnerable = False
                self.speed /= 2  # Restore normal speed
                self.attack_cooldown = 60  # Normal cooldown
                print("BOSS BERSERKER MODE ENDED!")
            
            # Attack every frame during berserker mode
            if hasattr(player, 'lives') and not getattr(player, 'invulnerable', False):
                berserker_damage = self.attack_damage // 2  # Half damage but rapid
                player.lives -= berserker_damage
                if hasattr(player, 'iFrame'):
                    player.iFrame()
                print(f"BERSERKER FURY! Hit player for {berserker_damage} damage!")
        
        # Show berserker visual feedback
        self.attack_flash_until = pygame.time.get_ticks() + self.attack_flash_time
        self.attacking = True
        
        # Trigger screen shake
        self._trigger_screen_shake(10, 200)
        
        # Create berserker particles
        self._create_attack_particles("combo")
    
    def _charge_attack(self, player):
        """Charge attack - Long-range charging attack"""
        if not self.charging:
            # Start charging
            self.charging = True
            self.charge_attack_timer = 60  # 1 second charge time
            print("BOSS IS CHARGING UP A DEVASTATING ATTACK!")
        else:
            # Continue charging
            self.charge_attack_timer -= 1
            if self.charge_attack_timer <= 0:
                # Release charge attack
                self.charging = False
                self._execute_charge_attack(player)
    
    def _execute_charge_attack(self, player):
        """Execute the charged attack"""
        if hasattr(player, 'lives') and not getattr(player, 'invulnerable', False):
            # Massive damage
            charge_damage = self.attack_damage * 8  # 8x damage
            player.lives -= charge_damage
            
            # Massive knockback
            if hasattr(player, 'rect'):
                knockback_direction = 1 if self.facing_right else -1
                player.rect.x += knockback_direction * (self.attack_knockback * 5)  # 5x knockback
                
                # Launch player very high
                if hasattr(player, 'y_velocity'):
                    player.y_velocity = -20  # Very high launch
            
            if hasattr(player, 'iFrame'):
                player.iFrame()
            
            print(f"BOSS CHARGED ATTACK! Hit player for {charge_damage} MASSIVE damage!")
        
        # Show charge attack visual feedback
        self.attack_flash_until = pygame.time.get_ticks() + self.attack_flash_time
        self.attacking = True
        
        # Trigger massive screen shake
        self._trigger_screen_shake(25, 1000)  # Massive shake
        
        # Create charge attack particles
        self._create_attack_particles("desperate")

    def _multi_shot_attack(self, player):
        """Special ability: Multi-shot attack"""
        if not self.can_shoot:
            return

        # Create multiple projectiles in a spread pattern
        for angle_offset in [-30, -15, 0, 15, 30]:
            projectile = EnemyProjectile(
                self.rect.centerx, 
                self.rect.centery,
                angle_offset,
                4.0  # Speed
            )
            self.projectile_manager.add_projectile(projectile)

        self.special_ability_cooldown = 300  # 5 second cooldown
        print("Level 2 enemy used multi-shot attack!")

    def _dash_attack(self, player):
        """Special ability: Dash attack"""
        # Dash in facing direction
        dash_distance = 100
        if self.facing_right:
            self.rect.x += dash_distance
        else:
            self.rect.x -= dash_distance

        # Deal damage if close to player (only if player is provided)
        if player and self.rect.colliderect(player.rect):
            if hasattr(player, 'lives') and not getattr(player, 'invulnerable', False):
                player.lives -= self.attack_damage * 2  # Double damage for dash
                if hasattr(player, 'iFrame'):
                    player.iFrame()

        self.special_ability_cooldown = 240  # 4 second cooldown
        print("Level 2 enemy used dash attack!")

    def _update_special_abilities(self, player, dt):
        """Update special abilities"""
        # Shield ability
        if self.ability_type == "shield" and self.special_ability_cooldown <= 0:
            if self.health < self.max_health * 0.3:  # Use shield when low health
                self._activate_shield()
                self.special_ability_cooldown = 600  # 10 second cooldown

    def _activate_shield(self):
        """Activate temporary shield"""
        self.invulnerable = True
        self.invulnerable_timer = 180  # 3 seconds of invulnerability
        print("BOSS activated shield!")

    def _teleport_to_player(self, player):
        """Teleport behind player for surprise attack"""
        if not player:
            return
        
        # Teleport to a position behind the player
        teleport_distance = 100
        if player.rect.centerx > self.rect.centerx:
            # Player is to the right, teleport to their left
            self.rect.x = player.rect.x - teleport_distance
        else:
            # Player is to the left, teleport to their right
            self.rect.x = player.rect.x + teleport_distance
        
        self.rect.y = player.rect.y  # Same height as player
        self.teleport_cooldown = 300  # 5 second cooldown
        print("BOSS teleported behind player!")

    def _summon_minions(self, player):
        """Summon minion enemies to help the boss"""
        # This would create additional enemies to help the boss
        # For now, just create projectiles that act like minions
        for i in range(3):
            angle = (i * 120) * math.pi / 180
            projectile = EnemyProjectile(
                self.rect.centerx,
                self.rect.centery,
                math.degrees(angle),
                3.0
            )
            self.projectile_manager.add_projectile(projectile)
        
        self.summon_cooldown = 600  # 10 second cooldown
        print("BOSS summoned minions!")

    def jump(self):
        """BOSS jump - Much more powerful than Level 1"""
        if self.on_ground and self.jump_cooldown <= 0:
            self.y_velocity = -self.jump_power
            self.on_ground = False
            self.jump_cooldown = self.max_jump_cooldown
            self.double_jump_used = False  # Reset double jump
            print(f"BOSS jumped!")
    
    def double_jump_attack(self):
        """BOSS double jump with attack"""
        if not self.on_ground and self.double_jump and not self.double_jump_used:
            self.y_velocity = -self.jump_power * 0.8  # Slightly weaker than first jump
            self.double_jump_used = True
            print(f"BOSS double jump attack!")

    def _get_distance_to_player(self, player):
        """Calculate distance to player"""
        if not player:
            return float('inf')
        
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        return math.sqrt(dx*dx + dy*dy)

    def _can_see_player(self, player, obstacles):
        """Check if enemy can see player (line of sight)"""
        if not player:
            return False

        distance = self._get_distance_to_player(player)
        if distance > self.sight_range:
            return False

        # Simple line of sight check
        start_x, start_y = self.rect.centerx, self.rect.centery
        end_x, end_y = player.rect.centerx, player.rect.centery

        steps = int(distance / 10)
        for i in range(steps + 1):
            t = i / steps
            check_x = start_x + (end_x - start_x) * t
            check_y = start_y + (end_y - start_y) * t

            for obstacle in obstacles:
                if hasattr(obstacle, 'rect') and obstacle.rect.collidepoint(check_x, check_y):
                    return False

        return True

    def _apply_physics(self, obstacles, dt):
        """Apply physics including gravity and collision"""
        # Apply gravity
        if not self.on_ground:
            self.y_velocity += self.gravity * dt
            self.rect.y += self.y_velocity * dt

        # Check ground collision
        self._check_ground_collision(obstacles)
        
        # Reset double jump when landing
        if self.on_ground:
            self.double_jump_used = False

    def _check_ground_collision(self, obstacles):
        """Check collision with ground obstacles"""
        self.on_ground = False
        
        for obstacle in obstacles:
            if hasattr(obstacle, 'rect') and self.rect.colliderect(obstacle.rect):
                if self.y_velocity > 0:  # Falling down
                    self.rect.bottom = obstacle.rect.top
                    self.y_velocity = 0
                    self.on_ground = True
                    break

    def take_damage(self, damage):
        """Take damage with invulnerability frames - BOSS level"""
        if self.invulnerable:
            return

        # Reduce damage in rage mode (boss gets tougher)
        if self.rage_mode:
            damage = int(damage * 0.7)  # 30% damage reduction

        self.health -= damage
        self.invulnerable = True
        self.invulnerable_timer = 30  # Shorter invulnerability for boss

        # Check for phase changes
        old_phase = self.current_phase
        self._update_boss_phase()
        
        if old_phase != self.current_phase:
            print(f"BOSS entered Phase {self.current_phase}!")
            if self.current_phase >= 3:
                print("BOSS is now in RAGE MODE!")
                self.rage_mode = True

        if self.health <= 0:
            self.alive = False
            print(f"BOSS DEFEATED! Well done!")

    def draw(self, surface, debug_mode=False):
        """Draw enemy with enhanced visuals"""
        if not self.alive or not self.visible:
            return

        # Blink when invulnerable
        if self.invulnerable and (pygame.time.get_ticks() // 100) % 2:
            return

        # Draw enemy sprite
        if self.facing_right:
            # Draw facing right
            surface.blit(self.image, self.rect)
        else:
            # Flip horizontally when facing left
            flipped_image = pygame.transform.flip(self.image, True, False)
            surface.blit(flipped_image, self.rect)
        
        # Draw colored overlay for different enemy types
        if hasattr(self, 'overlay_color'):
            overlay_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            overlay_surface.fill((*self.overlay_color, 80))  # Semi-transparent overlay
            surface.blit(overlay_surface, self.rect)

        # Draw boss level indicator
        font = pygame.font.Font(None, 16)
        level_text = font.render("BOSS", True, (255, 255, 0))
        surface.blit(level_text, (self.rect.x + 2, self.rect.y + 2))
        
        
        # Draw phase indicator with enhanced colors
        phase_colors = {
            1: (255, 255, 255),  # White
            2: (255, 255, 0),    # Yellow
            3: (255, 165, 0),    # Orange
            4: (255, 0, 0),      # Red
            5: (128, 0, 128)     # Purple for final phase
        }
        phase_color = phase_colors.get(self.current_phase, (255, 255, 255))
        phase_text = font.render(f"P{self.current_phase}", True, phase_color)
        surface.blit(phase_text, (self.rect.x + 2, self.rect.y + 18))
        
        # Draw rage mode indicator
        if self.rage_mode:
            rage_text = font.render("RAGE!", True, (255, 0, 0))
            surface.blit(rage_text, (self.rect.x + 2, self.rect.y + 34))
        
        # Draw phase transition effect
        if self.phase_transition and self.phase_transition_timer > 0:
            self.phase_transition_timer -= 1
            if self.phase_transition_timer <= 0:
                self.phase_transition = False
            
            # Pulsing effect during transition
            pulse = (120 - self.phase_transition_timer) / 120.0
            pulse_alpha = int(255 * (0.5 + 0.5 * math.sin(pulse * math.pi * 4)))
            transition_surface = pygame.Surface((self.rect.width + 20, self.rect.height + 20), pygame.SRCALPHA)
            transition_surface.fill((255, 255, 0, pulse_alpha))
            surface.blit(transition_surface, (self.rect.x - 10, self.rect.y - 10))

        # Draw boss health bar with phase indicators
        bar_width = self.rect.width
        bar_height = 6
        bar_x = self.rect.x
        bar_y = self.rect.y - 15

        # Background
        pygame.draw.rect(surface, (255, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        
        # Health with phase colors
        health_width = int((self.health / self.max_health) * bar_width)
        if self.current_phase == 1:
            health_color = (0, 255, 0)  # Green
        elif self.current_phase == 2:
            health_color = (255, 255, 0)  # Yellow
        elif self.current_phase == 3:
            health_color = (255, 165, 0)  # Orange
        else:  # Phase 4
            health_color = (255, 0, 0)  # Red
        
        pygame.draw.rect(surface, health_color, (bar_x, bar_y, health_width, bar_height))
        
        # Phase dividers
        for i, threshold in enumerate(self.health_thresholds):
            divider_x = bar_x + int(threshold * bar_width)
            pygame.draw.line(surface, (255, 255, 255), (divider_x, bar_y), (divider_x, bar_y + bar_height), 1)

        # Draw special ability indicator
        if self.special_ability_cooldown > 0:
            ability_text = font.render(f"{self.ability_type[:3]}", True, (255, 255, 0))
            surface.blit(ability_text, (self.rect.x + 2, self.rect.y + 18))
        
        # Draw attack visual feedback
        now = pygame.time.get_ticks()
        if now < self.attack_flash_until:
            # Flash red when attacking
            flash_alpha = int(200 * (1 - (now - (self.attack_flash_until - self.attack_flash_time)) / self.attack_flash_time))
            flash_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            flash_surface.fill((255, 0, 0, flash_alpha))
            surface.blit(flash_surface, self.rect)
            
            # Draw attack text above enemy
            attack_font = pygame.font.Font(None, 28)
            if self.rage_mode:
                attack_text = attack_font.render("RAGE ATTACK!", True, (255, 100, 0))
            else:
                attack_text = attack_font.render("BOSS ATTACK!", True, (255, 0, 0))
            text_rect = attack_text.get_rect(center=(self.rect.centerx, self.rect.y - 40))
            surface.blit(attack_text, text_rect)

        # Draw projectiles
        self.projectile_manager.draw(surface)

        # Debug information
        if debug_mode:
            self._draw_debug_info(surface)

    def _draw_debug_info(self, surface):
        """Draw debug information"""
        font = pygame.font.Font(None, 20)
        
        # AI state
        state_text = font.render(f"State: {self.ai_state}", True, (255, 255, 255))
        surface.blit(state_text, (self.rect.x, self.rect.y - 30))

        # Sight range
        pygame.draw.circle(surface, self.sight_color, 
                         self.rect.center, self.sight_range, 2)

        # Attack range
        attack_rect = pygame.Rect(
            self.rect.centerx - self.attack_range.x/2,
            self.rect.centery - self.attack_range.y/2,
            self.attack_range.x,
            self.attack_range.y
        )
        pygame.draw.rect(surface, (255, 0, 0), attack_rect, 2)

        # Patrol points
        for i, (px, py) in enumerate(self.patrol_points):
            color = (0, 255, 0) if i == self.current_patrol_target else (100, 100, 100)
            pygame.draw.circle(surface, color, (int(px), int(py)), 5)

        # Direction indicator
        arrow_end_x = self.rect.centerx + self.direction * 30
        pygame.draw.line(surface, (255, 255, 0), 
                        self.rect.center, (arrow_end_x, self.rect.centery), 3)


# Level 2 Enemy Types
class Level2HunterEnemy(Level2Enemy):
    """Hunter enemy that learns player patterns"""
    
    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "Level2Hunter"
        # Keep the same sprite as base enemy, but add a colored overlay for identification
        self.overlay_color = (255, 100, 255)  # Magenta overlay
        self.ability_type = "multi_shot"
        self.learning_rate = 0.1
        self.player_velocity_history = []

    def _behavior_chase(self, player, obstacles, dt):
        """Override chase to use learning"""
        super()._behavior_chase(player, obstacles, dt)
        
        # Learn from player movement
        if hasattr(player, 'scroll_speed'):
            self.player_velocity_history.append(player.scroll_speed)
            if len(self.player_velocity_history) > 60:
                self.player_velocity_history.pop(0)

    def _behavior_attack(self, player, obstacles, dt):
        """Override attack to use learned patterns"""
        if self.attack_cooldown <= 0:
            # Use learned patterns to predict player movement
            if len(self.player_velocity_history) > 10:
                avg_velocity = sum(self.player_velocity_history) / len(self.player_velocity_history)
                predicted_x = player.rect.centerx + avg_velocity * 30
                
                # Aim at predicted position
                dx = predicted_x - self.rect.centerx
                if dx > 0:
                    self.direction = 1
                    self.facing_right = True
                else:
                    self.direction = -1
                    self.facing_right = False
            
            self._multi_shot_attack(player)
            self.attack_cooldown = 45  # Faster attacks


class Level2StealthEnemy(Level2Enemy):
    """Stealth enemy that uses invisibility"""
    
    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "Level2Stealth"
        # Keep the same sprite as base enemy, but add a colored overlay for identification
        self.overlay_color = (100, 100, 255)  # Blue overlay
        self.ability_type = "dash"
        self.stealth_mode = True
        self.stealth_timer = 0
        self.ambush_range = 80

    def _update_ai_state(self, player, obstacles):
        """Override to include stealth mechanics"""
        if self.stealth_mode:
            if self._can_see_player(player, obstacles) and self._get_distance_to_player(player) < self.ambush_range:
                self.stealth_mode = False
                self.ai_state = "attack"
            elif self._can_see_player(player, obstacles):
                self.ai_state = "hide"
        else:
            super()._update_ai_state(player, obstacles)
            
            # Return to stealth after some time
            if self.ai_timer > 300:
                self.stealth_mode = True
                self.ai_state = "idle"

    def _behavior_hide(self, player, obstacles, dt):
        """Hide from player"""
        if player:
            # Move away from player
            dx = self.rect.centerx - player.rect.centerx
            if dx > 0:
                self.direction = 1
                self.facing_right = True
            else:
                self.direction = -1
                self.facing_right = False
            
            self.rect.x += self.direction * self.speed * 0.5 * dt  # Slower when hiding

    def draw(self, surface, debug_mode=False):
        """Override to show stealth effect"""
        if self.stealth_mode:
            # Draw with transparency
            temp_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            stealth_color = (*self.image.get_at((0, 0))[:3], 128)  # Semi-transparent
            temp_surface.fill(stealth_color)
            surface.blit(temp_surface, self.rect)
        else:
            super().draw(surface, debug_mode)


class Level2BossEnemy(Level2Enemy):
    """Boss enemy with multiple phases"""
    
    def __init__(self, x, y):
        super().__init__(x, y)
        self.name = "Level2Boss"
        # Keep the same sprite as base enemy, but add a colored overlay for identification
        self.overlay_color = (255, 0, 0)  # Bright red overlay
        self.ability_type = "shield"
        self.health = 300
        self.max_health = 300
        self.phase = 1
        self.phase_timer = 0

    def _update_ai_state(self, player, obstacles):
        """Override to include phase-based behavior"""
        # Update phase based on health
        health_percentage = self.health / self.max_health
        if health_percentage > 0.7:
            self.phase = 1
        elif health_percentage > 0.3:
            self.phase = 2
        else:
            self.phase = 3

        # Phase-specific behavior
        if self.phase == 1:
            super()._update_ai_state(player, obstacles)
        elif self.phase == 2:
            # Phase 2: More aggressive
            if self._get_distance_to_player(player) < self.attack_range.length():
                self.ai_state = "attack"
            else:
                self.ai_state = "chase"
        else:
            # Phase 3: Desperate rush
            self.ai_state = "chase"

    def _behavior_attack(self, player, obstacles, dt):
        """Override attack for phase-based abilities"""
        if self.phase == 1:
            super()._behavior_attack(player, obstacles, dt)
        elif self.phase == 2:
            # Phase 2: Rapid multi-shot
            if self.attack_cooldown <= 0:
                self._multi_shot_attack(player)
                self.attack_cooldown = 30  # Faster attacks
        else:
            # Phase 3: Desperate attacks
            if self.attack_cooldown <= 0:
                self._dash_attack(player)
                self.attack_cooldown = 20  # Very fast attacks

    def draw(self, surface, debug_mode=False):
        """Override to show phase effects"""
        super().draw(surface, debug_mode)
        
        # Draw phase indicator
        font = pygame.font.Font(None, 20)
        phase_text = font.render(f"Phase {self.phase}", True, (255, 255, 0))
        surface.blit(phase_text, (self.rect.x, self.rect.y - 50))

        # Draw phase-specific effects
        if self.phase == 2:
            # Glowing effect
            pygame.draw.circle(surface, (255, 255, 0, 100), 
                            self.rect.center, self.rect.width, 2)
        elif self.phase == 3:
            # Pulsing red effect
            pulse = math.sin(pygame.time.get_ticks() * 0.01) * 0.3 + 0.7
            pulse_rect = pygame.Rect(
                self.rect.x - 10, self.rect.y - 10,
                self.rect.width + 20, self.rect.height + 20
            )
            pygame.draw.rect(surface, (255, 0, 0, int(100 * pulse)), pulse_rect, 3)
