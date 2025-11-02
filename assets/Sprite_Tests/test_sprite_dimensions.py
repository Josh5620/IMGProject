import pygame
import sys

pygame.init()

# Test sprite dimensions
sprites_to_test = [
    ("Skeleton Idle", "assets/Level2/Skeleton/Idle.png"),
    ("Skeleton Walk", "assets/Level2/Skeleton/Walk.png"),
    ("Skeleton Attack", "assets/Level2/Skeleton/Attack.png"),
    ("Mushroom Idle", "assets/Level2/Mushroom/Idle.png"),
    ("Mushroom Run", "assets/Level2/Mushroom/Run.png"),
    ("Mushroom Attack", "assets/Level2/Mushroom/Attack.png"),
    ("Flying Eye Flight", "assets/Level2/Flying eye/Flight.png"),
    ("Flying Eye Attack", "assets/Level2/Flying eye/Attack.png"),
]

print("\n" + "=" * 70)
print("LEVEL 2 SPRITE SHEET ANALYSIS")
print("=" * 70)

for name, path in sprites_to_test:
    try:
        img = pygame.image.load(path)
        width = img.get_width()
        height = img.get_height()
        
        print(f"\n{name}:")
        print(f"  Total Size: {width}x{height}")
        
        # Try different frame counts
        for frames in [4, 5, 6, 8, 10, 11, 12]:
            frame_width = width // frames
            if width % frames == 0:  # Perfect division
                print(f"  → {frames} frames @ {frame_width}px width ✓ (perfect fit)")
        
        # Show some common frame widths
        for fw in [24, 32, 33, 40, 48, 51, 57, 58, 64, 150]:
            frames = width // fw
            if frames > 0 and frames < 20:
                remainder = width % fw
                if remainder == 0:
                    print(f"  → {fw}px frame width = {frames} frames ✓ (perfect)")
                elif remainder < 10:
                    print(f"  → {fw}px frame width = {frames} frames ({remainder}px leftover)")
                    
    except Exception as e:
        print(f"\n{name}: ERROR - {e}")

print("\n" + "=" * 70)
print("RECOMMENDATION:")
print("Use frame widths that divide evenly (marked with ✓)")
print("=" * 70 + "\n")

pygame.quit()
