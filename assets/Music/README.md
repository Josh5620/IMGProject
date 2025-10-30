# 🎵 Background Music Files

Place your background music files in this folder with the following names:

## Required Files (all in MP3 format):

1. **`IntroBackgroundMusic.mp3`** - Plays on the main menu and level select screens
2. **`ForestLevelBackgroundMusic.mp3`** - Plays during Level 1 gameplay
3. **`DungeonLevelBackgroundMusic.mp3`** - Plays during Level 2 gameplay  
4. **`BossLevelBackgroundMusic.mp3`** - Plays during boss battle

## Format Requirements:
- ✅ **MP3 format** is supported
- ❌ **MP4 format** is NOT supported (it's a video format)
- If you have MP4 files, convert them to MP3 first

## How It Works:
- Music automatically loops infinitely
- Music pauses when you open the pause menu (ESC key)
- Music resumes when you continue playing
- Volume is set to 50% by default (adjustable in code)
- Transitions smoothly between different game states

## To Convert MP4 to MP3:
You can use online converters like:
- https://cloudconvert.com/mp4-to-mp3
- https://convertio.co/mp4-mp3/
- Or use FFmpeg: `ffmpeg -i input.mp4 -vn -acodec libmp3lame output.mp3`

## Volume Adjustment:
If you want to change the volume, edit `menus.py` and change:
```python
self.music_volume = 0.5  # Change this value (0.0 to 1.0)
```

## Troubleshooting:
- If music doesn't play, check that the file names match exactly (case-sensitive)
- Check the console for error messages starting with ⚠️
- Make sure files are in MP3 format
- Verify that the files are not corrupted

