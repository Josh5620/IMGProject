"""
Test script to visualize the new trap animations and damage frames
"""
import pygame
from blocks import LightningTrap, FireTrap, AnimatedTrap

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Trap Animation Test")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)

# Create trap instances
lightning = LightningTrap(200, 150)
fire = FireTrap(400, 150)
saw = AnimatedTrap(600, 150, 'assets/Level2/Traps/SawTrap.png', 64, 32)

traps = [
    (lightning, "Lightning", (200, 150)),
    (fire, "Fire", (400, 150)),
    (saw, "Saw", (600, 150))
]

# Mock player for testing
class MockPlayer:
    def __init__(self):
        self.rect = pygame.Rect(0, 0, 32, 48)
        self.lives = 10
        self.invulnerable = False
    
    def iFrame(self):
        self.invulnerable = True

player = MockPlayer()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
    screen.fill((50, 50, 50))
    
    # Update and draw each trap
    for trap, name, pos in traps:
        trap.update_animation()
        
        # Draw the trap
        screen.blit(trap.image, (trap.rect.x, trap.rect.y))
        
        # Draw label
        label = font.render(f"{name} - Frame: {trap.current_frame}/{len(trap.frames)-1}", True, (255, 255, 255))
        screen.blit(label, (pos[0] - 50, pos[1] - 30))
        
        # Highlight damage frames
        if hasattr(trap, 'damage_frames'):
            if trap.current_frame in trap.damage_frames:
                # Draw red border for damage frames
                pygame.draw.rect(screen, (255, 0, 0), trap.rect, 3)
                damage_text = font.render("DAMAGE!", True, (255, 50, 50))
                screen.blit(damage_text, (pos[0] - 30, trap.rect.bottom + 10))
            else:
                # Draw green border for safe frames
                pygame.draw.rect(screen, (0, 255, 0), trap.rect, 2)
        else:
            # Saw trap always damages
            pygame.draw.rect(screen, (255, 100, 0), trap.rect, 3)
            damage_text = font.render("ALWAYS DAMAGE", True, (255, 150, 0))
            screen.blit(damage_text, (pos[0] - 50, trap.rect.bottom + 10))
    
    # Instructions
    instructions = font.render("ESC to exit | Red = Damage Frame | Green = Safe Frame", True, (200, 200, 200))
    screen.blit(instructions, (20, 550))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
print("\nTrap Info:")
print(f"Lightning: {len(lightning.frames)} frames, damage on frames {lightning.damage_frames}")
print(f"Fire: {len(fire.frames)} frames, damage on frames {fire.damage_frames}")
print(f"Saw: {len(saw.frames)} frames, always damages")
