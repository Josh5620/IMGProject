# Level 2 Powerup System - Complete Guide

## Overview

Level 2 now has a fully functional powerup system using **mushroom sprites** from your `mushroom level 2.png` spritesheet! Each powerup type automatically uses a different mushroom sprite from the third row of the sheet.

---

## Powerup Types & Effects

| Object Name (Tiled) | Powerup Type | Effect | Mushroom Sprite |
|---------------------|--------------|--------|-----------------|
| `health_mushroom` | health_burst | Restores all hearts to maximum | Column 0 (Row 2) |
| `fire_mushroom` | fire_cloak | 15 seconds of invincibility | Column 1 (Row 2) |
| `speed_mushroom` | speed_wind | 15 seconds of 2x speed | Column 2 (Row 2) |
| `strength_mushroom` | wolf_strength | 15 seconds of 3x damage | Column 3 (Row 2) |
| `amulet_mushroom` | grandma_amulet | 10 seconds shield protection | Column 4 (Row 2) |
| `wisdom_mushroom` | forest_wisdom | Ultimate combo ability | Column 5 (Row 2) |

---

## How to Add Powerups in Tiled

### Step 1: Open Your Level 2 Map
Open `DungeonMapActual.tmx` in Tiled

### Step 2: Select the Object Layer
Click on "Object Layer 1" (or your objects layer)

### Step 3: Insert a Point or Rectangle
Use the "Insert Point" (I key) or "Insert Rectangle" (R key) tool

### Step 4: Place the Object
Click where you want the powerup to appear

### Step 5: Add the Type Property
1. With the object selected, go to Properties panel
2. Add a custom property:
   - **Name**: `type`
   - **Type**: `string`
   - **Value**: One of the object names from the table above

### Example:
```
Object Properties:
  Name: (leave blank or name it)
  Type: string
  Value: health_mushroom  ← This spawns a health powerup!
```

---

## Sprite Configuration

### Current Setup (Default)
- **Spritesheet**: `assets/Level2/mushroom level 2.png`
- **Row**: 2 (third row, 0-indexed)
- **Sprite Size**: 32x32 pixels per mushroom
- **Scaled To**: 40x40 pixels in-game

### To Change Which Row Is Used

Edit `level2_powerup_loader.py`, line ~10:

```python
def load_mushroom_sprites(sprite_sheet_path="assets/Level2/mushroom level 2.png", 
                         row=2,  # ← Change this number (0 = first row, 1 = second, etc.)
                         sprite_width=32,  # ← Adjust if your sprites are different size
                         sprite_height=32):
```

### To Change Sprite Mapping

Edit `level2_powerup_loader.py`, lines ~24-31:

```python
powerup_types = [
    "health_burst",      # Column 0 ← Uses 1st mushroom in row
    "fire_cloak",        # Column 1 ← Uses 2nd mushroom in row
    "speed_wind",        # Column 2 ← Uses 3rd mushroom in row
    "wolf_strength",     # Column 3 ← Uses 4th mushroom in row
    "grandma_amulet",    # Column 4 ← Uses 5th mushroom in row
    "forest_wisdom"      # Column 5 ← Uses 6th mushroom in row
]
```

Change the order to map different mushrooms to different powerups!

---

## Powerup Effects (Detailed)

### 🔴 Health Burst (`health_mushroom`)
- **Effect**: Instant full health restoration
- **Lives**: Restores to 10 (maximum)
- **Visual**: Red/pink glow with heart particles

### 🔥 Fire Cloak (`fire_mushroom`)
- **Effect**: Complete invincibility for 15 seconds
- **Protection**: Immune to all damage (enemies, traps, etc.)
- **Visual**: Yellow/orange fiery aura

### 💨 Speed Wind (`speed_mushroom`)
- **Effect**: 2x movement speed for 15 seconds
- **Speed**: 200% of normal speed
- **Visual**: Blue wind trails and motion blur

### 💪 Wolf Strength (`strength_mushroom`)
- **Effect**: 3x damage multiplier for 15 seconds
- **Damage**: All attacks deal triple damage
- **Visual**: Brown/orange power aura with sparks

### 🛡️ Grandma's Amulet (`amulet_mushroom`)
- **Effect**: Shield absorbs one hit for 10 seconds
- **Protection**: Blocks first damage, then disappears
- **Visual**: Pink protective shield bubble

### 🌲 Forest Wisdom (`wisdom_mushroom`)
- **Effect**: Ultimate combo ability (all buffs!)
- **Buffs**: 1.5x speed, 2x damage, shield, +3 health, full ammo
- **Duration**: 10 seconds for all effects
- **Visual**: Green mystical aura

---

## Testing Your Powerups

### Quick Test
1. Run `python level2_powerup_loader.py` to verify sprites load correctly
2. You should see:
```
============================================================
LEVEL 2 POWERUP LOADER - TEST
============================================================

✅ Successfully loaded 6 mushroom sprites:
  - health_burst
  - fire_cloak
  - speed_wind
  - wolf_strength
  - grandma_amulet
  - forest_wisdom

📍 Tiled Object Names:
  - 'health_mushroom' → health_burst
  - 'fire_mushroom' → fire_cloak
  - 'speed_mushroom' → speed_wind
  - 'strength_mushroom' → wolf_strength
  - 'amulet_mushroom' → grandma_amulet
  - 'wisdom_mushroom' → forest_wisdom
============================================================
```

### In-Game Test
1. Add powerup objects to your Tiled map (see "How to Add Powerups" above)
2. Save the map
3. Run `python main.py`
4. Select Level 2
5. Look for console output:
```
✅ Loaded 6 mushroom powerup sprites
Level 2 - Number of powerups spawned: 3
Spawned health_burst powerup at (320, 384)
Spawned speed_wind powerup at (640, 384)
Spawned wolf_strength powerup at (960, 384)
```
6. Walk over the mushrooms to collect them!

---

## Visual Features

All powerups have:
- ✨ **Bobbing animation** - Gentle up/down floating
- 💫 **Pulsing glow** - Rhythmic size changes
- ⭐ **Sparkle particles** - Rotating stars around the mushroom
- 🎨 **Color-coded glow** - Each type has unique colors
- 🎆 **Collection effects** - Particle burst when collected

---

## Troubleshooting

### Problem: "Could not load mushroom sprites"
**Solution**: Check that `assets/Level2/mushroom level 2.png` exists

### Problem: Powerups don't spawn
**Solution**: 
- Verify object `type` property is spelled exactly as shown in table
- Check console output for spawn messages
- Make sure objects are in "Object Layer 1"

### Problem: Wrong mushroom sprite appears
**Solution**: 
- Check the `row` parameter in `load_mushroom_sprites()`
- Verify sprite sheet has correct layout (8 columns)
- Try different row numbers (0, 1, 2, 3...)

### Problem: Mushroom sprites are too small/large
**Solution**: Edit `level2_powerup_loader.py`, line ~43:
```python
sprite = pygame.transform.scale(sprite, (40, 40))  # ← Change size here
```

### Problem: Powerup collected but no effect
**Solution**: Check that player has `apply_level2_powerup()` method in `entities.py`

---

## Files Modified

### New Files Created:
- ✅ `level2_powerup_loader.py` - Sprite extraction and powerup creation
- ✅ `LEVEL2_POWERUP_GUIDE.md` - This documentation

### Existing Files Modified:
- ✅ `game.py` - Added powerup system to Level 2 class
- ℹ️ `level2_powerups.py` - Already existed (effects logic)
- ℹ️ `entities.py` - Already has `apply_level2_powerup()` method

---

## Quick Reference Card

```
╔═══════════════════════════════════════════════════════════╗
║             LEVEL 2 POWERUP QUICK REFERENCE               ║
╠═══════════════════════════════════════════════════════════╣
║ Tiled Object Name  │ Effect              │ Duration       ║
╠════════════════════╪═════════════════════╪════════════════╣
║ health_mushroom    │ Restore all hearts  │ Instant        ║
║ fire_mushroom      │ Invincibility       │ 15 seconds     ║
║ speed_mushroom     │ 2x Speed            │ 15 seconds     ║
║ strength_mushroom  │ 3x Damage           │ 15 seconds     ║
║ amulet_mushroom    │ Shield (1 hit)      │ 10 seconds     ║
║ wisdom_mushroom    │ All abilities!      │ 10 seconds     ║
╚════════════════════╧═════════════════════╧════════════════╝
```

---

**Happy Level Designing! 🍄**

*All mushroom sprites are automatically extracted from row 2 (third row) of your spritesheet!*

