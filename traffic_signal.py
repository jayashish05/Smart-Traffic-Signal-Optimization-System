"""Traffic signal logic with polished rendering (traffic light boxes + glow)."""

import pygame
from utils import (
    NORTH, SOUTH, EAST, WEST,
    CENTER_X, CENTER_Y, HALF_ROAD,
    COLOR_RED, COLOR_GREEN, COLOR_YELLOW, COLOR_SIGNAL_DARK,
    DECISION_INTERVAL,
)

class TrafficSignal:
    """Manages the current signal phase for a 4-way intersection.

    state:
      0 = N/S Green
      1 = N/S Yellow
      2 = E/W Green
      3 = E/W Yellow
    """

    def __init__(self):
        self.state = 0

    def set_state(self, state: int):
        self.state = state % 4

    def get_state(self) -> int:
        return self.state

    def get_phase(self) -> int:
        """Return high-level phase (0 = NS, 1 = EW) based on current state."""
        if self.state in (0, 1):
            return 0
        return 1

    def green_directions(self) -> set:
        if self.state == 0:
            return {NORTH, SOUTH}
        elif self.state == 2:
            return {EAST, WEST}
        return set() # Yellow states act as red for approaching cars

    def _get_lights(self) -> dict:
        """Return light color for each direction"""
        if self.state == 0:
            return {NORTH: "G", SOUTH: "G", EAST: "R", WEST: "R"}
        elif self.state == 1:
            return {NORTH: "Y", SOUTH: "Y", EAST: "R", WEST: "R"}
        elif self.state == 2:
            return {NORTH: "R", SOUTH: "R", EAST: "G", WEST: "G"}
        elif self.state == 3:
            return {NORTH: "R", SOUTH: "R", EAST: "Y", WEST: "Y"}
        return {NORTH: "R", SOUTH: "R", EAST: "R", WEST: "R"}

    def draw(self, surface: pygame.Surface):
        lights = self._get_lights()
        offset = HALF_ROAD + 25   # distance from centre to the signal post

        positions = {
            NORTH: (CENTER_X + offset, CENTER_Y - offset),      # top-right
            SOUTH: (CENTER_X - offset, CENTER_Y + offset),      # bottom-left
            EAST:  (CENTER_X + offset, CENTER_Y + offset),      # bottom-right
            WEST:  (CENTER_X - offset, CENTER_Y - offset),      # top-left
        }

        for direction, (px, py) in positions.items():
            color_code = lights[direction]
            self._draw_signal_box(surface, px, py, color_code, direction)

    def _draw_signal_box(self, surface, x, y, color_code, direction):
        box_w, box_h = 24, 62

        # Box background
        box_rect = pygame.Rect(x - box_w // 2, y - box_h // 2, box_w, box_h)
        pygame.draw.rect(surface, COLOR_SIGNAL_DARK, box_rect, border_radius=6)
        pygame.draw.rect(surface, (70, 70, 80), box_rect, width=2, border_radius=6)

        # Draw Red, Yellow, Green vertically
        red_center = (x, y - 18)
        is_red = (color_code == "R")
        r_col = COLOR_RED if is_red else (80, 30, 25)
        if is_red:
            glow = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*COLOR_RED, 50), (15, 15), 14)
            surface.blit(glow, (red_center[0] - 15, red_center[1] - 15))
        pygame.draw.circle(surface, r_col, red_center, 6)

        yellow_center = (x, y)
        is_yellow = (color_code == "Y")
        y_col = COLOR_YELLOW if is_yellow else (80, 60, 20)
        if is_yellow:
            glow = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*COLOR_YELLOW, 50), (15, 15), 14)
            surface.blit(glow, (yellow_center[0] - 15, yellow_center[1] - 15))
        pygame.draw.circle(surface, y_col, yellow_center, 6)

        green_center = (x, y + 18)
        is_green = (color_code == "G")
        g_col = COLOR_GREEN if is_green else (20, 60, 35)
        if is_green:
            glow = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*COLOR_GREEN, 50), (15, 15), 14)
            surface.blit(glow, (green_center[0] - 15, green_center[1] - 15))
        pygame.draw.circle(surface, g_col, green_center, 6)

        # Post (thin line from box to road edge)
        if direction == NORTH:
            pygame.draw.line(surface, (70, 70, 80), (x, y + box_h // 2), (x, y + box_h // 2 + 12), 3)
        elif direction == SOUTH:
            pygame.draw.line(surface, (70, 70, 80), (x, y - box_h // 2), (x, y - box_h // 2 - 12), 3)
        elif direction == EAST:
            pygame.draw.line(surface, (70, 70, 80), (x - box_w // 2, y), (x - box_w // 2 - 12, y), 3)
        elif direction == WEST:
            pygame.draw.line(surface, (70, 70, 80), (x + box_w // 2, y), (x + box_w // 2 + 12, y), 3)

class FixedTimerController:
    """Handles green and yellow phases automatically."""
    def __init__(self, green_interval: int = DECISION_INTERVAL, yellow_interval: int = 45):
        self.green_interval = green_interval
        self.yellow_interval = yellow_interval
        self.counter = 0

    def tick(self, signal: TrafficSignal):
        self.counter += 1
        state = signal.get_state()
        if state in (0, 2): # Green phase
            if self.counter >= self.green_interval:
                self.counter = 0
                signal.set_state(state + 1) # Go to Yellow
        else: # Yellow phase
            if self.counter >= self.yellow_interval:
                self.counter = 0
                signal.set_state((state + 1) % 4) # Go to next Green

    def reset(self):
        self.counter = 0
