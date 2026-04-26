"""
gameconf.py — All constants for TSIS 4 Snake game.
"""

# ── Grid ──────────────────────────────────────
TILE_SIZE      = 20
GRID_COLS      = 30
GRID_ROWS      = 30
BOARD_WIDTH    = GRID_COLS * TILE_SIZE   # 600
BOARD_HEIGHT   = GRID_ROWS * TILE_SIZE   # 600
RENDER_FPS     = 60

# ── Directions ────────────────────────────────
DIR_RIGHT = (1,   0)
DIR_LEFT  = (-1,  0)
DIR_DOWN  = (0,   1)
DIR_UP    = (0,  -1)

# ── Snake speeds (logic steps per second) ─────
TPS_BY_LEVEL        = {1: 8, 2: 10, 3: 13, 4: 16, 5: 20}
TOP_LEVEL           = max(TPS_BY_LEVEL)
FOODS_TO_NEXT_LEVEL = 3

# ── Colours ───────────────────────────────────
COL_BLACK      = (0,   0,   0)
COL_WHITE      = (255, 255, 255)
COL_GRAY       = (50,  50,  50)
COL_LGRAY      = (140, 140, 140)
COL_DGRAY      = (25,  25,  35)
COL_BG         = (15,  15,  15)
COL_PANEL      = (30,  30,  45)
COL_WALL       = (80,  80,  80)
COL_DARK_GREEN = (0,   140, 0)
COL_GREEN      = (0,   200, 0)
COL_RED        = (220, 30,  30)
COL_GOLD       = (255, 200, 0)
COL_ACTIVE     = (255, 215, 50)
COL_TEAL       = (0,   180, 180)
COL_PURPLE     = (160, 0,   200)
COL_ORANGE     = (255, 140, 0)

# Poison food colour
COL_POISON     = (120, 0, 20)

# Obstacle block colour
COL_OBSTACLE   = (100, 80, 60)

# Power-up colours
POWERUP_COLOR_MAP = {
    "shield": (0,   220, 120),
    "slow":   (0,   160, 255),
    "speed":  (255, 160, 0),
}

# ── Food tiers (name, colour, score, grow, lifespan_s, weight) ──
FOOD_TIER_TABLE = [
    ("diamond", (100, 200, 255), 60, 3,  4.0, 10),
    ("cherry",  (255, 20,  147), 25, 2,  7.0, 30),
    ("apple",   (220, 50,  50),  10, 1, 10.0, 60),
]

MAX_FOOD_ON_BOARD = 3
FOOD_SPAWN_PERIOD = 3.5   # seconds

# ── Power-up settings ─────────────────────────
POWERUP_EFFECT_SECONDS = 5.0   # seconds effect lasts
POWERUP_FIELD_TTL      = 8.0   # seconds before disappears uncollected
SPEED_BOOST_TPS        = 6     # extra steps/sec when boosted
SLOW_MOTION_TPS        = 4     # steps/sec reduction when slowed

# ── Obstacles ────────────────────────────────
OBSTACLE_START_LEVEL = 3     # obstacles start appearing from level 3
OBSTACLES_PER_TIER   = 4     # extra blocks added each new level

# ── DB connection (edit to match your PostgreSQL setup) ──
PG_DB_CONFIG = {
    "password": "postgres",   # ← change to your password
    "user":     "postgres",
    "dbname":   "snake_db",
    "port":     5432,
    "host":     "localhost",
}

PREFS_PATH = "settings.json"

DEFAULT_PREFS = {
    "sound":       False,
    "grid":        True,
    "snake_color": [0, 200, 0],
}
