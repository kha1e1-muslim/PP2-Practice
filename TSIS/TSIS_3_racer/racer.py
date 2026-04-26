"""
racer.py — Core game logic for TSIS 3 Racer.
Extends Practice 10 & 11 with:
  - Lane hazards: oil spills, speed bumps, nitro strips
  - Road obstacles: barriers, potholes
  - Three power-ups: Nitro, Shield, Repair
  - Dynamic difficulty scaling
  - Score = distance + coins + power-up bonuses
  - Safe spawn logic (never on top of player)
"""

import math
import random
import sys
import pygame
from persistence import load_preferences, record_score

# ── Colours ───────────────────────────────────────────────────────────────────
COL_WHITE      = (255, 255, 255)
COL_BLACK      = (0,   0,   0)
COL_ASPHALT    = (50,  52,  55)
COL_CURB       = (210, 200, 185)
COL_GRASS_DARK = (34,  90,  34)
COL_GRASS_LITE = (45,  120, 45)
COL_GOLD       = (255, 185, 0)
COL_SILVER     = (192, 192, 210)
COL_BRONZE     = (180, 100, 30)
COL_MERC_SHINE = (60,  70,  80)
COL_MERC_GLASS = (140, 200, 230)
COL_LED_WHITE  = (230, 240, 255)
COL_LED_RED    = (255, 60,  60)
COL_ORANGE     = (255, 140, 0)
COL_RED        = (220, 40,  40)
COL_TEAL       = (0,   200, 180)
COL_PURPLE     = (160, 0,   200)

SKYLINE_COLORS = [
    (90, 80, 55), (65, 80, 65), (80, 60, 60),
    (55, 75, 90), (75, 70, 85), (60, 65, 80),
]
ENEMY_BODY_COLORS = [
    (200, 200, 50), (0, 140, 200), (160, 0, 160),
    (255, 140, 0),  (30, 160, 30), (200, 30, 30),
]

# Screen / road geometry
WIN_W, WIN_H    = 600, 700
FRAMES_PER_SEC  = 60
ROAD_X_LEFT     = 80
ROAD_X_RIGHT    = 480
ROAD_WIDTH      = ROAD_X_RIGHT - ROAD_X_LEFT
LANE_WIDTH      = ROAD_WIDTH // 4
LANE_CENTERS    = [ROAD_X_LEFT + LANE_WIDTH * i + LANE_WIDTH // 2 for i in range(4)]

# Difficulty presets  {name: (enemy_interval, obstacle_interval, base_speed)}
DIFFICULTY_PRESETS = {
    "hard":   (60,  90,  7),
    "normal": (90,  130, 5),
    "easy":   (120, 180, 4),
}

# Weighted coin tiers (same as Practice 11)
COIN_TIER_TABLE = [
    ("gold",   COL_GOLD,   16, 5,  30, 10),
    ("silver", COL_SILVER, 13, 3,  15, 30),
    ("bronze", COL_BRONZE, 10, 1,  5,  60),
]

# Power-up registry
POWERUP_TABLE = {
    "repair": {"color": (0,   220, 80),  "label": "R", "duration": 0},    # instant
    "shield": {"color": (0,   180, 255), "label": "S", "duration": 0},    # until hit
    "nitro":  {"color": (255, 80,  0),   "label": "N", "duration": 4.0},
}
POWERUP_LIFETIME = 7.0   # seconds before power-up disappears

HAZARD_KINDS = ["nitro_strip", "bump", "oil"]


# ─────────────────────────────────────────────
#  ASPHALT TEXTURE
# ─────────────────────────────────────────────
def build_asphalt_tile(width, height):
    surf = pygame.Surface((width, height))
    surf.fill(COL_ASPHALT)
    rng = random.Random(42)
    for _ in range(width * height // 7):
        px = rng.randint(0, width - 1)
        py = rng.randint(0, height - 1)
        delta = rng.randint(-10, 10)
        tone = tuple(max(0, min(255, COL_ASPHALT[i] + delta)) for i in range(3))
        surf.set_at((px, py), tone)
    return surf


# ─────────────────────────────────────────────
#  SCENERY
# ─────────────────────────────────────────────
class LaneDash:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def update(self, speed):
        self.y += speed
        if self.y > WIN_H:
            self.y -= WIN_H + 50

    def draw(self, surface):
        pygame.draw.rect(surface, COL_WHITE, (self.x - 3, self.y, 6, 38), border_radius=2)


class Tree:
    def __init__(self, speed, y=None):
        self.x = random.randint(ROAD_X_RIGHT + 6, WIN_W - 16)
        self.r = random.randint(12, 22)
        self.y = y if y is not None else random.randint(-self.r, WIN_H)

    def update(self, speed):
        self.y += speed
        if self.y - self.r > WIN_H:
            self.__init__(speed)

    def draw(self, surface):
        pygame.draw.rect(surface, (90, 55, 20), (self.x - 3, self.y, 6, self.r))
        pygame.draw.circle(surface, COL_GRASS_DARK, (self.x, self.y), self.r)
        pygame.draw.circle(surface, COL_GRASS_LITE, (self.x - 4, self.y - 4), max(1, self.r - 4))


class Building:
    def __init__(self, speed, y=None):
        self.w     = random.randint(28, 55)
        self.h     = random.randint(60, 160)
        self.x     = random.randint(2, max(2, ROAD_X_LEFT - self.w - 4))
        self.y     = y if y is not None else random.randint(-200, WIN_H)
        self.color = random.choice(SKYLINE_COLORS)
        self.speed = speed
        self.wins  = [(random.randint(5, self.w - 11), random.randint(8, self.h - 16),
                       random.random() > 0.4)
                      for _ in range(random.randint(4, 10))]

    def update(self, speed):
        self.y += speed
        if self.y > WIN_H:
            self.__init__(speed)

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.w, self.h))
        edge_tone = tuple(min(255, v + 20) for v in self.color)
        pygame.draw.rect(surface, edge_tone, (self.x, self.y, self.w, self.h), 1)
        for wx, wy, lit in self.wins:
            win_color = (255, 240, 150) if lit else (30, 30, 40)
            pygame.draw.rect(surface, win_color, (self.x + wx, self.y + wy, 6, 8))


# ─────────────────────────────────────────────
#  PLAYER CAR
# ─────────────────────────────────────────────
class PlayerCar(pygame.sprite.Sprite):
    W, H = 48, 88

    def __init__(self, body_color):
        super().__init__()
        self.body_color = body_color
        self.image      = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self._draw()
        self.rect          = self.image.get_rect()
        self.rect.centerx  = LANE_CENTERS[1]
        self.rect.bottom   = WIN_H - 30
        self.base_speed    = 5
        self.speed         = 5

    def update(self, keys):
        if keys[pygame.K_LEFT]:  self.rect.x -= self.speed
        if keys[pygame.K_RIGHT]: self.rect.x += self.speed
        if keys[pygame.K_UP]:    self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:  self.rect.y += self.speed
        self.rect.left   = max(ROAD_X_LEFT + 4,  self.rect.left)
        self.rect.right  = min(ROAD_X_RIGHT - 4, self.rect.right)
        self.rect.top    = max(0,                self.rect.top)
        self.rect.bottom = min(WIN_H,            self.rect.bottom)

    def _draw(self):
        canvas, w, h = self.image, self.W, self.H
        body = self.body_color

        # Shadow
        shadow = pygame.Surface((w - 6, h - 10), pygame.SRCALPHA)
        shadow.fill((0, 0, 0, 55))
        canvas.blit(shadow, (3, 8))

        # Tyres
        for tx, ty, tw, th in [(0, 8, 10, 18), (w - 10, 8, 10, 18),
                               (0, h - 26, 10, 18), (w - 10, h - 26, 10, 18)]:
            pygame.draw.rect(canvas, (22, 22, 22), (tx, ty, tw, th), border_radius=3)
            pygame.draw.rect(canvas, (155, 155, 170), (tx + 2, ty + 4, tw - 4, th - 8), border_radius=2)

        # Body
        pygame.draw.rect(canvas, body, (8, 4, w - 16, h - 8), border_radius=10)

        # Specular
        highlight = pygame.Surface((8, h - 20), pygame.SRCALPHA)
        highlight.fill((255, 255, 255, 22))
        canvas.blit(highlight, (w // 2 - 4, 10))

        # Hood crease
        pygame.draw.line(canvas, COL_MERC_SHINE, (16, 6),     (16, 30),     1)
        pygame.draw.line(canvas, COL_MERC_SHINE, (w - 16, 6), (w - 16, 30), 1)

        # Windshield
        pygame.draw.rect(canvas, COL_MERC_GLASS, (11, 12, w - 22, 18), border_radius=4)
        pygame.draw.line(canvas, body, (14, 22), (w - 14, 22), 1)

        # Rear window
        pygame.draw.rect(canvas, COL_MERC_GLASS, (11, h - 30, w - 22, 14), border_radius=4)

        # Side windows
        pygame.draw.rect(canvas, COL_MERC_GLASS, (8,     34, 5, 22), border_radius=2)
        pygame.draw.rect(canvas, COL_MERC_GLASS, (w - 13, 34, 5, 22), border_radius=2)

        # LED strips
        for lx in (10, w - 18):
            pygame.draw.rect(canvas, COL_LED_WHITE, (lx, 5, 8, 4), border_radius=1)
        pygame.draw.rect(canvas, COL_LED_WHITE, (11, 4, w - 22, 2))
        for lx in (10, w - 18):
            pygame.draw.rect(canvas, COL_LED_RED, (lx, h - 9, 8, 4), border_radius=1)
        pygame.draw.rect(canvas, (180, 20, 20), (11, h - 8, w - 22, 2))

        # Mercedes star
        cx2, cy2, radius = w // 2, 9, 5
        for i in range(3):
            angle = math.radians(i * 120 - 90)
            pygame.draw.line(canvas, COL_SILVER, (cx2, cy2),
                             (int(cx2 + radius * math.cos(angle)),
                              int(cy2 + radius * math.sin(angle))), 2)
        pygame.draw.circle(canvas, COL_SILVER, (cx2, cy2), radius, 1)
        pygame.draw.rect(canvas, COL_SILVER, (w // 2 - 6, h - 11, 12, 3), border_radius=1)


# ─────────────────────────────────────────────
#  ENEMY CAR  (traffic)
# ─────────────────────────────────────────────
class EnemyCar(pygame.sprite.Sprite):
    W, H = 48, 88

    def __init__(self, speed, player_rect=None):
        super().__init__()
        self.image = pygame.Surface((self.W, self.H), pygame.SRCALPHA)
        self.color = random.choice(ENEMY_BODY_COLORS)
        self.shape = random.choice(["sedan", "suv"])
        self._draw()
        # Safe spawn: never directly above player
        self.rect = self.image.get_rect()
        lane_idx = self._safe_lane(player_rect)
        self.rect.centerx = LANE_CENTERS[lane_idx]
        self.rect.bottom  = -10
        self.speed = speed

    def update(self, *args):
        self.rect.y += self.speed
        if self.rect.top > WIN_H:
            self.kill()

    def _safe_lane(self, player_rect):
        candidates = list(range(4))
        if player_rect:
            for i, lx in enumerate(LANE_CENTERS):
                if abs(lx - player_rect.centerx) < LANE_WIDTH:
                    candidates = [l for l in candidates if l != i]
        return random.choice(candidates) if candidates else random.randint(0, 3)

    def _draw(self):
        canvas, w, h, body = self.image, self.W, self.H, self.color
        for tx, ty, tw, th in [(0, 8, 10, 18), (w - 10, 8, 10, 18),
                               (0, h - 26, 10, 18), (w - 10, h - 26, 10, 18)]:
            pygame.draw.rect(canvas, (22, 22, 22), (tx, ty, tw, th), border_radius=3)
            pygame.draw.rect(canvas, (140, 140, 155), (tx + 2, ty + 4, tw - 4, th - 8), border_radius=2)
        if self.shape == "sedan":
            pygame.draw.rect(canvas, body, (8, 4, w - 16, h - 8), border_radius=9)
            pygame.draw.rect(canvas, (160, 210, 240), (11, 12, w - 22, 16), border_radius=4)
            pygame.draw.rect(canvas, (160, 210, 240), (11, h - 28, w - 22, 12), border_radius=4)
        else:
            pygame.draw.rect(canvas, body, (7, 3, w - 14, h - 6), border_radius=5)
            shade = tuple(max(0, x - 45) for x in body)
            pygame.draw.rect(canvas, shade, (12, 5, w - 24, 3))
            pygame.draw.rect(canvas, shade, (12, 10, w - 24, 3))
            pygame.draw.rect(canvas, (160, 210, 240), (10, 15, w - 20, 20), border_radius=3)
            pygame.draw.rect(canvas, (160, 210, 240), (10, h - 32, w - 20, 16), border_radius=3)
        for lx in (10, w - 18):
            pygame.draw.rect(canvas, COL_LED_RED, (lx, 5, 8, 4), border_radius=1)
        pygame.draw.rect(canvas, (200, 20, 20), (11, 4, w - 22, 2))
        for lx in (10, w - 18):
            pygame.draw.rect(canvas, COL_LED_WHITE, (lx, h - 9, 8, 4), border_radius=1)


# ─────────────────────────────────────────────
#  WEIGHTED COIN  (same as Practice 11)
# ─────────────────────────────────────────────
class Coin(pygame.sprite.Sprite):
    def __init__(self, road_speed):
        super().__init__()
        weights   = [tier_row[5] for tier_row in COIN_TIER_TABLE]
        tier_pick = random.choices(COIN_TIER_TABLE, weights=weights, k=1)[0]
        tier_name, tier_color, tier_radius, self.coin_value, self.score_value, _ = tier_pick
        self.tier      = tier_name
        self._radius   = tier_radius
        self._colour   = tier_color
        self._base     = self._make_surf(tier_radius, tier_color)
        self.image     = self._base.copy()
        self.rect      = self.image.get_rect()
        self.rect.centerx  = random.choice(LANE_CENTERS)
        self.rect.bottom   = -10
        self.road_speed    = road_speed
        self._phase        = random.uniform(0, 2 * math.pi)

    def update(self, *args):
        self.rect.y += self.road_speed
        if self.rect.top > WIN_H:
            self.kill()
            return
        now_t = pygame.time.get_ticks() / 1000.0
        scale = 1.0 + 0.12 * math.sin(now_t * 4 + self._phase)
        new_radius = max(1, int(self._radius * scale))
        self.image = self._make_surf(new_radius, self._colour)
        cx, cy = self.rect.center
        self.rect = self.image.get_rect(center=(cx, cy))

    @staticmethod
    def _make_surf(radius, colour):
        size = radius * 2 + 6
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        rim_tone   = tuple(max(0, c - 40) for c in colour)
        shine_tone = tuple(min(255, c + 60) for c in colour)
        pygame.draw.circle(surf, rim_tone,   (cx, cy), radius)
        pygame.draw.circle(surf, colour,     (cx, cy), radius - 2)
        pygame.draw.circle(surf, shine_tone, (cx - radius // 4, cy - radius // 4), radius // 3)
        return surf


# ─────────────────────────────────────────────
#  POWER-UP
# ─────────────────────────────────────────────
class PowerUp(pygame.sprite.Sprite):
    RADIUS = 18

    def __init__(self, kind, road_speed, player_rect=None):
        super().__init__()
        self.kind       = kind
        self.road_speed = road_speed
        self.spawned_at = pygame.time.get_ticks() / 1000.0

        radius   = self.RADIUS
        side     = radius * 2 + 4
        self.image = pygame.Surface((side, side), pygame.SRCALPHA)
        body_tone  = POWERUP_TABLE[kind]["color"]
        pygame.draw.circle(self.image, body_tone, (radius + 2, radius + 2), radius)
        pygame.draw.circle(self.image, COL_WHITE, (radius + 2, radius + 2), radius, 2)
        glyph_font = pygame.font.SysFont("arial", 20, bold=True)
        glyph_surf = glyph_font.render(POWERUP_TABLE[kind]["label"], True, COL_WHITE)
        self.image.blit(glyph_surf, glyph_surf.get_rect(center=(radius + 2, radius + 2)))

        self.rect = self.image.get_rect()
        self.rect.centerx = random.choice(LANE_CENTERS)
        self.rect.bottom  = -10

    def update(self, *args):
        self.rect.y += self.road_speed
        if self.rect.top > WIN_H:
            self.kill()
            return
        # Timeout
        age = pygame.time.get_ticks() / 1000.0 - self.spawned_at
        if age > POWERUP_LIFETIME:
            self.kill()


# ─────────────────────────────────────────────
#  LANE HAZARD  (oil spill / speed bump / nitro strip)
# ─────────────────────────────────────────────
class LaneHazard(pygame.sprite.Sprite):
    def __init__(self, road_speed, player_rect=None):
        super().__init__()
        self.htype      = random.choice(HAZARD_KINDS)
        self.road_speed = road_speed

        w, h = LANE_WIDTH - 10, 28
        self.image = pygame.Surface((w, h), pygame.SRCALPHA)

        if self.htype == "oil":
            pygame.draw.ellipse(self.image, (20, 20, 40, 200), (0, 0, w, h))
            pygame.draw.ellipse(self.image, (80, 60, 120, 150), (4, 4, w - 8, h - 8))
            tag = pygame.font.SysFont("arial", 13, bold=True).render("OIL", True, (150, 100, 255))
            self.image.blit(tag, tag.get_rect(center=(w // 2, h // 2)))
        elif self.htype == "bump":
            pygame.draw.rect(self.image, (180, 140, 60), (0, 6, w, 16), border_radius=4)
            pygame.draw.rect(self.image, (220, 180, 80), (0, 6, w, 8),  border_radius=4)
            tag = pygame.font.SysFont("arial", 11, bold=True).render("BUMP", True, COL_BLACK)
            self.image.blit(tag, tag.get_rect(center=(w // 2, h // 2)))
        else:  # nitro_strip
            pygame.draw.rect(self.image, (255, 80, 0, 180), (0, 0, w, h), border_radius=4)
            tag = pygame.font.SysFont("arial", 13, bold=True).render("NITRO", True, COL_WHITE)
            self.image.blit(tag, tag.get_rect(center=(w // 2, h // 2)))

        self.rect = self.image.get_rect()
        lane_idx = random.randint(0, 3)
        self.rect.centerx = LANE_CENTERS[lane_idx]
        self.rect.bottom  = -10

    def update(self, *args):
        self.rect.y += self.road_speed
        if self.rect.top > WIN_H:
            self.kill()


# ─────────────────────────────────────────────
#  ROAD OBSTACLE  (barrier / pothole)
# ─────────────────────────────────────────────
class RoadObstacle(pygame.sprite.Sprite):
    def __init__(self, road_speed, player_rect=None):
        super().__init__()
        self.otype      = random.choice(["barrier", "pothole"])
        self.road_speed = road_speed

        if self.otype == "barrier":
            w, h = 54, 22
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (220, 60, 60), (0, 4, w, h - 8), border_radius=4)
            for bx in range(0, w, 14):
                pygame.draw.rect(self.image, COL_WHITE, (bx, 4, 7, h - 8))
        else:  # pothole
            w = h = 36
            self.image = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(self.image, (25, 20, 20, 230), (2, 2, w - 4, h - 4))
            pygame.draw.ellipse(self.image, (60, 50, 50, 180), (6, 6, w - 12, h - 12))

        self.rect = self.image.get_rect()
        lane_idx = self._safe_lane(player_rect)
        self.rect.centerx = LANE_CENTERS[lane_idx]
        self.rect.bottom  = -10

    def update(self, *args):
        self.rect.y += self.road_speed
        if self.rect.top > WIN_H:
            self.kill()

    def _safe_lane(self, player_rect):
        candidates = list(range(4))
        if player_rect:
            for i, lx in enumerate(LANE_CENTERS):
                if abs(lx - player_rect.centerx) < LANE_WIDTH:
                    candidates = [l for l in candidates if l != i]
        return random.choice(candidates) if candidates else random.randint(0, 3)


# ─────────────────────────────────────────────
#  MAIN GAME CLASS
# ─────────────────────────────────────────────
class RacerGame:
    def __init__(self, window, tick_clock, driver_name, prefs):
        self.window      = window
        self.tick_clock  = tick_clock
        self.driver_name = driver_name
        self.prefs       = prefs

        chosen_diff = prefs.get("difficulty", "normal")
        self.enemy_interval_seed, self.obstacle_interval_seed, base_speed = DIFFICULTY_PRESETS[chosen_diff]
        self.base_speed = base_speed

        car_body_color = tuple(prefs.get("car_color", [28, 32, 38]))
        self.asphalt   = build_asphalt_tile(ROAD_WIDTH, WIN_H)

        self.body_font  = pygame.font.SysFont("arial", 22, bold=True)
        self.small_font = pygame.font.SysFont("arial", 17)
        self.tiny_font  = pygame.font.SysFont("arial", 14)

        self._init(car_body_color)

    def _init(self, car_body_color=None):
        if car_body_color is None:
            car_body_color = tuple(self.prefs.get("car_color", [28, 32, 38]))

        self.scene      = pygame.sprite.Group()
        self.enemies    = pygame.sprite.Group()
        self.coins_grp  = pygame.sprite.Group()
        self.powerups   = pygame.sprite.Group()
        self.hazards    = pygame.sprite.Group()
        self.obstacles  = pygame.sprite.Group()

        self.driver = PlayerCar(car_body_color)
        self.scene.add(self.driver)

        self.lane_dashes = [LaneDash(ROAD_X_LEFT + LANE_WIDTH * i, sy)
                            for i in range(1, 4) for sy in range(0, WIN_H, 68)]
        self.skyline     = [Building(self.base_speed) for _ in range(7)]
        self.foliage     = [Tree(self.base_speed)     for _ in range(9)]
        self.scroll_offset = 0

        # Timers
        self.enemy_timer    = 0
        self.coin_timer     = 0
        self.hazard_timer   = 0
        self.obstacle_timer = 0
        self.powerup_timer  = 0

        self.enemy_interval    = self.enemy_interval_seed
        self.obstacle_interval = self.obstacle_interval_seed
        self.hazard_interval   = 150
        self.coin_interval     = 110
        self.powerup_interval  = 300

        # State
        self.road_speed   = self.base_speed
        self.enemy_speed  = self.base_speed
        self.points       = 0
        self.coin_total   = 0
        self.distance_m   = 0
        self.tier_level   = 1
        self.is_over      = False
        self.is_paused    = False

        # Power-up state
        self.live_powerup       = None   # "nitro" | "shield" | "repair" | None
        self.powerup_expires_at = 0.0
        self.shield_on          = False
        self.nitro_on           = False

        # Toast messages
        self.toast_text   = ""
        self.toast_frames = 0

        # Coins since last enemy speed-up (Practice 11 mechanic kept)
        self.coins_at_speedup_mark = 0

    # ── Run (returns "retry" | "menu") ───────────────────────────────────
    def run(self):
        from ui import GameOverScreen
        while True:
            dt = self.tick_clock.tick(FRAMES_PER_SEC) / 1000.0
            self._handle_events()
            if not self.is_over and not self.is_paused:
                self._update(dt)
            self._draw()
            if self.is_over:
                record_score(self.driver_name, self.points, self.distance_m, self.coin_total)
                return GameOverScreen().run(
                    self.window, self.tick_clock,
                    self.points, self.distance_m, self.coin_total, self.driver_name
                )

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.is_paused = not self.is_paused

    # ── Update ───────────────────────────────────────────────────────────
    def _update(self, dt):
        keys = pygame.key.get_pressed()

        # Nitro speed boost
        if self.nitro_on:
            self.driver.speed = self.driver.base_speed + 4
        else:
            self.driver.speed = self.driver.base_speed

        self.driver.update(keys)
        self.scroll_offset = (self.scroll_offset + self.road_speed) % WIN_H

        for dash in self.lane_dashes: dash.update(self.road_speed)
        for bld  in self.skyline:     bld.update(self.road_speed)
        for tr   in self.foliage:     tr.update(self.road_speed)

        self.distance_m += 1

        # ── Spawning ─────────────────────────────────────────────────
        self.powerup_timer += 1
        if self.powerup_timer >= self.powerup_interval:
            # Only one power-up on screen at a time
            if len(self.powerups) == 0:
                pu_kind = random.choice(["nitro", "shield", "repair"])
                pu = PowerUp(pu_kind, self.road_speed, self.driver.rect)
                self.powerups.add(pu); self.scene.add(pu)
            self.powerup_timer = 0

        self.obstacle_timer += 1
        if self.obstacle_timer >= self.obstacle_interval:
            obs = RoadObstacle(self.road_speed, self.driver.rect)
            self.obstacles.add(obs); self.scene.add(obs)
            self.obstacle_timer = 0

        self.hazard_timer += 1
        if self.hazard_timer >= self.hazard_interval:
            haz = LaneHazard(self.road_speed, self.driver.rect)
            self.hazards.add(haz); self.scene.add(haz)
            self.hazard_timer = 0

        self.coin_timer += 1
        if self.coin_timer >= self.coin_interval:
            coin = Coin(self.road_speed)
            self.coins_grp.add(coin); self.scene.add(coin)
            self.coin_timer = 0

        self.enemy_timer += 1
        if self.enemy_timer >= self.enemy_interval:
            foe = EnemyCar(self.enemy_speed, self.driver.rect)
            self.enemies.add(foe); self.scene.add(foe)
            self.enemy_timer = 0

        # ── Update all sprites ────────────────────────────────────────
        self.enemies.update()
        self.coins_grp.update()
        self.hazards.update()
        self.obstacles.update()
        self.powerups.update()

        # ── Collisions ───────────────────────────────────────────────
        # Enemy collision
        if pygame.sprite.spritecollideany(self.driver, self.enemies):
            if self.shield_on:
                self.shield_on    = False
                self.live_powerup = None
                # Kill the enemy car
                pygame.sprite.spritecollide(self.driver, self.enemies, True)
                self.toast_text   = "🛡 Shield absorbed the hit!"
                self.toast_frames = 120
            else:
                self.is_over = True

        # Obstacle collision
        obs_hits = pygame.sprite.spritecollide(self.driver, self.obstacles, False)
        if obs_hits:
            if self.shield_on:
                self.shield_on    = False
                self.live_powerup = None
                for obs in obs_hits: obs.kill()
                self.toast_text   = "🛡 Shield blocked obstacle!"
                self.toast_frames = 120
            else:
                self.is_over = True

        # Hazard collision
        haz_hits = pygame.sprite.spritecollide(self.driver, self.hazards, True)
        for haz in haz_hits:
            if haz.htype == "oil":
                # Slow down briefly
                self.driver.speed = max(2, self.driver.base_speed - 2)
                self.toast_text   = "🛢 Oil spill! Slowing down..."
                self.toast_frames = 90
            elif haz.htype == "bump":
                self.points       = max(0, self.points - 10)
                self.toast_text   = "🚧 Speed bump! -10 score"
                self.toast_frames = 90
            elif haz.htype == "nitro_strip":
                self._activate_powerup("nitro")

        # Coin collision
        collected = pygame.sprite.spritecollide(self.driver, self.coins_grp, True)
        for coin in collected:
            self.coin_total += coin.coin_value
            self.points     += coin.score_value

        # Power-up collision
        pu_hits = pygame.sprite.spritecollide(self.driver, self.powerups, True)
        for pu in pu_hits:
            self._activate_powerup(pu.kind)

        # ── Power-up timer expiry ─────────────────────────────────────
        now_t = pygame.time.get_ticks() / 1000.0
        if self.nitro_on and now_t >= self.powerup_expires_at:
            self.nitro_on     = False
            self.live_powerup = None

        # ── Difficulty scaling ────────────────────────────────────────
        # Every 500 distance units → faster, more spawns
        if self.distance_m % 500 == 0 and self.distance_m > 0:
            self.road_speed        = min(self.road_speed + 1, 16)
            self.enemy_speed       = min(self.enemy_speed + 1, 18)
            self.enemy_interval    = max(35, self.enemy_interval - 5)
            self.obstacle_interval = max(60, self.obstacle_interval - 5)
            self.hazard_interval   = max(80, self.hazard_interval - 5)
            self.tier_level       += 1
            self.toast_text        = f"⬆ Level {self.tier_level}! Speed up!"
            self.toast_frames      = 120

        # Practice 11: enemy speed-up every 5 coin units
        if self.coin_total - self.coins_at_speedup_mark >= 5:
            self.coins_at_speedup_mark = self.coin_total
            self.enemy_speed = min(self.enemy_speed + 1, 18)
            for foe in self.enemies:
                foe.speed = self.enemy_speed

        # Passive score
        self.points += 1

        if self.toast_frames > 0:
            self.toast_frames -= 1

    def _activate_powerup(self, kind):
        now_t = pygame.time.get_ticks() / 1000.0
        self.live_powerup = kind
        if kind == "nitro":
            self.nitro_on            = True
            self.shield_on           = False
            self.powerup_expires_at  = now_t + POWERUP_TABLE["nitro"]["duration"]
            self.toast_text   = "⚡ NITRO! Speed boost!"
            self.toast_frames = 90
        elif kind == "shield":
            self.shield_on    = True
            self.nitro_on     = False
            self.points      += 20
            self.toast_text   = "🛡 Shield active!"
            self.toast_frames = 90
        elif kind == "repair":
            self.live_powerup = None
            self.points      += 30
            # Clear all obstacles from screen
            self.obstacles.empty()
            self.toast_text   = "🔧 Repair! Obstacles cleared! +30"
            self.toast_frames = 120

    # ── Draw ─────────────────────────────────────────────────────────────
    def _draw(self):
        # Left: city pavement
        self.window.fill((105, 98, 88))
        tile_h = 40
        for ty in range(-tile_h, WIN_H + tile_h, tile_h):
            offset_ty = (ty + self.scroll_offset) % (WIN_H + tile_h) - tile_h
            pygame.draw.line(self.window, COL_CURB, (0, offset_ty), (ROAD_X_LEFT, offset_ty), 1)
        for tx in range(0, ROAD_X_LEFT, 20):
            pygame.draw.line(self.window, COL_CURB, (tx, 0), (tx, WIN_H), 1)
        for bld in self.skyline: bld.draw(self.window)

        # Right: grass
        pygame.draw.rect(self.window, COL_GRASS_DARK, (ROAD_X_RIGHT, 0, WIN_W - ROAD_X_RIGHT, WIN_H))
        for tr in self.foliage: tr.draw(self.window)

        # Asphalt
        self.window.blit(self.asphalt, (ROAD_X_LEFT, self.scroll_offset - WIN_H))
        self.window.blit(self.asphalt, (ROAD_X_LEFT, self.scroll_offset))

        # Road edges
        pygame.draw.rect(self.window, (215, 185, 0), (ROAD_X_LEFT - 6, 0, 6, WIN_H))
        pygame.draw.rect(self.window, COL_WHITE,     (ROAD_X_RIGHT,    0, 5, WIN_H))

        for dash in self.lane_dashes: dash.draw(self.window)

        # Sprites (draw order: hazards, coins, obstacles, power-ups, enemies, player)
        self.hazards.draw(self.window)
        self.coins_grp.draw(self.window)
        self.obstacles.draw(self.window)
        self.powerups.draw(self.window)
        self.enemies.draw(self.window)

        # Shield glow around player
        if self.shield_on:
            now_t = pygame.time.get_ticks() / 1000.0
            alpha = int(140 + 80 * math.sin(now_t * 6))
            glow  = pygame.Surface((self.driver.W + 16, self.driver.H + 16), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (0, 180, 255, alpha), glow.get_rect(), 4)
            self.window.blit(glow, (self.driver.rect.x - 8, self.driver.rect.y - 8))

        self.window.blit(self.driver.image, self.driver.rect)

        self._draw_hud()

        if self.toast_frames > 0:
            alpha     = min(255, self.toast_frames * 5)
            toast_sf  = self.body_font.render(self.toast_text, True, (255, 230, 80))
            toast_sf.set_alpha(alpha)
            self.window.blit(toast_sf, toast_sf.get_rect(center=(WIN_W // 2, 90)))

        if self.is_paused:
            self._draw_overlay("PAUSED", "P — resume")

        pygame.display.flip()

    def _draw_hud(self):
        # Left pill
        pill = pygame.Surface((185, 85), pygame.SRCALPHA)
        pill.fill((0, 0, 0, 120))
        self.window.blit(pill, (4, 4))

        self.window.blit(self.body_font.render(f"Score:  {self.points}",      True, COL_WHITE),     (10, 8))
        self.window.blit(self.body_font.render(f"Level:  {self.tier_level}",  True, (170,215,255)), (10, 34))
        self.window.blit(self.small_font.render(f"Dist: {self.distance_m}m",  True, (160,220,160)), (10, 62))

        # Coin counter top-right
        coin_surf = self.body_font.render(str(self.coin_total), True, COL_GOLD)
        coin_rect = coin_surf.get_rect(topright=(WIN_W - 14, 12))
        self.window.blit(coin_surf, coin_rect)
        ix, iy = coin_rect.left - 18, coin_rect.centery
        pygame.draw.circle(self.window, COL_GOLD,      (ix, iy), 12)
        pygame.draw.circle(self.window, (195, 150, 0), (ix, iy), 12, 2)
        coin_glyph = self.small_font.render("$", True, (120, 80, 0))
        self.window.blit(coin_glyph, coin_glyph.get_rect(center=(ix, iy)))

        # Active power-up HUD
        if self.live_powerup:
            now_t  = pygame.time.get_ticks() / 1000.0
            tone   = POWERUP_TABLE[self.live_powerup]["color"]
            text   = self.live_powerup.upper()
            if self.nitro_on:
                remaining = max(0, self.powerup_expires_at - now_t)
                text = f"NITRO {remaining:.1f}s"
            elif self.shield_on:
                text = "SHIELD active"
            pu_surf = self.small_font.render(f"⚡ {text}", True, tone)
            pygame.draw.rect(self.window, (0, 0, 0, 140),
                             (WIN_W // 2 - pu_surf.get_width() // 2 - 8, 8,
                              pu_surf.get_width() + 16, 28))
            self.window.blit(pu_surf, pu_surf.get_rect(center=(WIN_W // 2, 22)))

        # Hint
        hint = self.tiny_font.render("P=Pause  Arrow keys=Drive", True, (100, 100, 100))
        self.window.blit(hint, (ROAD_X_LEFT + 4, WIN_H - 18))

    def _draw_overlay(self, title, sub):
        veil = pygame.Surface((WIN_W, WIN_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        self.window.blit(veil, (0, 0))
        title_font = pygame.font.SysFont("arial", 44, bold=True)
        sub_font   = pygame.font.SysFont("arial", 22)
        title_surf = title_font.render(title, True, COL_WHITE)
        self.window.blit(title_surf, title_surf.get_rect(center=(WIN_W // 2, WIN_H // 2 - 30)))
        sub_surf = sub_font.render(sub, True, (200, 200, 200))
        self.window.blit(sub_surf, sub_surf.get_rect(center=(WIN_W // 2, WIN_H // 2 + 20)))
