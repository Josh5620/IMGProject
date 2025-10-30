"""
Level 2 Powerup Sprite Loader
Extracts mushroom sprites from the spritesheet and maps them to powerup types
"""

import pygame


def load_mushroom_sprites(sprite_sheet_path="assets/Level2/mushroom level 2.png", 
                         row=2, sprite_width=16, sprite_height=16):
    """
    Load mushroom sprites from a specific row of the spritesheet
    
    Args:
        sprite_sheet_path: Path to the mushroom spritesheet
        row: Which row to extract from (0-indexed, default=2 for third row)
        sprite_width: Width of each sprite in pixels
        sprite_height: Height of each sprite in pixels
    
    Returns:
        Dictionary mapping powerup types to their sprite images
    """
    try:
        # Load the spritesheet
        sheet = pygame.image.load(sprite_sheet_path).convert_alpha()
        
        # Powerup types in order (6 types)
        powerup_types = [
            "health_burst",      # Column 0
            "fire_cloak",        # Column 1
            "speed_wind",        # Column 2
            "wolf_strength",     # Column 3
            "grandma_amulet",    # Column 4
            "forest_wisdom"      # Column 5
        ]
        
        # Dictionary to store the sprites
        mushroom_sprites = {}
        
        # Extract each mushroom sprite from the row
        for col, powerup_type in enumerate(powerup_types):
            # Calculate the position in the spritesheet
            x = col * sprite_width
            y = row * sprite_height
            
            # Extract the sprite
            sprite_rect = pygame.Rect(x, y, sprite_width, sprite_height)
            sprite = sheet.subsurface(sprite_rect).copy()
            
            # Scale it up for better visibility (16x16 -> 32x32)
            sprite = pygame.transform.scale(sprite, (32, 32))
            
            mushroom_sprites[powerup_type] = sprite
            print(f"Loaded {powerup_type} mushroom from column {col}")
        
        return mushroom_sprites
    
    except Exception as e:
        print(f"Error loading mushroom sprites: {e}")
        return {}


def create_level2_powerup_with_sprite(x, y, powerup_type, mushroom_sprites):
    """
    Create a Level 2 powerup with a mushroom sprite
    
    Args:
        x, y: Position of the powerup
        powerup_type: Type of powerup
        mushroom_sprites: Dictionary of loaded mushroom sprites
    
    Returns:
        Level2PowerupWithSprite object
    """
    from level2_powerups import Level2Powerup
    
    class Level2PowerupWithSprite(Level2Powerup):
        """Level 2 powerup that uses a mushroom sprite instead of procedural graphics"""
        
        def __init__(self, x, y, powerup_type, sprite_image):
            super().__init__(x, y, powerup_type)
            self.sprite_image = sprite_image
            self.has_sprite = sprite_image is not None
        
        def draw(self, surface, scroll_offset=0):
            """Draw powerup using mushroom sprite with scroll offset support"""
            if self.collected:
                # Draw collection particles (they stay in screen space)
                for particle in self.collection_particles:
                    alpha = int(255 * (particle['life'] / particle['max_life']))
                    if alpha > 0:
                        color = (*particle['color'], min(alpha, 255))
                        pygame.draw.circle(surface, color[:3], 
                                        (int(particle['x']), int(particle['y'])), 
                                        particle['size'])
                return
            
            if self.has_sprite:
                # Use mushroom sprite
                import math
                
                # Apply scroll offset to position (world space -> screen space)
                screen_x = self.rect.centerx - scroll_offset
                screen_y = self.rect.centery
                
                # Bobbing effect
                pulse_scale = 1.0 + math.sin(self.pulse_timer) * 0.15
                
                # Scale the sprite with pulse
                scaled_width = int(self.sprite_image.get_width() * pulse_scale)
                scaled_height = int(self.sprite_image.get_height() * pulse_scale)
                scaled_sprite = pygame.transform.scale(self.sprite_image, 
                                                      (scaled_width, scaled_height))
                
                # Position centered in screen space
                sprite_x = screen_x - scaled_width // 2
                sprite_y = self.rect.y + (self.rect.height - scaled_height) // 2
                
                # Draw glow behind sprite (in screen space)
                glow_radius = int(25 * pulse_scale)  # Reduced from 35
                for i in range(3):
                    radius = glow_radius - i * 4
                    if radius > 0:
                        alpha = 30 - i * 8
                        pygame.draw.circle(surface, self.color_set["glow"][:3], 
                                        (int(screen_x), int(screen_y)), radius)
                
                # Draw the mushroom sprite
                surface.blit(scaled_sprite, (int(sprite_x), int(sprite_y)))
                
                # Draw sparkles around it (in screen space)
                sparkle_count = 6
                for i in range(sparkle_count):
                    angle = (self.sparkle_timer * 60 + i * 60) % 360
                    sparkle_distance = 20 + math.sin(self.sparkle_timer * 2 + i) * 4  # Reduced from 30/6
                    sparkle_x = screen_x + int(sparkle_distance * math.cos(math.radians(angle)))
                    sparkle_y = screen_y + int(sparkle_distance * math.sin(math.radians(angle)))
                    
                    sparkle_size = 2 + int(math.sin(self.sparkle_timer * 4 + i))
                    pygame.draw.circle(surface, self.color_set["bright"][:3], 
                                    (int(sparkle_x), int(sparkle_y)), sparkle_size)
            else:
                # Fallback to original procedural drawing
                super().draw(surface)
    
    # Get the sprite for this powerup type
    sprite = mushroom_sprites.get(powerup_type)
    
    return Level2PowerupWithSprite(x, y, powerup_type, sprite)


# Object name to powerup type mapping (for Tiled)
TILED_OBJECT_TO_POWERUP = {
    "health_mushroom": "health_burst",
    "fire_mushroom": "fire_cloak",
    "speed_mushroom": "speed_wind",
    "strength_mushroom": "wolf_strength",
    "amulet_mushroom": "grandma_amulet",
    "wisdom_mushroom": "forest_wisdom"
}


if __name__ == "__main__":
    # Test the loader
    pygame.init()
    pygame.display.set_mode((1, 1))
    
    print("\n" + "=" * 60)
    print("LEVEL 2 POWERUP LOADER - TEST")
    print("=" * 60)
    
    sprites = load_mushroom_sprites()
    
    if sprites:
        print(f"\n✅ Successfully loaded {len(sprites)} mushroom sprites:")
        for powerup_type in sprites:
            print(f"  - {powerup_type}")
        print("\n📍 Tiled Object Names:")
        for obj_name, powerup_type in TILED_OBJECT_TO_POWERUP.items():
            print(f"  - '{obj_name}' → {powerup_type}")
    else:
        print("\n❌ Failed to load mushroom sprites")
    
    print("=" * 60)

