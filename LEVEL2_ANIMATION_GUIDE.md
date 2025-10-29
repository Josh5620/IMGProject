# Level 2 Enemy Animation System Guide

## ✅ What Was Implemented

All Level 2 enemies now support **PNG sprite sheet animations** identical to how Level 1 enemies work!

## 🎮 Supported Enemies (7 Total)

### Regular Enemies (6):
1. **WolfEnemy** - Ferocious wolf with bite attacks
2. **ShadowCreature** - Dark enemy that phases through walls
3. **DarkEnchanter** - Ranged magical spellcaster
4. **MutatedMushroom** - Poison cloud attacks (uses custom grid-based loader)
5. **Skeleton** - Ranged bone-throwing enemy
6. **FlyingMonster** - Aerial dive attacker

### Boss (1):
7. **ForestBoss** (formerly Level2Boss) - Multi-phase ultimate boss

## 🎨 How It Works

### Animation System Features:
- ✅ Frame-based PNG sprite sheet support (one-row horizontal frames)
- ✅ Automatic frame slicing and scaling
- ✅ State-based animations: `idle`, `run`, `attack`
- ✅ Automatic horizontal flipping for direction
- ✅ Fallback to colored placeholders if sprites don't exist
- ✅ Same system as Level 1 (Warrior, Archer)

### Animation States:
Each enemy automatically switches between:
- **Idle** - When standing still
- **Run** - When moving
- **Attack** - When performing attacks

## 📁 Required Directory Structure

Place your PNG sprite sheets in this structure:

```
assets/Level2/
├── Wolf/
│   ├── Idle.png
│   ├── Run.png
│   └── Attack.png
├── ShadowCreature/
│   ├── Idle.png
│   ├── Run.png
│   └── Attack.png
├── DarkEnchanter/
│   ├── Idle.png
│   ├── Run.png
│   └── Attack.png
├── Skeleton/
│   ├── Idle.png
│   ├── Run.png
│   └── Attack.png
├── FlyingMonster/
│   ├── Idle.png
│   ├── Fly.png      (instead of Run.png)
│   └── Attack.png
└── ForestBoss/
    ├── Idle.png     (64px frame width)
    ├── Run.png      (64px frame width)
    └── Attack.png   (64px frame width)
```

## 🖼️ Sprite Sheet Format

### Standard Enemies (Wolf, Shadow, Skeleton, Flying):
- **Format**: One-row horizontal sprite sheet
- **Frame Width**: 48 pixels
- **Frame Height**: Any height (will be scaled to 48px)
- **Number of Frames**: Any (will be auto-detected)
- **Example**: If sheet is 384px wide with 48px frames = 8 frames

### Boss (ForestBoss):
- **Frame Width**: 64 pixels (larger for boss)
- **Frame Height**: Any (will be scaled to 64px)

### Dark Enchanter:
- **Frame Width**: 64 pixels

## 🔧 Configuration

Animation manifests are defined at the top of `Level2Enemies.py`:

```python
# Example for Wolf Enemy
WOLF_ENEMY_ANIM = {
    "idle":   {"file": "assets/Level2/Wolf/Idle.png",   "frame_width": 48},
    "run":    {"file": "assets/Level2/Wolf/Run.png",    "frame_width": 48},
    "attack": {"file": "assets/Level2/Wolf/Attack.png", "frame_width": 48}
}
```

## 📝 How to Add Animations

1. **Create your sprite sheets**:
   - One row of frames, side-by-side
   - Each frame should be the same width
   - Save as PNG with transparency

2. **Place in correct folder**:
   - `assets/Level2/[EnemyName]/[State].png`

3. **Update frame_width** in the animation manifest (if needed):
   - Open `Level2Enemies.py`
   - Find the enemy's ANIM dictionary
   - Set correct `frame_width` value

4. **Done!** The game will automatically:
   - Load the sprite sheet
   - Slice it into frames
   - Scale frames to appropriate size
   - Animate the enemy

## 🎯 Key Changes Made

### 1. Animation Manifests
- Added complete ANIM dictionaries for all 7 enemies
- Includes paths and frame widths

### 2. Updated Enemy Classes
All enemies now have:
- Animation loading with try/catch fallback
- `update_animation()` method for state-based animation
- Automatic frame updates in `update()` method
- Direction-based sprite flipping

### 3. Backward Compatibility
- Game works WITHOUT sprite sheets (uses colored placeholders)
- No errors if assets don't exist
- Graceful fallback system

## 🔍 Testing

To test if animations are loaded, run:
```bash
python Level2Enemies.py
```

This will analyze your sprite sheets and show:
- Frame counts
- Dimensions
- Whether files exist

## 🎨 Animation Examples (from Level 1)

Look at these working examples:
- `assets/Level1/Warrior/Run.png` - 320x64px (8 frames @ 40px each)
- `assets/Level1/Warrior/Attack.png` - 200x64px (5 frames @ 40px each)
- `assets/Level1/Archer/Run.png` - 512x64px (8 frames @ 64px each)
- `assets/Level1/Archer/Attack.png` - 704x64px (11 frames @ 64px each)

## 💡 Tips

1. **Keep frame widths consistent** within each enemy
2. **Use transparency** for clean edges
3. **Test with placeholder first** to verify game logic
4. **Match Level 1 style** for visual consistency
5. **Boss is bigger** (64px vs 48px frames)

## 🚀 Next Steps

1. Create or obtain sprite sheets for your enemies
2. Place them in the correct folders
3. Verify frame_width in manifests
4. Test in game!

---

**Status**: ✅ Animation system fully implemented and ready for assets!
