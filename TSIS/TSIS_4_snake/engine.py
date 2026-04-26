"""
engine.py — Core Snake game logic for TSIS 4.
Extends Practice 10 & 11 with:
  - Poison food (shortens snake by 2)
  - Three power-ups: Speed Boost, Slow Motion, Shield
  - Obstacle blocks from Level 3
  - Personal best display
  - DB save on game over
"""

import json
import math
import os
import random
import pygame
from gameconf import *
from datastore import fetch_personal_best, record_session


# ─────────────────────────────────────────────
#  PREFERENCES helpers
# ─────────────────────────────────────────────
def load_user_prefs():
    if os.path.exists(PREFS_PATH):
        try:
            with open(PREFS_PATH) as fp:
                payload = json.load(fp)
            for pref_key, pref_val in DEFAULT_PREFS.items():
                payload.setdefault(pref_key, pref_val)
            return payload
        except Exception:
            pass
    return dict(DEFAULT_PREFS)


def save_user_prefs(prefs: dict):
    with open(PREFS_PATH, "w") as fp:
        json.dump(prefs, fp, indent=2)


# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def render_grid_cell(surface, color, col, row, shrink=2, radius=4):
    rect = pygame.Rect(
        col * TILE_SIZE + shrink,
        row * TILE_SIZE + shrink,
        TILE_SIZE - shrink * 2,
        TILE_SIZE - shrink * 2,
    )
    pygame.draw.rect(surface, color, rect, border_radius=radius)


# ─────────────────────────────────────────────
#  OBSTACLE BLOCK
# ─────────────────────────────────────────────
class WallBrick:
    def __init__(self, col, row):
        self.col = col
        self.row = row

    def draw(self, surface):
        rect = pygame.Rect(self.col * TILE_SIZE, self.row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, COL_OBSTACLE, rect)
        pygame.draw.rect(surface, (140, 110, 80), rect, 2)
        # Cross pattern to look like a wall brick
        pygame.draw.line(surface, (80, 60, 40),
                         (rect.left, rect.centery), (rect.right, rect.centery), 1)
        pygame.draw.line(surface, (80, 60, 40),
                         (rect.centerx, rect.top), (rect.centerx, rect.bottom), 1)


# ─────────────────────────────────────────────
#  POISON FOOD
# ─────────────────────────────────────────────
class ToxicPellet:
    """
    Dark-red item. Eating it shortens the snake by 2 segments.
    If snake length drops to ≤ 1 → game over.
    Disappears after FOOD_SPAWN_PERIOD * 2 seconds.
    """
    LIFESPAN = FOOD_SPAWN_PERIOD * 2

    def __init__(self, col, row):
        self.col   = col
        self.row   = row
        self.age   = 0.0
        self.alive = True

    def update(self, dt):
        self.age += dt
        if self.age >= self.LIFESPAN:
            self.alive = False

    def draw(self, surface):
        cx = self.col * TILE_SIZE + TILE_SIZE // 2
        cy = self.row * TILE_SIZE + TILE_SIZE // 2
        radius = TILE_SIZE // 2 - 1
        # Dark red circle with skull-like cross
        pygame.draw.circle(surface, COL_POISON,    (cx, cy), radius)
        pygame.draw.circle(surface, (200, 0, 30),  (cx, cy), radius, 2)
        glyph_font = pygame.font.SysFont("consolas", 12, bold=True)
        glyph_surf = glyph_font.render("☠", True, (255, 80, 80))
        surface.blit(glyph_surf, glyph_surf.get_rect(center=(cx, cy)))


# ─────────────────────────────────────────────
#  POWER-UP
# ─────────────────────────────────────────────
class BoardPowerUp:
    """
    One of: "speed", "slow", "shield".
    Disappears from the field after POWERUP_FIELD_TTL seconds.
    """
    def __init__(self, kind, col, row):
        self.kind   = kind
        self.col    = col
        self.row    = row
        self.age    = 0.0
        self.alive  = True
        self.colour = POWERUP_COLOR_MAP[kind]

    def update(self, dt):
        self.age += dt
        if self.age >= POWERUP_FIELD_TTL:
            self.alive = False

    @property
    def fraction_remaining(self):
        return max(0.0, 1.0 - self.age / POWERUP_FIELD_TTL)

    def draw(self, surface):
        cx = self.col * TILE_SIZE + TILE_SIZE // 2
        cy = self.row * TILE_SIZE + TILE_SIZE // 2
        radius = TILE_SIZE // 2 - 1

        # Pulsing glow
        now_t   = pygame.time.get_ticks() / 1000.0
        scale   = 1.0 + 0.15 * math.sin(now_t * 5)
        pulse_r = max(1, int(radius * scale))
        glow    = pygame.Surface((pulse_r * 2 + 4, pulse_r * 2 + 4), pygame.SRCALPHA)
        glow_color = (*self.colour, 60)
        pygame.draw.circle(glow, glow_color, (pulse_r + 2, pulse_r + 2), pulse_r + 2)
        surface.blit(glow, (cx - pulse_r - 2, cy - pulse_r - 2))

        pygame.draw.circle(surface, self.colour, (cx, cy), radius)
        pygame.draw.circle(surface, COL_WHITE,   (cx, cy), radius, 2)

        glyph_map  = {"shield": "S", "slow": "▼", "speed": "▲"}
        glyph_font = pygame.font.SysFont("consolas", 12, bold=True)
        glyph_surf = glyph_font.render(glyph_map[self.kind], True, COL_WHITE)
        surface.blit(glyph_surf, glyph_surf.get_rect(center=(cx, cy)))

        # Timeout arc
        frac     = self.fraction_remaining
        ring_r   = radius + 4
        arc_rect = pygame.Rect(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
        if frac > 0.01:
            pygame.draw.arc(surface, self.colour, arc_rect,
                            -math.pi / 2,
                            -math.pi / 2 + 2 * math.pi * frac, 2)


# ─────────────────────────────────────────────
#  FOOD ITEM  (weighted + disappearing, from P11)
# ─────────────────────────────────────────────
class FoodPellet:
    def __init__(self, col, row):
        weights   = [tier_row[5] for tier_row in FOOD_TIER_TABLE]
        tier_pick = random.choices(FOOD_TIER_TABLE, weights=weights, k=1)[0]
        tier_name, tier_color, tier_score, tier_grow, tier_lifespan, _ = tier_pick
        self.col      = col
        self.row      = row
        self.tier     = tier_name
        self.colour   = tier_color
        self.score    = tier_score
        self.grow     = tier_grow
        self.lifespan = tier_lifespan
        self.age      = 0.0
        self.alive    = True

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifespan:
            self.alive = False

    @property
    def fraction_remaining(self):
        return max(0.0, 1.0 - self.age / self.lifespan)

    def draw(self, surface):
        cx = self.col * TILE_SIZE + TILE_SIZE // 2
        cy = self.row * TILE_SIZE + TILE_SIZE // 2
        radius = TILE_SIZE // 2 - 1
        pygame.draw.circle(surface, self.colour, (cx, cy), radius)
        shine_tone = tuple(min(255, c + 80) for c in self.colour)
        pygame.draw.circle(surface, shine_tone, (cx - radius // 3, cy - radius // 3), radius // 3)

        # Countdown arc
        frac   = self.fraction_remaining
        ring_r = radius + 4
        if frac > 0.5:
            phase    = (1.0 - frac) * 2
            ring_col = (int(255 * phase), 220, 0)
        else:
            phase    = (0.5 - frac) * 2
            ring_col = (255, int(220 * (1 - phase)), 0)
        arc_rect = pygame.Rect(cx - ring_r, cy - ring_r, ring_r * 2, ring_r * 2)
        if frac > 0.01:
            pygame.draw.arc(surface, ring_col, arc_rect,
                            -math.pi / 2,
                            -math.pi / 2 + 2 * math.pi * frac, 2)
        glyph_font = pygame.font.SysFont("consolas", 11, bold=True)
        glyph_surf = glyph_font.render(self.tier[0].upper(), True, COL_BLACK)
        surface.blit(glyph_surf, glyph_surf.get_rect(center=(cx, cy)))


# ─────────────────────────────────────────────
#  SNAKE GAME
# ─────────────────────────────────────────────
class SnakeRound:
    def __init__(self, window, tick_clock, player_handle, prefs):
        self.window        = window
        self.tick_clock    = tick_clock
        self.player_handle = player_handle
        self.prefs         = prefs

        # Fonts
        self.hud_font   = pygame.font.SysFont("consolas", 20, bold=True)
        self.title_font = pygame.font.SysFont("consolas", 42, bold=True)
        self.body_font  = pygame.font.SysFont("consolas", 24, bold=True)
        self.tiny_font  = pygame.font.SysFont("consolas", 15)

        self.best_score = fetch_personal_best(player_handle)
        self._init_round()

    def _init_round(self):
        mid_col = GRID_COLS // 2
        mid_row = GRID_ROWS // 2

        self.body         = [(mid_col - i, mid_row) for i in range(3)]
        self.heading      = DIR_RIGHT
        self.next_heading = DIR_RIGHT

        self.points         = 0
        self.tier           = 1
        self.foods_in_tier  = 0

        self.steps_per_sec    = TPS_BY_LEVEL[self.tier]
        self._step_accumulator = 0.0

        # Food / poison
        self.food_pool         = []
        self.toxin             = None
        self.food_spawn_acc    = 0.0
        self.toxin_spawn_acc   = 0.0

        # Power-up on field and active effect
        self.live_powerup      = None    # BoardPowerUp or None
        self.powerup_spawn_acc = 0.0
        self.active_buff       = None    # "speed" | "slow" | "shield" | None
        self.buff_expires_ms   = 0       # ms (get_ticks)
        self.shield_armed      = False   # shield absorbed one hit

        # Obstacles
        self.wall_set    = set()   # set of (col, row)
        self.wall_bricks = []      # list of WallBrick

        self.is_over          = False
        self.is_paused        = False
        self.score_recorded   = False

        # Spawn initial food
        self._spawn_food()

    # ── Occupied cells ────────────────────────────────────────────────────
    def _occupied(self):
        occ = set(self.body) | self.wall_set
        for food in self.food_pool:
            occ.add((food.col, food.row))
        if self.toxin:
            occ.add((self.toxin.col, self.toxin.row))
        if self.live_powerup:
            occ.add((self.live_powerup.col, self.live_powerup.row))
        return occ

    def _random_free_cell(self):
        occ = self._occupied()
        # Exclude border
        for _ in range(500):
            col = random.randint(1, GRID_COLS - 2)
            row = random.randint(1, GRID_ROWS - 2)
            if (col, row) not in occ:
                return col, row
        return None

    # ── Spawning ──────────────────────────────────────────────────────────
    def _spawn_food(self):
        if len(self.food_pool) >= MAX_FOOD_ON_BOARD:
            return
        cell = self._random_free_cell()
        if cell:
            self.food_pool.append(FoodPellet(*cell))

    def _spawn_toxin(self):
        if self.toxin and self.toxin.alive:
            return
        cell = self._random_free_cell()
        if cell:
            self.toxin = ToxicPellet(*cell)

    def _spawn_powerup(self):
        if self.live_powerup and self.live_powerup.alive:
            return
        cell = self._random_free_cell()
        if cell:
            kind = random.choice(["speed", "slow", "shield"])
            self.live_powerup = BoardPowerUp(kind, *cell)

    def _place_walls(self):
        """
        Place OBSTACLES_PER_TIER * (tier - OBSTACLE_START_LEVEL + 1) blocks,
        guaranteed not to be on the snake's head area (3x3 safe zone).
        """
        count     = OBSTACLES_PER_TIER * (self.tier - OBSTACLE_START_LEVEL + 1)
        head_c, head_r = self.body[0]
        safe_zone = {(head_c + dc, head_r + dr)
                     for dc in range(-3, 4) for dr in range(-3, 4)}

        for _ in range(count):
            for _attempt in range(300):
                col = random.randint(1, GRID_COLS - 2)
                row = random.randint(1, GRID_ROWS - 2)
                pos = (col, row)
                if (pos not in self.wall_set
                        and pos not in set(self.body)
                        and pos not in safe_zone):
                    self.wall_set.add(pos)
                    self.wall_bricks.append(WallBrick(col, row))
                    break

    # ── Main run loop ─────────────────────────────────────────────────────
    def run(self):
        """Returns "retry" or "menu"."""
        from screens import GameOverScreen
        while True:
            dt = self.tick_clock.tick(RENDER_FPS) / 1000.0
            self._handle_events()
            if not self.is_over and not self.is_paused:
                self._update(dt)
            self._draw()

            if self.is_over:
                if not self.score_recorded:
                    record_session(self.player_handle, self.points, self.tier)
                    self.score_recorded = True
                    if self.points > self.best_score:
                        self.best_score = self.points
                return GameOverScreen().run(
                    self.window, self.tick_clock,
                    self.points, self.tier, self.best_score, self.player_handle
                )

    # ── Events ────────────────────────────────────────────────────────────
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                import sys; pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.is_paused = not self.is_paused
                if event.key == pygame.K_RIGHT and self.heading != DIR_LEFT:
                    self.next_heading = DIR_RIGHT
                if event.key == pygame.K_LEFT  and self.heading != DIR_RIGHT:
                    self.next_heading = DIR_LEFT
                if event.key == pygame.K_DOWN  and self.heading != DIR_UP:
                    self.next_heading = DIR_DOWN
                if event.key == pygame.K_UP    and self.heading != DIR_DOWN:
                    self.next_heading = DIR_UP

    # ── Update ────────────────────────────────────────────────────────────
    def _update(self, dt):
        now_ms = pygame.time.get_ticks()

        # ── Power-up effect expiry ────────────────────────────────────
        if self.active_buff in ("speed", "slow"):
            if now_ms >= self.buff_expires_ms:
                self.active_buff = None

        # ── Current speed (modified by power-up) ─────────────────────
        base_tps = TPS_BY_LEVEL[self.tier]
        if self.active_buff == "speed":
            cur_tps = base_tps + SPEED_BOOST_TPS
        elif self.active_buff == "slow":
            cur_tps = max(2, base_tps - SLOW_MOTION_TPS)
        else:
            cur_tps = base_tps
        self.steps_per_sec = cur_tps

        # ── Food / poison / power-up timers ──────────────────────────
        for food in self.food_pool:
            food.update(dt)
        self.food_pool = [f for f in self.food_pool if f.alive]

        if self.toxin:
            self.toxin.update(dt)
            if not self.toxin.alive:
                self.toxin = None

        if self.live_powerup:
            self.live_powerup.update(dt)
            if not self.live_powerup.alive:
                self.live_powerup = None

        # ── Spawn timers ──────────────────────────────────────────────
        self.powerup_spawn_acc += dt
        if self.powerup_spawn_acc >= FOOD_SPAWN_PERIOD * 2:
            self.powerup_spawn_acc = 0.0
            self._spawn_powerup()

        self.toxin_spawn_acc += dt
        if self.toxin_spawn_acc >= FOOD_SPAWN_PERIOD * 1.5:
            self.toxin_spawn_acc = 0.0
            self._spawn_toxin()

        self.food_spawn_acc += dt
        if self.food_spawn_acc >= FOOD_SPAWN_PERIOD:
            self.food_spawn_acc = 0.0
            self._spawn_food()

        # ── Snake movement ────────────────────────────────────────────
        self._step_accumulator += dt
        step_time = 1.0 / self.steps_per_sec
        while self._step_accumulator >= step_time:
            self._step_accumulator -= step_time
            self._step()

    def _step(self):
        self.heading = self.next_heading
        head_c, head_r = self.body[0]
        d_col, d_row   = self.heading
        new_head = (head_c + d_col, head_r + d_row)
        nc, nr   = new_head

        # ── Wall collision ────────────────────────────────────────────
        hit_border = (nc <= 0 or nc >= GRID_COLS - 1 or nr <= 0 or nr >= GRID_ROWS - 1)
        if hit_border:
            if self.shield_armed:
                self.shield_armed = False
                self.active_buff  = None
                return   # skip this step (absorb hit)
            self.is_over = True
            return

        # ── Obstacle collision ────────────────────────────────────────
        if new_head in self.wall_set:
            if self.shield_armed:
                self.shield_armed = False
                self.active_buff  = None
                return
            self.is_over = True
            return

        # ── Self collision ────────────────────────────────────────────
        if new_head in self.body:
            if self.shield_armed:
                self.shield_armed = False
                self.active_buff  = None
                return
            self.is_over = True
            return

        # Move
        self.body.insert(0, new_head)

        # ── Poison collision ──────────────────────────────────────────
        if self.toxin and (self.toxin.col, self.toxin.row) == new_head:
            self.toxin = None
            # Shorten by 2 (already added head, remove 2 from tail)
            for _ in range(min(2, len(self.body) - 1)):
                self.body.pop()
            if len(self.body) <= 1:
                self.is_over = True
                return
            self.body.pop()   # normal tail removal
            return

        # ── Power-up collection ───────────────────────────────────────
        if (self.live_powerup
                and (self.live_powerup.col, self.live_powerup.row) == new_head):
            kind = self.live_powerup.kind
            self.live_powerup = None
            now_ms = pygame.time.get_ticks()
            if kind == "shield":
                self.active_buff  = "shield"
                self.shield_armed = True
            else:
                self.active_buff     = kind
                self.buff_expires_ms = now_ms + int(POWERUP_EFFECT_SECONDS * 1000)
            self.body.pop()   # normal move (no growth)
            return

        # ── Food collision ────────────────────────────────────────────
        eaten = None
        for food in self.food_pool:
            if (food.col, food.row) == new_head:
                eaten = food
                break

        if eaten:
            self.points        += eaten.score
            self.foods_in_tier += 1
            self.food_pool.remove(eaten)
            # Grow extra segments
            for _ in range(eaten.grow - 1):
                self.body.append(self.body[-1])
            # Level up?
            if self.foods_in_tier >= FOODS_TO_NEXT_LEVEL and self.tier < TOP_LEVEL:
                self.tier          += 1
                self.foods_in_tier  = 0
                # Place obstacles starting from level 3
                if self.tier >= OBSTACLE_START_LEVEL:
                    self._place_walls()
            self._spawn_food()
        else:
            self.body.pop()

    # ── Draw ──────────────────────────────────────────────────────────────
    def _draw(self):
        self.window.fill(COL_BG)
        snake_color = tuple(self.prefs.get("snake_color", [0, 200, 0]))

        # Grid overlay
        if self.prefs.get("grid", True):
            for c in range(GRID_COLS):
                for r in range(GRID_ROWS):
                    pygame.draw.circle(self.window, COL_GRAY,
                                       (c * TILE_SIZE + TILE_SIZE // 2,
                                        r * TILE_SIZE + TILE_SIZE // 2), 1)

        # Wall border
        pygame.draw.rect(self.window, COL_WALL,
                         pygame.Rect(0, 0, BOARD_WIDTH, BOARD_HEIGHT), TILE_SIZE)

        # Obstacles
        for brick in self.wall_bricks:
            brick.draw(self.window)

        # Food items
        for food in self.food_pool:
            food.draw(self.window)

        # Poison
        if self.toxin and self.toxin.alive:
            self.toxin.draw(self.window)

        # Power-up on field
        if self.live_powerup and self.live_powerup.alive:
            self.live_powerup.draw(self.window)

        # Snake
        dark_tone = tuple(max(0, c - 60) for c in snake_color)
        for i, (col, row) in enumerate(self.body):
            tone = snake_color if i == 0 else dark_tone
            render_grid_cell(self.window, tone, col, row)
            if i == 0:
                self._draw_eyes(col, row)

        # Shield glow around head
        if self.shield_armed:
            now_t  = pygame.time.get_ticks() / 1000.0
            alpha  = int(140 + 80 * math.sin(now_t * 6))
            head_c, head_r = self.body[0]
            glow   = pygame.Surface((TILE_SIZE + 10, TILE_SIZE + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (0, 220, 120, alpha), glow.get_rect(), 3)
            self.window.blit(glow, (head_c * TILE_SIZE - 5, head_r * TILE_SIZE - 5))

        self._draw_hud()

        if self.is_paused:
            self._draw_overlay("PAUSED", "P — resume")

        pygame.display.flip()

    def _draw_eyes(self, col, row):
        cx = col * TILE_SIZE + TILE_SIZE // 2
        cy = row * TILE_SIZE + TILE_SIZE // 2
        dx, dy = self.heading
        perp   = (-dy, dx)
        for sign in (-1, 1):
            ex = cx + sign * perp[0] * 4 + dx * 4
            ey = cy + sign * perp[1] * 4 + dy * 4
            pygame.draw.circle(self.window, COL_WHITE, (ex, ey), 3)
            pygame.draw.circle(self.window, COL_BLACK, (ex + dx, ey + dy), 1)

    def _draw_hud(self):
        # Score / level / personal best
        self.window.blit(
            self.hud_font.render(f"Score: {self.points}", True, COL_WHITE),
            (TILE_SIZE + 4, 4))
        level_surf = self.hud_font.render(f"Level: {self.tier}", True, COL_GOLD)
        self.window.blit(level_surf, (BOARD_WIDTH // 2 - level_surf.get_width() // 2, 4))

        best_surf = self.tiny_font.render(f"Best: {self.best_score}", True, COL_LGRAY)
        self.window.blit(best_surf, (BOARD_WIDTH - best_surf.get_width() - TILE_SIZE - 4, 4))

        # Foods to next level
        if self.tier < TOP_LEVEL:
            remaining = FOODS_TO_NEXT_LEVEL - self.foods_in_tier
            progress_surf = self.tiny_font.render(
                f"Next lvl: {remaining} food{'s' if remaining != 1 else ''}",
                True, (180, 180, 180))
        else:
            progress_surf = self.tiny_font.render("MAX LEVEL", True, COL_GOLD)
        self.window.blit(progress_surf,
                         (BOARD_WIDTH - progress_surf.get_width() - TILE_SIZE - 4, 24))

        # Active power-up indicator
        if self.active_buff:
            now_ms = pygame.time.get_ticks()
            tone   = POWERUP_COLOR_MAP.get(self.active_buff, COL_WHITE)
            if self.active_buff == "shield":
                txt = "SHIELD ready"
            else:
                remaining = max(0, (self.buff_expires_ms - now_ms) / 1000)
                txt = f"{self.active_buff.upper()} {remaining:.1f}s"
            buff_surf = self.tiny_font.render(f"⚡ {txt}", True, tone)
            pygame.draw.rect(self.window, (0, 0, 0),
                             (BOARD_WIDTH // 2 - buff_surf.get_width() // 2 - 6,
                              BOARD_HEIGHT - 24,
                              buff_surf.get_width() + 12, 20))
            self.window.blit(buff_surf,
                             (BOARD_WIDTH // 2 - buff_surf.get_width() // 2,
                              BOARD_HEIGHT - 22))

        # Legend bottom-left
        lx, ly = TILE_SIZE + 4, BOARD_HEIGHT - TILE_SIZE - 4
        for tier_name, tier_color, tier_score, tier_grow, _life, _ in FOOD_TIER_TABLE:
            pygame.draw.circle(self.window, tier_color, (lx + 6, ly - 4), 6)
            legend_surf = self.tiny_font.render(
                f"{tier_name}: +{tier_score}pts  +{tier_grow}seg", True, (160, 160, 160))
            self.window.blit(legend_surf, (lx + 16, ly - 12))
            ly -= 18

    def _draw_overlay(self, title, sub):
        veil = pygame.Surface((BOARD_WIDTH, BOARD_HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 170))
        self.window.blit(veil, (0, 0))
        title_surf = self.title_font.render(title, True, COL_WHITE)
        self.window.blit(title_surf,
                         title_surf.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2 - 30)))
        sub_surf = self.body_font.render(sub, True, (200, 200, 200))
        self.window.blit(sub_surf,
                         sub_surf.get_rect(center=(BOARD_WIDTH // 2, BOARD_HEIGHT // 2 + 25)))
