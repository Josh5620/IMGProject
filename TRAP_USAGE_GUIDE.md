# Level 2 Trap Usage Guide

## Overview
Level 2 now supports three types of animated traps with different damage mechanics:

1. **Saw Trap** - Continuously damages (original trap)
2. **Lightning Trap** - Damages only during lightning strike frames ⚡
3. **Fire Trap** - Damages only during flame burst frames 🔥

## Trap Types

### 1. Saw Trap (SawTrap)
- **Type Name in Tiled**: `sawtrap`
- **Sprite**: `assets/Level2/Traps/SawTrap.png`
- **Frame Size**: 64x32 pixels
- **Damage Behavior**: ALL frames deal damage (always dangerous)
- **Cooldown**: 1000ms (1 second)
- **Damage**: 1 heart

### 2. Lightning Trap (LightningTrap) ⚡
- **Type Name in Tiled**: `lightningtrap`
- **Sprite**: `assets/Level2/Traps/LightningTrap.png`
- **Frame Size**: 96x96 pixels
- **Total Frames**: 10
- **Damage Frames**: 4, 5, 6 (middle frames when lightning bolt appears)
- **Safe Frames**: 0, 1, 2, 3, 7, 8, 9 (buildup and recovery)
- **Animation Speed**: 80ms per frame
- **Cooldown**: 2000ms (2 seconds between hits)
- **Damage**: 1 heart

**Usage Tip**: Lightning has a warning buildup before the strike. Players can time their movement to pass through during safe frames!

### 3. Fire Trap (FireTrap) 🔥
- **Type Name in Tiled**: `firetrap`
- **Sprite**: `assets/Level2/Traps/FireTrap.png`
- **Frame Size**: 64x64 pixels
- **Total Frames**: 6
- **Damage Frames**: 3, 4, 5 (when flames are actively burning)
- **Safe Frames**: 0, 1, 2 (buildup phase)
- **Animation Speed**: 100ms per frame
- **Cooldown**: 1500ms (1.5 seconds between hits)
- **Damage**: 1 heart

**Usage Tip**: Fire has a shorter buildup. Players need to watch for the initial spark frames to time their passage!

## How to Add Traps in Tiled Map Editor

### Step 1: Create an Object Layer
If you don't have one, create an object layer for traps (e.g., "Traps" or "Hazards")

### Step 2: Add Object
1. Click the "Insert Rectangle" tool
2. Place a rectangle where you want the trap
3. Size doesn't matter - it will be replaced by the trap sprite

### Step 3: Set Object Type
In the object properties, add a **Custom Property**:
- **Name**: `type`
- **Type**: string
- **Value**: One of:
  - `sawtrap`
  - `lightningtrap`
  - `firetrap`

### Example Object Setup
```
Object Name: Trap_001 (optional)
Type Property: "lightningtrap"
Position: X=500, Y=300
```

## Code Implementation Details

### Frame-Based Damage System
The new traps use a `FrameBasedTrap` class that only checks collision during specific animation frames:

```python
# Only these frames deal damage
damage_frames = [4, 5, 6]  # Lightning strike frames

# Check if current frame is dangerous
if self.current_frame in self.damage_frames:
    # Deal damage if player collides
```

### Customizing Trap Parameters
You can modify trap behavior in `game.py`:

```python
# Example: Make lightning more dangerous
trap = LightningTrap(
    anchor_x, 
    anchor_y, 
    damage=2,        # 2 hearts instead of 1
    cooldown=1000    # 1 second cooldown instead of 2
)
```

### Creating Custom Traps
To create your own frame-based trap:

```python
from blocks import FrameBasedTrap

class MyCustomTrap(FrameBasedTrap):
    def __init__(self, x, y, damage=1, cooldown=1000):
        super().__init__(
            x, y,
            'assets/Level2/Traps/MyTrap.png',
            frame_width=64,
            frame_height=64,
            damage=damage,
            cooldown=cooldown,
            damage_frames=[2, 3],  # Your dangerous frames
            animation_speed=120     # Speed in milliseconds
        )
```

## Collision System
All traps now use **world-space collision detection** to work correctly with level scrolling:

- Player position is converted to world space by adding scroll offset
- Ensures traps damage consistently throughout the entire level
- Matches the collision system used by Level 1 enemies

## Testing Your Traps
Run `test_traps.py` to visualize trap animations and damage frames:
```bash
python test_traps.py
```

This shows:
- **Red border** = Damage frame (dangerous!)
- **Green border** = Safe frame (can pass through)
- Frame numbers and timing

## Gameplay Tips

### For Level Designers:
- Place lightning traps with timing puzzles - players can learn the pattern
- Use fire traps in rapid sequences for timing challenges
- Mix saw traps (always dangerous) with frame-based traps for variety
- Leave enough space for players to observe trap timing before committing

### For Players:
- Watch the animation cycle before attempting to pass
- Lightning: Wait for the bright flash, then move during recovery
- Fire: Look for the initial spark, count to when flames appear
- Saw: No safe frames - need to jump over or dash through with invulnerability

## Technical Notes
- All traps respect invulnerability frames
- Cooldown prevents spam damage
- Dash ability grants invulnerability - can be used to pass through traps safely
- Traps are drawn in front of the background but behind the player
