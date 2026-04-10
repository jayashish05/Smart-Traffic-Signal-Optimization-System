"""Constants, color palette, and helper functions for the traffic simulation."""

import random

# ─── Window & Layout ────────────────────────────────────────────────
WIDTH, HEIGHT = 800, 800
FPS = 30

ROAD_WIDTH = 120                       # total width of a road (2 lanes)
HALF_ROAD = ROAD_WIDTH // 2            # 60 px
LANE_WIDTH = ROAD_WIDTH // 2           # each lane is 60 px

CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

# Intersection bounding box
INT_LEFT   = CENTER_X - HALF_ROAD
INT_RIGHT  = CENTER_X + HALF_ROAD
INT_TOP    = CENTER_Y - HALF_ROAD
INT_BOTTOM = CENTER_Y + HALF_ROAD

# ─── Directions ─────────────────────────────────────────────────────
NORTH = 0          # heading upward (y decreasing)
SOUTH = 1          # heading downward (y increasing)
EAST  = 2          # heading right (x increasing)
WEST  = 3          # heading left (x decreasing)

DIRECTION_NAMES = {NORTH: "North", SOUTH: "South", EAST: "East", WEST: "West"}

# ─── Vehicle geometry ───────────────────────────────────────────────
CAR_LENGTH = 30
CAR_WIDTH  = 22
CAR_SPEED  = 3
MIN_GAP    = 8      # minimum bumper-to-bumper gap between cars

# Lane centre positions (right-hand traffic: drive on the right)
LANE_CENTER = {
    NORTH: CENTER_X + LANE_WIDTH // 2,   # right half of vertical road
    SOUTH: CENTER_X - LANE_WIDTH // 2,   # left half of vertical road
    EAST:  CENTER_Y + LANE_WIDTH // 2,   # bottom half of horizontal road
    WEST:  CENTER_Y - LANE_WIDTH // 2,   # top half of horizontal road
}

# Spawn configs: (x, y) where cars appear
SPAWN_POS = {
    NORTH: (LANE_CENTER[NORTH], HEIGHT + CAR_LENGTH),
    SOUTH: (LANE_CENTER[SOUTH], -CAR_LENGTH),
    EAST:  (-CAR_LENGTH, LANE_CENTER[EAST]),
    WEST:  (WIDTH + CAR_LENGTH, LANE_CENTER[WEST]),
}

# Velocity vectors
VELOCITY = {
    NORTH: (0, -CAR_SPEED),
    SOUTH: (0,  CAR_SPEED),
    EAST:  ( CAR_SPEED, 0),
    WEST:  (-CAR_SPEED, 0),
}

# Stop-line: the coordinate at which the FRONT of the car must stop
STOP_LINE = {
    NORTH: INT_BOTTOM + 4,       # front of car (top edge) stops here
    SOUTH: INT_TOP - 4,          # front of car (bottom edge) stops here
    EAST:  INT_LEFT - 4,         # front of car (right edge) stops here
    WEST:  INT_RIGHT + 4,        # front of car (left edge) stops here
}

# ─── Colors ─────────────────────────────────────────────────────────
COLOR_BG            = (25, 27, 35)
COLOR_GRASS         = (34, 45, 30)
COLOR_ROAD          = (55, 58, 66)
COLOR_ROAD_EDGE     = (75, 78, 86)
COLOR_LANE_MARK     = (180, 180, 160)
COLOR_CROSSWALK     = (200, 200, 190)
COLOR_INTERSECTION  = (48, 50, 58)

COLOR_RED           = (220, 50, 47)
COLOR_GREEN         = (40, 200, 100)
COLOR_YELLOW        = (250, 200, 50)
COLOR_SIGNAL_DARK   = (30, 30, 30)

COLOR_CAR_BODY      = [
    (52, 152, 219),    # blue
    (46, 204, 113),    # green
    (231, 76, 60),     # red
    (243, 156, 18),    # orange
    (155, 89, 182),    # purple
    (26, 188, 156),    # teal
    (241, 196, 15),    # yellow
    (230, 126, 34),    # dark orange
]

COLOR_TEXT           = (240, 240, 235)
COLOR_TEXT_DIM       = (140, 145, 155)
COLOR_PANEL_BG       = (20, 22, 30)

# ─── RL / Simulation ────────────────────────────────────────────────
DECISION_INTERVAL = 150      # frames between RL decisions (~5 s at 30 FPS)
MAX_CARS_PER_DIR  = 5        # discretisation cap for Q-table state
SPAWN_PROB        = 0.025    # per direction per frame
SWITCH_PENALTY    = 2        # reward penalty for changing phase

# ─── Helpers ────────────────────────────────────────────────────────

def discretize_count(n: int) -> int:
    """Clamp car count to [0, MAX_CARS_PER_DIR]."""
    return min(n, MAX_CARS_PER_DIR)


def random_car_color():
    """Return a random car body color from the palette."""
    return random.choice(COLOR_CAR_BODY)
