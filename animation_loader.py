"""Utility helpers for slicing single-row sprite sheets into animation frames."""
from __future__ import annotations

from typing import List, Optional

import pygame


class SpriteSheetError(RuntimeError):
    """Exception raised when a sprite sheet cannot be processed."""


def load_animation_frames(
    path: str,
    *,
    frame_width: Optional[int] = None,
    frame_count: Optional[int] = None,
) -> List[pygame.Surface]:
    """Load animation frames from a single-row sprite sheet.

    Parameters
    ----------
    path:
        File system path to the sprite sheet image.
    frame_width:
        Explicit width for each frame in the sheet. Preferred over ``frame_count``
        when provided.
    frame_count:
        Number of frames contained in the sheet. Used only when ``frame_width``
        is not supplied.

    The sprite sheets are expected to be laid out horizontally (one row).  If
    neither ``frame_width`` nor ``frame_count`` is provided, the loader assumes
    square frames by using the sheet's height as the width.
    """

    if frame_width is not None and frame_width <= 0:
        raise SpriteSheetError("frame_width must be a positive integer")

    if frame_count is not None and frame_count <= 0:
        raise SpriteSheetError("frame_count must be a positive integer")

    sheet = pygame.image.load(path).convert_alpha()
    sheet_width = sheet.get_width()
    sheet_height = sheet.get_height()

    if frame_width is None:
        if frame_count is not None:
            frame_width = sheet_width // frame_count
            if frame_width <= 0:
                raise SpriteSheetError(
                    "Computed frame width is non-positive; check frame_count or sheet dimensions."
                )
        else:
            frame_width = sheet_height  # Fallback to square frames

    if frame_width > sheet_width:
        raise SpriteSheetError(
            "frame_width exceeds the width of the sprite sheet"
        )

    # Derive frame_count if not explicitly provided (or recompute to ensure it fits)
    frame_count = frame_count or max(sheet_width // frame_width, 1)

    frames: List[pygame.Surface] = []
    for index in range(frame_count):
        x = index * frame_width
        if x >= sheet_width:
            break
        width = min(frame_width, sheet_width - x)
        rect = pygame.Rect(x, 0, width, sheet_height)
        frame = sheet.subsurface(rect).copy()
        frames.append(frame)

    if not frames:
        raise SpriteSheetError("No frames could be extracted from the sprite sheet")

    return frames
