"""Vehicle with multi-intersection stop logic, car-following, and rendering."""

import pygame
from utils import (
    CAR_LENGTH, CAR_WIDTH, MIN_GAP,
    NORTH, SOUTH, EAST, WEST,
    WIDTH, HEIGHT, random_car_color,
)


class Car:
    """A vehicle that travels through one or more intersections."""

    def __init__(self, x, y, vx, vy, direction, intersections, lane_key):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.direction = direction
        self.intersections = list(intersections)
        self.lane_key = lane_key

        self.next_int_idx = 0        # which intersection we're approaching next
        self.inside_current = False  # True once committed to crossing

        self.waiting = False
        self.wait_time = 0
        self.color = random_car_color()

    # ── geometry ─────────────────────────────────────────────────────

    def front_pos(self):
        """Leading-edge coordinate in the direction of travel."""
        if self.direction == NORTH:
            return self.y - CAR_LENGTH / 2
        elif self.direction == SOUTH:
            return self.y + CAR_LENGTH / 2
        elif self.direction == EAST:
            return self.x + CAR_LENGTH / 2
        else:
            return self.x - CAR_LENGTH / 2

    def back_pos(self):
        """Trailing-edge coordinate."""
        if self.direction == NORTH:
            return self.y + CAR_LENGTH / 2
        elif self.direction == SOUTH:
            return self.y - CAR_LENGTH / 2
        elif self.direction == EAST:
            return self.x - CAR_LENGTH / 2
        else:
            return self.x + CAR_LENGTH / 2

    # ── update ───────────────────────────────────────────────────────

    def update(self, signals, cars_in_lane):
        """Advance one frame.

        Args:
            signals: dict mapping intersection idx → TrafficSignal.
            cars_in_lane: list of Car objects sharing this lane.
        """
        should_stop = False

        if self.next_int_idx < len(self.intersections):
            inter = self.intersections[self.next_int_idx]

            # Check if we've fully cleared the current intersection
            if self.inside_current and self._has_cleared(inter):
                self.next_int_idx += 1
                self.inside_current = False

        # Possibly approach the next intersection
        if not self.inside_current and self.next_int_idx < len(self.intersections):
            inter = self.intersections[self.next_int_idx]
            signal = signals[inter.idx]
            at_stop = self._front_at_or_past_stop(inter)

            if at_stop:
                if self.direction in signal.green_directions():
                    # Green → commit to entering
                    self.inside_current = True
                else:
                    # Red / Yellow → stop
                    should_stop = True

        # Car-following
        if not should_stop:
            should_stop = self._car_ahead_too_close(cars_in_lane)

        if should_stop:
            self.waiting = True
            self.wait_time += 1
        else:
            self.waiting = False
            self.x += self.vx
            self.y += self.vy

    # ── stop-line helpers ────────────────────────────────────────────

    def _front_at_or_past_stop(self, inter):
        """True when the front bumper has reached or passed the stop line."""
        front = self.front_pos()
        sl = inter.stop_line(self.direction)
        if self.direction == NORTH:
            return front <= sl
        elif self.direction == SOUTH:
            return front >= sl
        elif self.direction == EAST:
            return front >= sl
        else:
            return front <= sl

    def _has_cleared(self, inter):
        """True when the entire car has exited the intersection box."""
        back = self.back_pos()
        if self.direction == NORTH:
            return back < inter.top
        elif self.direction == SOUTH:
            return back > inter.bottom
        elif self.direction == EAST:
            return back > inter.right
        else:
            return back < inter.left

    # ── car-following ────────────────────────────────────────────────

    def _car_ahead_too_close(self, cars_in_lane):
        threshold = CAR_LENGTH + MIN_GAP
        for other in cars_in_lane:
            if other is self:
                continue
            gap = self._gap_to(other)
            if gap is not None and 0 <= gap < threshold:
                return True
        return False

    def _gap_to(self, other):
        """Bumper-to-bumper gap to car ahead (None if not ahead)."""
        if self.direction == NORTH:
            if other.y < self.y:
                return self.front_pos() - other.back_pos()
        elif self.direction == SOUTH:
            if other.y > self.y:
                return other.back_pos() - self.front_pos()
        elif self.direction == EAST:
            if other.x > self.x:
                return other.back_pos() - self.front_pos()
        elif self.direction == WEST:
            if other.x < self.x:
                return self.front_pos() - other.back_pos()
        return None

    # ── rendering ────────────────────────────────────────────────────

    def draw(self, surface):
        if self.direction in (NORTH, SOUTH):
            w, h = CAR_WIDTH, CAR_LENGTH
        else:
            w, h = CAR_LENGTH, CAR_WIDTH

        bx = int(self.x - w / 2)
        by = int(self.y - h / 2)

        # Shadow
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((0, 0, 0, 45))
        surface.blit(s, (bx + 3, by + 3))

        # Body
        pygame.draw.rect(surface, self.color,
                         pygame.Rect(bx, by, w, h), border_radius=5)

        # Cabin
        r, g, b = self.color
        dk = (max(r - 50, 0), max(g - 50, 0), max(b - 50, 0))
        if self.direction in (NORTH, SOUTH):
            c = pygame.Rect(bx + 3, by + int(h * 0.25), w - 6, int(h * 0.4))
        else:
            c = pygame.Rect(bx + int(w * 0.25), by + 3, int(w * 0.4), h - 6)
        pygame.draw.rect(surface, dk, c, border_radius=3)

        # Windshield
        ws = (180, 210, 230)
        if self.direction == NORTH:
            pygame.draw.rect(surface, ws,
                             pygame.Rect(bx + 4, by + 3, w - 8, 5), border_radius=2)
        elif self.direction == SOUTH:
            pygame.draw.rect(surface, ws,
                             pygame.Rect(bx + 4, by + h - 8, w - 8, 5), border_radius=2)
        elif self.direction == EAST:
            pygame.draw.rect(surface, ws,
                             pygame.Rect(bx + w - 8, by + 4, 5, h - 8), border_radius=2)
        else:
            pygame.draw.rect(surface, ws,
                             pygame.Rect(bx + 3, by + 4, 5, h - 8), border_radius=2)

        # Headlights
        hl = (255, 255, 190)
        if self.direction == NORTH:
            pygame.draw.circle(surface, hl, (bx + 4, by + 3), 2)
            pygame.draw.circle(surface, hl, (bx + w - 4, by + 3), 2)
        elif self.direction == SOUTH:
            pygame.draw.circle(surface, hl, (bx + 4, by + h - 3), 2)
            pygame.draw.circle(surface, hl, (bx + w - 4, by + h - 3), 2)
        elif self.direction == EAST:
            pygame.draw.circle(surface, hl, (bx + w - 3, by + 4), 2)
            pygame.draw.circle(surface, hl, (bx + w - 3, by + h - 4), 2)
        else:
            pygame.draw.circle(surface, hl, (bx + 3, by + 4), 2)
            pygame.draw.circle(surface, hl, (bx + 3, by + h - 4), 2)

    # ── lifecycle ────────────────────────────────────────────────────

    def has_exited(self):
        margin = CAR_LENGTH + 20
        return (self.x < -margin or self.x > WIDTH + margin or
                self.y < -margin or self.y > HEIGHT + margin)
