"""
=============================================================
  tools.py — Tool logic for TSIS 2 Paint Application
  Contains:
    - Mode ID constants
    - Geometry helpers for all shapes
    - CanvasEngine: bucket_fill(), render_shape()
=============================================================
"""

import math
import pygame
from collections import deque

# ─────────────────────────────────────────────
#  MODE ID CONSTANTS
# ─────────────────────────────────────────────
MODE_PENCIL  = "pencil"
MODE_ERASER  = "eraser"
MODE_FILL    = "fill"
MODE_TEXT    = "text"
MODE_LINE    = "line"
MODE_RECT    = "rect"
MODE_SQUARE  = "square"
MODE_CIRCLE  = "circle"
MODE_RTRI    = "right_tri"
MODE_ETRI    = "equil_tri"
MODE_RHOMBUS = "rhombus"

# Modes that require drag interaction (mouse down → drag → mouse up)
DRAG_MODES = {
    MODE_RHOMBUS,
    MODE_ETRI,
    MODE_RTRI,
    MODE_CIRCLE,
    MODE_SQUARE,
    MODE_RECT,
    MODE_LINE,
}


# ─────────────────────────────────────────────
#  GEOMETRY HELPERS
# ─────────────────────────────────────────────

def make_rhombus_corners(ax, ay, bx, by):
    """
    Rhombus (diamond) inscribed in the bounding rectangle.
    Vertices at midpoints of each side.
    """
    left_x   = min(ax, bx)
    right_x  = max(ax, bx)
    top_y    = min(ay, by)
    bottom_y = max(ay, by)
    mid_x    = (left_x + right_x)  // 2
    mid_y    = (top_y  + bottom_y) // 2
    return [(mid_x, top_y), (right_x, mid_y), (mid_x, bottom_y), (left_x, mid_y)]


def make_equi_tri_corners(ax, ay, bx, by):
    """
    Equilateral triangle with base along the bottom of the drag rect.
    Height = base * sqrt(3) / 2.
    """
    left_x  = min(ax, bx)
    right_x = max(ax, bx)
    base    = right_x - left_x
    height  = int(base * math.sqrt(3) / 2)
    bottom  = max(ay, by)
    apex    = (left_x + base // 2, bottom - height)
    return [apex, (left_x, bottom), (right_x, bottom)]


def make_right_tri_corners(ax, ay, bx, by):
    """
    Right-angle triangle.
    Right angle at bottom-left (ax, by), apex at (ax, ay), hypotenuse to (bx, by).
    """
    return [(ax, ay), (ax, by), (bx, by)]


def make_square_corners(ax, ay, bx, by):
    """
    Four corners of a square.
    Side length = min(|dx|, |dy|) so it stays square regardless of drag direction.
    """
    delta_x = bx - ax
    delta_y = by - ay
    side    = min(abs(delta_x), abs(delta_y))
    step_x  = side * (1 if delta_x >= 0 else -1)
    step_y  = side * (1 if delta_y >= 0 else -1)
    return [(ax, ay), (ax + step_x, ay), (ax + step_x, ay + step_y), (ax, ay + step_y)]


# ─────────────────────────────────────────────
#  CANVAS ENGINE
# ─────────────────────────────────────────────

class CanvasEngine:
    """
    Handles drawing shapes and bucket-fill.
    Used both for live preview (onto window surface)
    and final commit (onto draw layer surface).
    """

    # ── Bucket Fill ───────────────────────────────────────────────────────
    def bucket_fill(self, layer, x, y, fill_color):
        """
        Iterative BFS flood fill using pygame.Surface.get_at() / set_at().
        Fills all connected pixels of the same color as (x, y)
        with fill_color. Stops at boundaries of a different color.

        Parameters:
            layer      — pygame.Surface to fill (the draw layer)
            x, y       — starting pixel coordinates (click position)
            fill_color — (R, G, B) tuple of the replacement color
        """
        # Clamp click to surface bounds
        layer_w, layer_h = layer.get_size()
        if not (0 <= x < layer_w and 0 <= y < layer_h):
            return

        # Get the color we are replacing (target color)
        target_rgb = layer.get_at((x, y))[:3]   # ignore alpha

        # Normalise fill color to (R, G, B)
        replacement_rgb = fill_color[:3]

        # Nothing to do if target already matches fill
        if target_rgb == replacement_rgb:
            return

        # BFS queue — use a deque for O(1) popleft
        pending = deque()
        pending.append((x, y))
        seen = set()
        seen.add((x, y))

        while pending:
            px, py = pending.popleft()

            # Skip if this pixel has drifted from the target color
            # (can happen at shape edges due to anti-aliasing or
            #  if we've already filled it)
            here = layer.get_at((px, py))[:3]
            if here != target_rgb:
                continue

            # Paint this pixel
            layer.set_at((px, py), replacement_rgb)

            # Check all 4 neighbours (cardinal directions only)
            for nx, ny in ((px + 1, py), (px - 1, py), (px, py + 1), (px, py - 1)):
                if (0 <= nx < layer_w and 0 <= ny < layer_h
                        and (nx, ny) not in seen):
                    seen.add((nx, ny))
                    pending.append((nx, ny))

    # ── Shape rendering ───────────────────────────────────────────────────
    def render_shape(self, layer, mode, anchor, cursor, color, thickness):
        """
        Draw the appropriate shape for `mode` onto `layer`.
        `anchor` and `cursor` are (x, y) tuples from mouse-down and current/up position.
        `thickness` is the outline stroke width in pixels.
        """
        ax, ay = anchor
        bx, by = cursor
        stroke = max(1, thickness)

        if mode == MODE_LINE:
            # Straight line between two points
            pygame.draw.line(layer, color, (ax, ay), (bx, by), stroke)

        elif mode == MODE_RECT:
            left_x = min(ax, bx)
            top_y  = min(ay, by)
            box_w  = abs(bx - ax)
            box_h  = abs(by - ay)
            if box_w > 1 and box_h > 1:
                pygame.draw.rect(layer, color, (left_x, top_y, box_w, box_h), stroke)

        elif mode == MODE_SQUARE:
            corners = make_square_corners(ax, ay, bx, by)
            # Only draw if the square has non-zero size
            if abs(bx - ax) > 2 and abs(by - ay) > 2:
                pygame.draw.polygon(layer, color, corners, stroke)

        elif mode == MODE_CIRCLE:
            mid_x  = (ax + bx) // 2
            mid_y  = (ay + by) // 2
            radius = int(math.hypot(bx - ax, by - ay) / 2)
            if radius > 1:
                pygame.draw.circle(layer, color, (mid_x, mid_y), radius, stroke)

        elif mode == MODE_RTRI:
            corners = make_right_tri_corners(ax, ay, bx, by)
            pygame.draw.polygon(layer, color, corners, stroke)

        elif mode == MODE_ETRI:
            corners = make_equi_tri_corners(ax, ay, bx, by)
            if len(corners) == 3:
                pygame.draw.polygon(layer, color, corners, stroke)

        elif mode == MODE_RHOMBUS:
            corners = make_rhombus_corners(ax, ay, bx, by)
            if abs(bx - ax) > 2 and abs(by - ay) > 2:
                pygame.draw.polygon(layer, color, corners, stroke)
