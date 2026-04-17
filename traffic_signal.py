"""Traffic signal with Green → Yellow → Red phases and rendering."""

import pygame
from utils import (
    NORTH, SOUTH, EAST, WEST,
    HALF_ROAD,
    COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_SIGNAL_DARK,
    DECISION_INTERVAL,
)


class TrafficSignal:
    """4-state signal: 0=NS Green, 1=NS Yellow, 2=EW Green, 3=EW Yellow."""

    def __init__(self):
        self.state = 0

    def set_state(self, state):
        self.state = state % 4

    def get_state(self):
        return self.state

    def get_phase(self):
        return 0 if self.state in (0, 1) else 1

    def green_directions(self):
        if self.state == 0:
            return {NORTH, SOUTH}
        elif self.state == 2:
            return {EAST, WEST}
        return set()       # yellow → nobody gets green

    def _get_lights(self):
        if self.state == 0:
            return {NORTH: "G", SOUTH: "G", EAST: "R", WEST: "R"}
        elif self.state == 1:
            return {NORTH: "Y", SOUTH: "Y", EAST: "R", WEST: "R"}
        elif self.state == 2:
            return {NORTH: "R", SOUTH: "R", EAST: "G", WEST: "G"}
        else:
            return {NORTH: "R", SOUTH: "R", EAST: "Y", WEST: "Y"}

    def draw(self, surface, cx, cy):
        """Draw four signal boxes around the intersection centred at (cx, cy)."""
        lights = self._get_lights()
        offset = HALF_ROAD + 25

        positions = {
            NORTH: (cx + offset, cy - offset),
            SOUTH: (cx - offset, cy + offset),
            EAST:  (cx + offset, cy + offset),
            WEST:  (cx - offset, cy - offset),
        }

        for direction, (px, py) in positions.items():
            self._draw_signal_box(surface, px, py, lights[direction])

    def _draw_signal_box(self, surface, x, y, code):
        box_w, box_h = 24, 62
        rect = pygame.Rect(x - box_w // 2, y - box_h // 2, box_w, box_h)
        pygame.draw.rect(surface, COLOR_SIGNAL_DARK, rect, border_radius=6)
        pygame.draw.rect(surface, (70, 70, 80), rect, width=2, border_radius=6)

        for dy, active_code, on_col, off_col in [
            (-18, "R", COLOR_RED,    (80, 30, 25)),
            (  0, "Y", COLOR_YELLOW, (80, 60, 20)),
            ( 18, "G", COLOR_GREEN,  (20, 60, 35)),
        ]:
            cx, cy = x, y + dy
            is_on = (code == active_code)
            col = on_col if is_on else off_col
            if is_on:
                glow = pygame.Surface((30, 30), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*on_col, 50), (15, 15), 14)
                surface.blit(glow, (cx - 15, cy - 15))
            pygame.draw.circle(surface, col, (cx, cy), 6)


class FixedTimerController:
    """Green/yellow cycling on a fixed timer."""

    def __init__(self, green_interval=DECISION_INTERVAL, yellow_interval=45):
        self.green_interval = green_interval
        self.yellow_interval = yellow_interval
        self.counter = 0

    def tick(self, signal):
        self.counter += 1
        state = signal.get_state()
        if state in (0, 2):
            if self.counter >= self.green_interval:
                self.counter = 0
                signal.set_state(state + 1)
        else:
            if self.counter >= self.yellow_interval:
                self.counter = 0
                signal.set_state((state + 1) % 4)

    def reset(self):
        self.counter = 0
