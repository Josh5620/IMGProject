"""
Test Boss Animation System
Displays all boss animations in a grid to verify they load and play correctly.
Controls:
- ESC: Exit
- 1-7: Jump to specific animation (1=Idle, 2=Walk, 3=Attack, 4=Cast, 5=Spell, 6=Hurt, 7=Death)
- SPACE: Pause/Resume
"""

import pygame
import sys
from BossEnemy import build_boss_animations_from_individual_files, BOSS_ASSETS_PATH

# Initialize Pygame
pygame.init()

# Screen setup
SCREEN_WIDTH = 1350
SCREEN_HEIGHT = 850
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Boss Animation Test")
clock = pygame.time.Clock()

# Load all animations
print("Loading boss animations from:", BOSS_ASSETS_PATH)
animations = build_boss_animations_from_individual_files(BOSS_ASSETS_PATH)

# Animation info
anim_names = ["idle", "run", "attack", "cast", "spell", "hurt", "death"]
anim_labels = {
    "idle": "Idle (8 frames)",
    "run": "Walk (8 frames)", 
    "attack": "Attack (10 frames)",
    "cast": "Cast (9 frames)",
    "spell": "Spell (16 frames)",
    "hurt": "Hurt (3 frames)",
    "death": "Death (10 frames)"
}

# Animation state
current_frame = {name: 0 for name in anim_names}
frame_timer = 0
FRAME_DELAY = 8  # Frames to wait between animation updates
paused = False

# Font
font = pygame.font.Font(None, 24)
title_font = pygame.font.Font(None, 36)

# Colors
BG_COLOR = (20, 20, 30)
TEXT_COLOR = (255, 255, 255)
LABEL_COLOR = (100, 200, 255)
FRAME_COLOR = (80, 80, 100)

def draw_animation_info():
    """Draw title and instructions"""
    title = title_font.render("Boss Animation Test - All Animations", True, TEXT_COLOR)
    screen.blit(title, (20, 10))
    
    instructions = [
        "ESC: Exit  |  SPACE: Pause/Resume  |  1-7: Jump to animation",
        f"Frame Delay: {FRAME_DELAY} ticks  |  Status: {'PAUSED' if paused else 'PLAYING'}"
    ]
    
    for i, text in enumerate(instructions):
        surf = font.render(text, True, LABEL_COLOR)
        screen.blit(surf, (20, 50 + i * 25))

def draw_animation(name, x, y, scale=1.0):
    """Draw a single animation with its label and frame counter"""
    if name not in animations or not animations[name]:
        error_text = font.render(f"{name}: NO FRAMES", True, (255, 0, 0))
        screen.blit(error_text, (x, y))
        return
    
    frames = animations[name]
    frame_idx = current_frame[name] % len(frames)
    frame = frames[frame_idx]
    
    # No scaling - show actual size (128x128)
    scaled_frame = pygame.transform.scale(
        frame,
        (frame.get_width() * scale, frame.get_height() * scale)
    )
    
    # Draw container background box (sized for 128x128)
    box_width = 400
    box_height = 180
    box_rect = pygame.Rect(x, y, box_width, box_height)
    pygame.draw.rect(screen, (30, 30, 40), box_rect)
    pygame.draw.rect(screen, LABEL_COLOR, box_rect, 3)
    
    # Draw animation title (top left)
    label = font.render(anim_labels.get(name, name).split('(')[0].strip(), True, LABEL_COLOR)
    screen.blit(label, (x + 10, y + 8))
    
    # Draw frame counter (top right)
    frame_info = font.render(f"Frame {frame_idx + 1}/{len(frames)}", True, TEXT_COLOR)
    screen.blit(frame_info, (x + box_width - 110, y + 8))
    
    # Draw the animation frame (centered, actual size)
    frame_rect = scaled_frame.get_rect(center=(x + box_width // 2, y + 100))
    bg_rect = frame_rect.inflate(15, 15)
    pygame.draw.rect(screen, FRAME_COLOR, bg_rect)
    pygame.draw.rect(screen, (100, 100, 120), bg_rect, 2)
    screen.blit(scaled_frame, frame_rect)
    
    # Draw frame dimensions (bottom)
    size_text = f"{frame.get_width()}x{frame.get_height()}px (actual size)"
    size_info = font.render(size_text, True, (150, 150, 150))
    screen.blit(size_info, (x + 10, y + box_height - 22))

def update_animations():
    """Update all animation frame counters"""
    global frame_timer
    
    if paused:
        return
    
    frame_timer += 1
    if frame_timer >= FRAME_DELAY:
        frame_timer = 0
        for name in anim_names:
            if name in animations and animations[name]:
                current_frame[name] = (current_frame[name] + 1) % len(animations[name])

def jump_to_animation(anim_index):
    """Reset a specific animation to frame 0"""
    if 0 <= anim_index < len(anim_names):
        name = anim_names[anim_index]
        current_frame[name] = 0
        print(f"Reset {name} to frame 0")

# Main loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                paused = not paused
                print("Paused" if paused else "Playing")
            elif event.key == pygame.K_1:
                jump_to_animation(0)
            elif event.key == pygame.K_2:
                jump_to_animation(1)
            elif event.key == pygame.K_3:
                jump_to_animation(2)
            elif event.key == pygame.K_4:
                jump_to_animation(3)
            elif event.key == pygame.K_5:
                jump_to_animation(4)
            elif event.key == pygame.K_6:
                jump_to_animation(5)
            elif event.key == pygame.K_7:
                jump_to_animation(6)
    
    # Update
    update_animations()
    
    # Draw
    screen.fill(BG_COLOR)
    draw_animation_info()
    
    # Layout animations in 3 columns (actual 128x128 size)
    start_x = 30
    start_y = 110
    spacing_x = 430  # Spacing for 400px wide boxes
    spacing_y = 200  # Spacing for 180px tall boxes
    
    for i, name in enumerate(anim_names):
        col = i % 3  # 3 columns for compact layout
        row = i // 3
        x = start_x + col * spacing_x
        y = start_y + row * spacing_y
        draw_animation(name, x, y, scale=1.0)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
