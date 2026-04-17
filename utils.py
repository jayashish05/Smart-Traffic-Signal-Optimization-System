"""Constants, intersection geometry, route definitions, and helpers."""

import random

# ─── Window & Layout ────────────────────────────────────────────────
WIDTH, HEIGHT = 1400, 800
FPS = 30
ROAD_WIDTH = 120
HALF_ROAD = ROAD_WIDTH // 2    # 60
LANE_WIDTH = ROAD_WIDTH // 2   # 60
CENTER_Y = HEIGHT // 2         # 400

# ─── Directions ─────────────────────────────────────────────────────
NORTH = 0
SOUTH = 1
EAST  = 2
WEST  = 3
DIRECTION_NAMES = {NORTH: "N", SOUTH: "S", EAST: "E", WEST: "W"}

# ─── Vehicle ────────────────────────────────────────────────────────
CAR_LENGTH = 30
CAR_WIDTH  = 22
CAR_SPEED  = 3
MIN_GAP    = 8

# ─── RL / Simulation ────────────────────────────────────────────────
DECISION_INTERVAL = 150
MAX_CARS_PER_DIR  = 5
SPAWN_PROB        = 0.02
SWITCH_PENALTY    = 2

# ─── Colors ─────────────────────────────────────────────────────────
COLOR_BG           = (25, 27, 35)
COLOR_ROAD         = (55, 58, 66)
COLOR_ROAD_EDGE    = (75, 78, 86)
COLOR_LANE_MARK    = (180, 180, 160)
COLOR_CROSSWALK    = (200, 200, 190)
COLOR_INTERSECTION = (48, 50, 58)
COLOR_RED          = (220, 50, 47)
COLOR_GREEN        = (40, 200, 100)
COLOR_YELLOW       = (250, 200, 50)
COLOR_SIGNAL_DARK  = (30, 30, 30)
COLOR_CAR_BODY     = [
    (52, 152, 219), (46, 204, 113), (231, 76, 60), (243, 156, 18),
    (155, 89, 182), (26, 188, 156), (241, 196, 15), (230, 126, 34),
]
COLOR_TEXT          = (240, 240, 235)
COLOR_TEXT_DIM      = (140, 145, 155)
COLOR_PANEL_BG      = (20, 22, 30)


# ─── Intersection geometry ──────────────────────────────────────────

class IntersectionConfig:
    """Bounding box and stop-line positions for one intersection."""

    def __init__(self, idx: int, cx: int, cy: int):
        self.idx = idx
        self.cx = cx
        self.cy = cy
        self.left   = cx - HALF_ROAD
        self.right  = cx + HALF_ROAD
        self.top    = cy - HALF_ROAD
        self.bottom = cy + HALF_ROAD

    def stop_line(self, direction: int) -> int:
        """Position where the FRONT of a car must stop on red."""
        if direction == NORTH:
            return self.bottom + 4
        elif direction == SOUTH:
            return self.top - 4
        elif direction == EAST:
            return self.left - 4
        elif direction == WEST:
            return self.right + 4
        return 0


INTERSECTIONS = [
    IntersectionConfig(0, 400, CENTER_Y),
    IntersectionConfig(1, 1000, CENTER_Y),
]

INT0 = INTERSECTIONS[0]
INT1 = INTERSECTIONS[1]

# ─── Route definitions ──────────────────────────────────────────────
# Each route: spawn pos, velocity, direction, list of intersections to
# cross (in order), and a lane key for car-following grouping.

EB_Y = CENTER_Y + LANE_WIDTH // 2   # 430  (eastbound lane)
WB_Y = CENTER_Y - LANE_WIDTH // 2   # 370  (westbound lane)

ROUTES = [
    # Northbound at Junction 1
    {"x": INT0.cx + LANE_WIDTH // 2, "y": HEIGHT + CAR_LENGTH,
     "vx": 0, "vy": -CAR_SPEED, "dir": NORTH,
     "ints": [INT0], "lane": "N0"},
    # Southbound at Junction 1
    {"x": INT0.cx - LANE_WIDTH // 2, "y": -CAR_LENGTH,
     "vx": 0, "vy": CAR_SPEED, "dir": SOUTH,
     "ints": [INT0], "lane": "S0"},
    # Northbound at Junction 2
    {"x": INT1.cx + LANE_WIDTH // 2, "y": HEIGHT + CAR_LENGTH,
     "vx": 0, "vy": -CAR_SPEED, "dir": NORTH,
     "ints": [INT1], "lane": "N1"},
    # Southbound at Junction 2
    {"x": INT1.cx - LANE_WIDTH // 2, "y": -CAR_LENGTH,
     "vx": 0, "vy": CAR_SPEED, "dir": SOUTH,
     "ints": [INT1], "lane": "S1"},
    # Eastbound — crosses Junction 1 then Junction 2
    {"x": -CAR_LENGTH, "y": EB_Y,
     "vx": CAR_SPEED, "vy": 0, "dir": EAST,
     "ints": [INT0, INT1], "lane": "E"},
    # Westbound — crosses Junction 2 then Junction 1
    {"x": WIDTH + CAR_LENGTH, "y": WB_Y,
     "vx": -CAR_SPEED, "vy": 0, "dir": WEST,
     "ints": [INT1, INT0], "lane": "W"},
]


# ─── Helpers ────────────────────────────────────────────────────────

def discretize_count(n: int) -> int:
    return min(n, MAX_CARS_PER_DIR)

def random_car_color():
    return random.choice(COLOR_CAR_BODY)
