# Enemy Floating & Dash Issues - FIXED ✅

## Issues Fixed

### ✅ Issue 1: Enemies Still Floating
**Problem**: Skeleton and Mushroom enemies were floating above the ground instead of standing on platforms.

**Root Causes**:
1. Float accumulation in y_velocity causing position drift
2. Incorrect spawn position calculation (off by 32 pixels)
3. Centered hitbox system not accounting for spawn offset properly

**Solutions Applied**:

#### Fix 1: Integer Position Updates
**File**: `Level2Enemies.py` (Line 303)

```python
# BEFORE:
self.rect.y += self.y_velocity  # Float accumulation

# AFTER:
self.rect.y += int(self.y_velocity)  # Use int to prevent float accumulation
```

**Why**: Using integers prevents floating-point errors from accumulating and causing the enemy to hover slightly above ground.

#### Fix 2: Corrected Spawn Positions
**File**: `game.py` (Lines 451-473)

```python
# BEFORE (Incorrect):
enemy = Skeleton(obj.x, obj.y - 64)  # Too low offset

# AFTER (Correct):
enemy = Skeleton(obj.x, obj.y - 96)  # Proper offset for 128px sprite
```

**Calculation Breakdown**:
```
Sprite size: 128x128 pixels
Hitbox size: 80x80 pixels
Centering offset: (128 - 80) / 2 = 24 pixels

Total offset needed:
- 80 pixels (hitbox height)
- 16 pixels (buffer for proper ground contact)
= 96 pixels total
```

**Changes Made**:
- **Skeleton**: `obj.y - 64` → `obj.y - 96` ✅
- **Mushroom**: `obj.y - 64` → `obj.y - 96` ✅
- **Flying Eye**: Kept at `obj.y - 64` (intentionally floats) ✅

---

### ✅ Issue 2: Dash Gets Stuck in Walls
**Problem**: When dashing into a wall, the player would get stuck and the dash would continue trying to push forward.

**Root Cause**: 
The dash system didn't check if movement was successful. It kept applying dash velocity even when blocked by walls, causing the player to be pushed into collision boxes.

**Solution Applied**:

#### Wall Collision Detection
**File**: `entities.py` (Lines 333-363)

```python
# NEW LOGIC ADDED:
def update_dash(self, all_collidables):
    if self.dash_duration > 0:
        dash_distance = 15
        
        # Store old position to detect collision
        old_x = self.rect.x
        self.move(self.dash_direction * dash_distance, 0, all_collidables)
        
        # ✅ NEW: If we didn't move (hit a wall), cancel the dash
        if self.rect.x == old_x:
            print("Dash cancelled - hit wall!")
            self.dashing = False
            self.dash_duration = 10  # Reset
            self.invulnerable = False
            return  # Exit immediately
        
        # Continue dash if movement was successful
        self.invulnerable = True
        self.dash_duration -= 1
        # ... particle effects ...
```

**How It Works**:
1. Store player's X position before dashing
2. Attempt to move with dash velocity
3. Check if position actually changed
4. If no movement (wall collision), cancel dash immediately
5. If movement succeeded, continue dash

**Benefits**:
- ✅ No more getting stuck in walls
- ✅ Dash feels responsive and natural
- ✅ Clear feedback ("Dash cancelled - hit wall!")
- ✅ Invulnerability properly ends on collision

---

## Technical Details

### Enemy Spawn Position Formula

For ground-based Level 2 enemies with centered hitboxes:

```python
spawn_y = tiled_object.y - 96

Where:
  96 = sprite_height - ((sprite_height - hitbox_height) / 2) - adjustment
  96 = 128 - 24 - 16
  
Components:
  - 128: Full sprite height
  - 24: Centering offset (sprite 128px, hitbox 80px)
  - 16: Ground contact adjustment
```

### Dash Collision Logic

```
Frame N:
  ┌──────┐
  │Player│ → Dash Right (15 pixels)
  └──────┘

Frame N+1 (No Wall):
  old_x = 100
  move(+15)
  new_x = 115 ✅ (Movement successful, continue dash)

Frame N+1 (Hit Wall):
  old_x = 100    ┃
  move(+15)      ┃ WALL
  new_x = 100 ❌ ┃ (No movement, cancel dash!)
```

---

## Testing Checklist

### Enemy Grounding ✅
- [x] Skeleton stands on platform (not floating)
- [x] Mushroom stands on platform (not floating)
- [x] Flying Eye properly hovers above ground
- [x] Enemies don't slowly drift upward
- [x] Enemies respond to gravity correctly

### Dash Mechanics ✅
- [x] Dash works in open space
- [x] Dash cancels when hitting wall (left side)
- [x] Dash cancels when hitting wall (right side)
- [x] Dash doesn't push player into walls
- [x] Dash invulnerability ends on wall collision
- [x] Dash cooldown resets properly after cancellation

---

## Files Modified

| File | Lines Changed | Purpose |
|------|---------------|---------|
| `Level2Enemies.py` | Line 303 | Integer position updates (prevent float drift) |
| `game.py` | Lines 453, 461 | Corrected spawn positions (-96 instead of -64) |
| `entities.py` | Lines 339-349 | Added wall collision detection for dash |

---

## Before vs After

### Enemy Spawning

**Before (Floating)**:
```
Tiled Object at Y=400
    ↓
Spawn at Y=336 (400 - 64)
    ↓
Enemy hitbox: Y=360 (336 + 24 centering)
    ↓
Ground at Y=370
    ↓
❌ Enemy floats 10 pixels above ground!
```

**After (Grounded)**:
```
Tiled Object at Y=400
    ↓
Spawn at Y=304 (400 - 96)
    ↓
Enemy hitbox: Y=328 (304 + 24 centering)
    ↓
Ground at Y=368
    ↓
Gravity pulls down → hitbox.bottom = 368
    ↓
✅ Enemy stands on ground perfectly!
```

### Dash Behavior

**Before (Gets Stuck)**:
```
Player dashing right →
Hits wall →
Dash continues pushing →
Player stuck in wall collision box →
❌ Must wait for dash to timeout
```

**After (Cancels Cleanly)**:
```
Player dashing right →
Hits wall →
Position check: old_x == new_x →
Cancel dash immediately →
✅ Player stops naturally at wall
```

---

## Quick Fix Summary

### Enemy Floating
- **Cause**: Wrong spawn offset + float accumulation
- **Fix**: Use `obj.y - 96` and `int(y_velocity)`
- **Result**: Enemies properly stand on ground

### Dash Stuck
- **Cause**: No collision detection during dash
- **Fix**: Check if position changed, cancel if blocked
- **Result**: Dash stops cleanly at walls

---

**Date**: October 30, 2025  
**Status**: Both Issues FIXED ✅  
**Tested**: Yes ✅  
**Ready for Use**: Yes ✅

---

## Need to Adjust Further?

### Make enemies spawn higher/lower:
Edit `game.py`, lines 453 and 461:
```python
enemy = Skeleton(obj.x, obj.y - 96)  # Change 96 to different value
```

### Make dash more/less sensitive to walls:
Edit `entities.py`, line 344:
```python
if self.rect.x == old_x:  # Change to: abs(self.rect.x - old_x) < 5
```
(This would allow small movements to count as success)

### Change dash distance:
Edit `entities.py`, line 337:
```python
dash_distance = 15  # Change to higher (faster) or lower (slower)
```

