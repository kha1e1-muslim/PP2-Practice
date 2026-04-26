"""
=============================================================
  PAINT APPLICATION — TSIS 2
  Extends Practice 10 & Practice 11 with:
    - Pencil (freehand) tool
    - Straight line tool with live preview
    - Three brush size levels: small(2), medium(5), large(10)
      switchable via keys 1/2/3 or on-screen buttons
    - Flood-fill tool (get_at / set_at, no extra libs)
    - Ctrl+S saves canvas as timestamped .png
    - Text tool: click → type → Enter to confirm / Escape to cancel
    - All Practice 10+11 shapes respect active brush size
=============================================================
"""

import sys
import pygame
from datetime import datetime
from tools import (
    CanvasEngine,
    DRAG_MODES,
    MODE_PENCIL, MODE_LINE, MODE_RECT, MODE_SQUARE,
    MODE_CIRCLE, MODE_RTRI, MODE_ETRI, MODE_RHOMBUS,
    MODE_ERASER, MODE_FILL, MODE_TEXT,
)

# ─────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────
WIN_WIDTH      = 1100
WIN_HEIGHT     = 720
PANEL_HEIGHT   = 100
CANVAS_HEIGHT  = WIN_HEIGHT - PANEL_HEIGHT
FRAMES_PER_SEC = 60

COL_WHITE    = (255, 255, 255)
COL_BLACK    = (0,   0,   0)
COL_PANEL_BG = (35,  35,  35)
COL_ACTIVE   = (255, 215, 50)

COLOR_SWATCHES = [
    (0,   0,   0),   (255, 255, 255), (220, 30,  30),  (30,  180, 30),
    (30,  30,  220), (255, 200, 0),   (255, 140, 0),   (180, 0,   180),
    (0,   200, 200), (180, 100, 40),  (255, 182, 193), (128, 128, 128),
    (0,   100, 0),   (0,   0,   128), (255, 69,  0),   (173, 216, 230),
]

# Brush size presets
SIZE_PRESETS = {1: 2, 2: 5, 3: 10}


# ─────────────────────────────────────────────
#  BUTTONS
# ─────────────────────────────────────────────
class BrushSizeButton:
    """Button for selecting brush size preset (1/2/3)."""
    def __init__(self, rect, label, size_id):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.size_id = size_id
        self.font    = pygame.font.SysFont("consolas", 11, bold=True)

    def draw(self, surface, active_size_id):
        is_active = self.size_id == active_size_id
        bg_col    = (100, 180, 255) if is_active else (70, 70, 70)
        edge_col  = (255, 255, 255) if is_active else (50, 50, 50)
        pygame.draw.rect(surface, bg_col,   self.rect, border_radius=5)
        pygame.draw.rect(surface, edge_col, self.rect, 2, border_radius=5)
        rendered = self.font.render(self.label, True, COL_BLACK if is_active else (200, 200, 200))
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class ToolButton:
    def __init__(self, rect, label, mode_id):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.mode_id = mode_id
        self.font    = pygame.font.SysFont("consolas", 11, bold=True)

    def draw(self, surface, active_mode):
        is_active = self.mode_id == active_mode
        bg_col    = COL_ACTIVE        if is_active else (80, 80, 80)
        edge_col  = (255, 255, 255)   if is_active else (55, 55, 55)
        pygame.draw.rect(surface, bg_col,   self.rect, border_radius=6)
        pygame.draw.rect(surface, edge_col, self.rect, 2, border_radius=6)
        rendered = self.font.render(self.label, True, COL_BLACK if is_active else (220, 220, 220))
        surface.blit(rendered, rendered.get_rect(center=self.rect.center))

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


# ─────────────────────────────────────────────
#  PAINT STUDIO
# ─────────────────────────────────────────────
class PaintStudio:
    def __init__(self):
        pygame.init()
        self.window     = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
        pygame.display.set_caption("Paint — TSIS 2")
        self.tick_clock = pygame.time.Clock()

        self.draw_layer = pygame.Surface((WIN_WIDTH, CANVAS_HEIGHT))
        self.draw_layer.fill(COL_WHITE)

        # Current state
        self.active_mode   = MODE_PENCIL
        self.active_color  = COL_BLACK
        self.size_index    = 2              # 1=small, 2=medium, 3=large
        self.stroke_width  = SIZE_PRESETS[self.size_index]
        self.eraser_radius = 18

        # Drag state (shapes, line)
        self.is_dragging    = False
        self.drag_origin    = None
        self.pre_drag_layer = None

        # Pencil trail
        self.last_point = None

        # Text tool state
        self.typing_mode    = False
        self.caret_pos      = None    # (x, y) on canvas
        self.typed_text     = ""
        self.label_font     = pygame.font.SysFont("arial", 22)
        self.pre_text_layer = None   # canvas before text

        # Canvas engine (handles shapes, fill, etc.)
        self.engine = CanvasEngine()

        self._build_ui()

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        panel_y = CANVAS_HEIGHT + 5
        btn_w   = 74
        btn_h   = 30
        gap     = 5
        origin_x = 6

        mode_defs = [
            ("✏ Pencil",   MODE_PENCIL),
            ("/ Line",     MODE_LINE),
            ("▭ Rect",     MODE_RECT),
            ("■ Square",   MODE_SQUARE),
            ("○ Circle",   MODE_CIRCLE),
            ("◺ R.Tri",    MODE_RTRI),
            ("△ Eq.Tri",   MODE_ETRI),
            ("◇ Rhombus",  MODE_RHOMBUS),
            ("⌫ Eraser",   MODE_ERASER),
            ("🪣 Fill",     MODE_FILL),
            ("T Text",     MODE_TEXT),
        ]

        self.tool_buttons = [
            ToolButton((origin_x + i * (btn_w + gap), panel_y + 4, btn_w, btn_h), lbl, mid)
            for i, (lbl, mid) in enumerate(mode_defs)
        ]

        # Brush size buttons
        sz_x = origin_x
        sz_y = panel_y + btn_h + 12
        self.brush_buttons = [
            BrushSizeButton((sz_x + i * 44, sz_y, 40, 22), lbl, sid)
            for i, (lbl, sid) in enumerate([
                ("S:2", 1), ("M:5", 2), ("L:10", 3)
            ])
        ]

        # Clear button
        self.clear_rect = pygame.Rect(sz_x + 3 * 44 + 6, sz_y, 56, 22)

        # Palette
        sw_size  = 22
        sw_gap   = 3
        pal_x    = origin_x + len(mode_defs) * (btn_w + gap) + 12
        pal_y    = panel_y + 4
        self.swatch_rects = []
        for i, c in enumerate(COLOR_SWATCHES):
            cx = pal_x + (i % 8) * (sw_size + sw_gap)
            cy = pal_y + (i // 8) * (sw_size + sw_gap)
            self.swatch_rects.append((pygame.Rect(cx, cy, sw_size, sw_size), c))

        self.label_font_small = pygame.font.SysFont("consolas", 11, bold=True)

    # ── Size helper ───────────────────────────────────────────────────────
    def _set_size(self, sid):
        self.size_index   = sid
        self.stroke_width = SIZE_PRESETS[sid]

    # ── Save ──────────────────────────────────────────────────────────────
    def _show_save_flash(self, filename):
        """Draw a brief 'Saved!' notification directly on screen."""
        self._save_msg   = f"✅ Saved: {filename}"
        self._save_timer = 150   # frames to show (2.5 s at 60fps)

    def _save_canvas(self):
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"canvas_{ts}.png"
        pygame.image.save(self.draw_layer, filename)
        self._show_save_flash(filename)

    # ── Text Tool Helpers ─────────────────────────────────────────────────
    def _start_text(self, x, y):
        self.typing_mode    = True
        self.caret_pos      = (x, y)
        self.typed_text     = ""
        self.pre_text_layer = self.draw_layer.copy()

    def _cancel_text(self):
        """Restore canvas to before text was started."""
        if self.pre_text_layer:
            self.draw_layer.blit(self.pre_text_layer, (0, 0))
        self.typing_mode    = False
        self.caret_pos      = None
        self.typed_text     = ""
        self.pre_text_layer = None

    def _commit_text(self):
        """Render text permanently onto canvas."""
        if self.typed_text and self.caret_pos:
            rendered = self.label_font.render(self.typed_text, True, self.active_color)
            self.draw_layer.blit(rendered, self.caret_pos)
        self.typing_mode    = False
        self.caret_pos      = None
        self.typed_text     = ""
        self.pre_text_layer = None

    def _handle_text_key(self, event):
        if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
            self._commit_text()
        elif event.key == pygame.K_ESCAPE:
            self._cancel_text()
        elif event.key == pygame.K_BACKSPACE:
            self.typed_text = self.typed_text[:-1]
        else:
            ch = event.unicode
            if ch and ch.isprintable():
                self.typed_text += ch

    # ── Events ────────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            # ── Keyboard ─────────────────────────────────────────────
            if event.type == pygame.KEYDOWN:
                # Text tool active: capture typing
                if self.typing_mode:
                    self._handle_text_key(event)
                    return

                # Ctrl+S → save
                key_mods = pygame.key.get_mods()
                if event.key == pygame.K_s and (key_mods & pygame.KMOD_CTRL):
                    self._save_canvas()
                    return

                # Tool shortcuts
                hotkey_map = {
                    pygame.K_p: MODE_PENCIL,
                    pygame.K_l: MODE_LINE,
                    pygame.K_r: MODE_RECT,
                    pygame.K_q: MODE_SQUARE,
                    pygame.K_c: MODE_CIRCLE,
                    pygame.K_t: MODE_RTRI,
                    pygame.K_g: MODE_ETRI,
                    pygame.K_d: MODE_RHOMBUS,
                    pygame.K_e: MODE_ERASER,
                    pygame.K_f: MODE_FILL,
                    pygame.K_x: MODE_TEXT,
                }
                if event.key in hotkey_map:
                    self.active_mode = hotkey_map[event.key]

                # Brush size shortcuts
                if event.key == pygame.K_1:
                    self._set_size(1)
                if event.key == pygame.K_2:
                    self._set_size(2)
                if event.key == pygame.K_3:
                    self._set_size(3)

                if event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    self.draw_layer.fill(COL_WHITE)

            # ── Mouse DOWN ────────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos

                # Panel UI clicks
                for tb in self.tool_buttons:
                    if tb.is_clicked(event.pos):
                        # Commit any active text before switching
                        if self.typing_mode:
                            self._commit_text()
                        self.active_mode = tb.mode_id
                        return

                for bb in self.brush_buttons:
                    if bb.is_clicked(event.pos):
                        self._set_size(bb.size_id)
                        return

                if self.clear_rect.collidepoint(event.pos):
                    self.draw_layer.fill(COL_WHITE)
                    return

                for rect, swatch_color in self.swatch_rects:
                    if rect.collidepoint(event.pos):
                        self.active_color = swatch_color
                        if self.active_mode == MODE_ERASER:
                            self.active_mode = MODE_PENCIL
                        return

                # Canvas click
                if my < CANVAS_HEIGHT:
                    if self.active_mode == MODE_TEXT:
                        # Start/move text cursor
                        if self.typing_mode:
                            self._commit_text()
                        self._start_text(mx, my)
                        return

                    if self.active_mode == MODE_FILL:
                        self.engine.bucket_fill(self.draw_layer, mx, my, self.active_color)
                        return

                    if self.active_mode in DRAG_MODES:
                        self.is_dragging    = True
                        self.drag_origin    = (mx, my)
                        self.pre_drag_layer = self.draw_layer.copy()

                    elif self.active_mode == MODE_PENCIL:
                        self.last_point = (mx, my)
                        pygame.draw.circle(self.draw_layer, self.active_color,
                                           (mx, my), self.stroke_width)

                    elif self.active_mode == MODE_ERASER:
                        self.last_point = (mx, my)
                        pygame.draw.circle(self.draw_layer, COL_WHITE,
                                           (mx, my), self.eraser_radius)

            # ── Mouse UP ──────────────────────────────────────────────
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mx, my = event.pos
                if self.is_dragging and self.drag_origin:
                    self.engine.render_shape(
                        self.draw_layer, self.active_mode,
                        self.drag_origin, (mx, my),
                        self.active_color, self.stroke_width
                    )
                self.is_dragging = False
                self.drag_origin = None
                self.last_point  = None

            # ── Mouse MOTION ──────────────────────────────────────────
            if event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if my >= CANVAS_HEIGHT:
                    continue
                if not pygame.mouse.get_pressed()[0]:
                    continue

                if self.active_mode == MODE_PENCIL and self.last_point:
                    pygame.draw.line(self.draw_layer, self.active_color,
                                     self.last_point, (mx, my),
                                     max(1, self.stroke_width * 2))
                    pygame.draw.circle(self.draw_layer, self.active_color,
                                       (mx, my), self.stroke_width)
                    self.last_point = (mx, my)

                elif self.active_mode == MODE_ERASER and self.last_point:
                    pygame.draw.line(self.draw_layer, COL_WHITE,
                                     self.last_point, (mx, my),
                                     self.eraser_radius * 2)
                    pygame.draw.circle(self.draw_layer, COL_WHITE,
                                       (mx, my), self.eraser_radius)
                    self.last_point = (mx, my)

    # ── Draw ──────────────────────────────────────────────────────────────
    def _draw(self):
        # ── Canvas area ──────────────────────────────────────────────
        if self.is_dragging and self.pre_drag_layer:
            self.window.blit(self.pre_drag_layer, (0, 0))
            mx, my = pygame.mouse.get_pos()
            self.engine.render_shape(
                self.window, self.active_mode,
                self.drag_origin, (mx, my),
                self.active_color, self.stroke_width
            )
        else:
            self.window.blit(self.draw_layer, (0, 0))

        # Text preview (live typing)
        if self.typing_mode and self.pre_text_layer:
            # Show snapshot + current typed text
            self.window.blit(self.pre_text_layer, (0, 0))
            rendered = self.label_font.render(
                self.typed_text + "|", True, self.active_color)
            self.window.blit(rendered, self.caret_pos)

        # ── Panel ────────────────────────────────────────────────────
        pygame.draw.rect(self.window, COL_PANEL_BG,
                         (0, CANVAS_HEIGHT, WIN_WIDTH, PANEL_HEIGHT))
        pygame.draw.line(self.window, (65, 65, 65),
                         (0, CANVAS_HEIGHT), (WIN_WIDTH, CANVAS_HEIGHT), 2)

        for tb in self.tool_buttons:
            tb.draw(self.window, self.active_mode)

        for bb in self.brush_buttons:
            bb.draw(self.window, self.size_index)

        # Clear button
        pygame.draw.rect(self.window, (140, 35, 35), self.clear_rect, border_radius=5)
        pygame.draw.rect(self.window, (210, 70, 70), self.clear_rect, 1, border_radius=5)
        clear_label = self.label_font_small.render("Clear", True, COL_WHITE)
        self.window.blit(clear_label, clear_label.get_rect(center=self.clear_rect.center))

        # Current brush size display
        size_label = self.label_font_small.render(
            f"Brush: {self.stroke_width}px", True, (160, 200, 255))
        self.window.blit(size_label, (self.clear_rect.right + 8,
                                      self.clear_rect.centery - size_label.get_height() // 2))

        # Swatches
        for rect, swatch_color in self.swatch_rects:
            pygame.draw.rect(self.window, swatch_color, rect, border_radius=3)
            if swatch_color == self.active_color and self.active_mode != MODE_ERASER:
                pygame.draw.rect(self.window, COL_ACTIVE, rect, 3, border_radius=3)
            else:
                pygame.draw.rect(self.window, (20, 20, 20), rect, 1, border_radius=3)

        # Active colour preview
        preview_rect = pygame.Rect(WIN_WIDTH - 58, CANVAS_HEIGHT + 10, 46, 46)
        pygame.draw.rect(self.window,
                         self.active_color if self.active_mode != MODE_ERASER else COL_WHITE,
                         preview_rect, border_radius=6)
        pygame.draw.rect(self.window, (180, 180, 180), preview_rect, 2, border_radius=6)

        # Eraser cursor ring
        if self.active_mode == MODE_ERASER:
            mx, my = pygame.mouse.get_pos()
            if my < CANVAS_HEIGHT:
                pygame.draw.circle(self.window, (160, 160, 160),
                                   (mx, my), self.eraser_radius, 2)

        # Hint bar
        hint_label = self.label_font_small.render(
            "P=Pencil  L=Line  R=Rect  Q=Square  C=Circle  T=R.Tri  G=Eq.Tri  "
            "D=Rhombus  E=Eraser  F=Fill  X=Text  1/2/3=Size  Del=Clear  Ctrl+S=Save",
            True, (110, 110, 110))
        self.window.blit(hint_label, (6, WIN_HEIGHT - 14))

        # Save flash notification
        if hasattr(self, '_save_timer') and self._save_timer > 0:
            self._save_timer -= 1
            alpha     = min(255, self._save_timer * 5)
            flash_fnt = pygame.font.SysFont("consolas", 16, bold=True)
            flash_msg = flash_fnt.render(self._save_msg, True, (80, 255, 120))
            flash_msg.set_alpha(alpha)
            self.window.blit(flash_msg, (WIN_WIDTH // 2 - flash_msg.get_width() // 2,
                                         CANVAS_HEIGHT // 2 - 14))

        # Text mode indicator
        if self.typing_mode:
            mode_indicator = self.label_font_small.render(
                "TEXT MODE — type, Enter=confirm, Esc=cancel", True, (255, 200, 50))
            self.window.blit(mode_indicator,
                             (WIN_WIDTH // 2 - mode_indicator.get_width() // 2,
                              CANVAS_HEIGHT - 22))

        pygame.display.flip()

    # ── Main Loop ─────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.tick_clock.tick(FRAMES_PER_SEC)
            self._handle_events()
            self._draw()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    PaintStudio().run()