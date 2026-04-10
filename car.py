"""Vehicle class with correct stop-line logic, car-following, and polished rendering."""

import pygame
from utils import (
    CAR_LENGTH, CAR_WIDTH, MIN_GAP,
    NORTH, SOUTH, EAST, WEST,
    STOP_LINE, INT_LEFT, INT_RIGHT, INT_TOP, INT_BOTTOM,
    WIDTH, HEIGHT, random_car_color,
)


class Car:
    """A single vehicle that moves through the intersection."""

    def __init__(self, x: float, y: float, vx: float, vy: float, direction: int):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.direction = direction
        self.waiting = False
        self.wait_time = 0
        self.color = random_car_color()
        self.crossed = False   # True once the car's BACK has cleared the intersection

    # ── geometry ─────────────────────────────────────────────────────

    def front_pos(self) -> float:
        """Leading-edge coordinate (the bumper closest to the intersection)."""
        if self.direction == NORTH:
            return self.y - CAR_LENGTH / 2     # top edge
        elif self.direction == SOUTH:
            return self.y + CAR_LENGTH / 2     # bottom edge
        elif self.direction == EAST:
            return self.x + CAR_LENGTH / 2     # right edge
        else:                                   # WEST
            return self.x - CAR_LENGTH / 2     # left edge

    def back_pos(self) -> float:
        """Trailing-edge coordinate."""
        if self.direction == NORTH:
            return self.y + CAR_LENGTH / 2
        elif self.direction == SOUTH:
            return self.y - CAR_LENGTH / 2
        elif self.direction == EAST:
            return self.x - CAR_LENGTH / 2
        else:
            return self.x + CAR_LENGTH / 2

    def is_inside_intersection(self) -> bool:
        """True if the car's bounding box overlaps the intersection box."""
        car_l = self.x - CAR_LENGTH / 2
        car_r = self.x + CAR_LENGTH / 2
        car_t = self.y - CAR_LENGTH / 2
        car_b = self.y + CAR_LENGTH / 2
        return (car_r > INT_LEFT and car_l < INT_RIGHT and
                car_b > INT_TOP  and car_t < INT_BOTTOM)

    def _approaching_stop_line(self) -> bool:
        """True if the car's front hasn't yet crossed the stop line."""
        front = self.front_pos()
        sl = STOP_LINE[self.direction]
        if self.direction == NORTH:
            return front > sl        # front is south of stop line (hasn't reached it)
        elif self.direction == SOUTH:
            return front < sl        # front is north of stop line
        elif self.direction == EAST:
            return front < sl        # front is west of stop line
        else:                        # WEST
            return front > sl        # front is east of stop line

    def front_at_or_past_stop(self) -> bool:
        """True if the front has reached or passed the stop line."""
        return not self._approaching_stop_line()

    # ── physics ──────────────────────────────────────────────────────

    def update(self, green_directions: set, cars_in_lane: list["Car"]):
        """Advance car by one frame: stop at red, yield to car ahead."""
        # Mark as crossed once fully past the intersection
        if not self.crossed and self._has_cleared_intersection():
            self.crossed = True

        should_stop = False

        # 1) Red-light stop: only if we haven't entered the intersection yet
        if not self.crossed and not self.is_inside_intersection():
            if self.direction not in green_directions:
                if self.front_at_or_past_stop():
                    should_stop = True

        # 2) Car-following: stop if the car ahead in this lane is too close
        if not should_stop:
            should_stop = self._car_ahead_too_close(cars_in_lane)

        if should_stop:
            self.waiting = True
            self.wait_time += 1
        else:
            self.waiting = False
            self.x += self.vx
            self.y += self.vy

    def _has_cleared_intersection(self) -> bool:
        """True once the trailing edge has exited the intersection."""
        back = self.back_pos()
        if self.direction == NORTH:
            return back < INT_TOP
        elif self.direction == SOUTH:
            return back > INT_BOTTOM
        elif self.direction == EAST:
            return back > INT_RIGHT
        else:
            return back < INT_LEFT

    def _car_ahead_too_close(self, cars_in_lane: list["Car"]) -> bool:
        """Return True if a car directly ahead is within safe following distance."""
        threshold = CAR_LENGTH + MIN_GAP
        for other in cars_in_lane:
            if other is self:
                continue
            gap = self._gap_to(other)
            if gap is not None and gap < threshold:
                return True
        return False

    def _gap_to(self, other: "Car"):
        """Distance from this car's front to other car's back, in travel direction.
        Returns None if the other car is not directly ahead."""
        if self.direction == NORTH:
            # Other must be further north (smaller y)
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

    def draw(self, surface: pygame.Surface):
        """Draw the car with body, cabin, windshield, and headlights."""
        if self.direction in (NORTH, SOUTH):
            w, h = CAR_WIDTH, CAR_LENGTH
        else:
            w, h = CAR_LENGTH, CAR_WIDTH

        bx = int(self.x - w / 2)
        by = int(self.y - h / 2)

        # Shadow
        shadow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 45))
        surface.blit(shadow_surf, (bx + 3, by + 3))

        # Body
        pygame.draw.rect(surface, self.color,
                         pygame.Rect(bx, by, w, h), border_radius=5)

        # Cabin (darker center strip)
        r, g, b = self.color
        darker = (max(r - 50, 0), max(g - 50, 0), max(b - 50, 0))
        if self.direction in (NORTH, SOUTH):
            cabin = pygame.Rect(bx + 3, by + int(h * 0.25), w - 6, int(h * 0.4))
        else:
            cabin = pygame.Rect(bx + int(w * 0.25), by + 3, int(w * 0.4), h - 6)
        pygame.draw.rect(surface, darker, cabin, border_radius=3)

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

    def has_exited(self) -> bool:
        margin = CAR_LENGTH + 20
        return (
            self.x < -margin or self.x > WIDTH + margin or
            self.y < -margin or self.y > HEIGHT + margin
        )
