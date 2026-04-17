"""Traffic environment with two intersections, yellow transitions, and lane-aware updates."""

import random
from car import Car
from traffic_signal import TrafficSignal
from utils import (
    NORTH, SOUTH, EAST, WEST,
    ROUTES, SPAWN_PROB, CAR_LENGTH, MIN_GAP,
    INTERSECTIONS, discretize_count,
)

YELLOW_DURATION = 55  # ~1.8 s at 30 FPS (enough for worst-case clearance)


class TrafficEnvironment:
    """Manages cars, signals, spawning, and RL state for two intersections."""

    DIRECTIONS = [NORTH, SOUTH, EAST, WEST]

    def __init__(self):
        self.intersections = INTERSECTIONS
        self.signals = {inter.idx: TrafficSignal() for inter in self.intersections}
        self.cars: list[Car] = []

        self.previous_actions = {inter.idx: 0 for inter in self.intersections}
        self.target_actions   = {inter.idx: 0 for inter in self.intersections}
        self.transition_timers = {inter.idx: 0 for inter in self.intersections}

        self.total_wait_frames = 0
        self.total_cars_served = 0

    # ── lane grouping ────────────────────────────────────────────────

    def _cars_by_lane(self) -> dict:
        groups: dict[str, list[Car]] = {}
        for car in self.cars:
            groups.setdefault(car.lane_key, []).append(car)
        return groups

    # ── RL interface (per intersection) ──────────────────────────────

    def get_state(self, int_idx: int):
        """State for one intersection: (N_wait, S_wait, E_wait, W_wait)."""
        inter = self.intersections[int_idx]
        counts = {d: 0 for d in self.DIRECTIONS}
        for car in self.cars:
            if car.waiting and self._car_targets(car, inter):
                counts[car.direction] += 1
        return tuple(discretize_count(counts[d]) for d in self.DIRECTIONS)

    def step(self, int_idx: int, action: int):
        """Apply RL action (set signal phase) for one intersection."""
        signal = self.signals[int_idx]
        prev = self.previous_actions[int_idx]

        self.target_actions[int_idx] = action
        if action != prev:
            signal.set_state(1 if prev == 0 else 3)   # yellow
            self.transition_timers[int_idx] = YELLOW_DURATION
        else:
            if self.transition_timers[int_idx] == 0:
                signal.set_state(0 if action == 0 else 2)

        self.previous_actions[int_idx] = action

    # ── intersection clearance ───────────────────────────────────────

    def _intersection_clear(self, int_idx: int) -> bool:
        """True if no car from the OLD phase is still committed inside
        the intersection.  Used to hold yellow until safe to switch."""
        target = self.target_actions[int_idx]
        # Directions that belonged to the OLD phase
        if target == 0:          # switching TO NS green → old was EW
            old_dirs = {EAST, WEST}
        else:                    # switching TO EW green → old was NS
            old_dirs = {NORTH, SOUTH}

        for car in self.cars:
            if car.direction not in old_dirs:
                continue
            if not car.inside_current:
                continue
            if car.next_int_idx < len(car.intersections):
                if car.intersections[car.next_int_idx].idx == int_idx:
                    return False          # old-phase car still crossing
        return True

    def _blocked_intersections(self) -> set:
        """Return set of intersection indices where cross-traffic is still
        committed.  Cars check this before committing on green."""
        blocked = set()
        for inter in self.intersections:
            greens = self.signals[inter.idx].green_directions()
            if not greens:                     # yellow phase → block
                blocked.add(inter.idx)
                continue
            for car in self.cars:
                if car.direction in greens:    # same phase, no conflict
                    continue
                if not car.inside_current:
                    continue
                if car.next_int_idx < len(car.intersections):
                    if car.intersections[car.next_int_idx].idx == inter.idx:
                        blocked.add(inter.idx)
                        break
        return blocked

    # ── frame update ─────────────────────────────────────────────────

    def tick_cars(self):
        """Advance every car by one frame."""
        # Handle yellow → green transitions
        for int_idx in list(self.transition_timers):
            if self.transition_timers[int_idx] > 0:
                self.transition_timers[int_idx] -= 1
                if self.transition_timers[int_idx] == 0:
                    # Only grant green if intersection is clear of old-phase cars
                    if self._intersection_clear(int_idx):
                        target = self.target_actions[int_idx]
                        self.signals[int_idx].set_state(0 if target == 0 else 2)
                    else:
                        # Hold yellow — keep timer at 1 so we recheck next frame
                        self.transition_timers[int_idx] = 1

        # Compute which intersections still have cross-traffic inside
        blocked = self._blocked_intersections()

        # Update cars with lane-aware following + cross-traffic safety
        groups = self._cars_by_lane()
        for car in self.cars:
            lane_cars = groups.get(car.lane_key, [])
            car.update(self.signals, lane_cars, blocked)

        self.total_wait_frames += sum(1 for c in self.cars if c.waiting)

        before = len(self.cars)
        self.cars = [c for c in self.cars if not c.has_exited()]
        self.total_cars_served += before - len(self.cars)

    # ── spawning ─────────────────────────────────────────────────────

    def spawn_cars(self):
        for route in ROUTES:
            if random.random() < SPAWN_PROB:
                sx, sy = route["x"], route["y"]
                lane = route["lane"]
                if not self._spawn_blocked(lane, sx, sy, route["dir"]):
                    car = Car(sx, sy, route["vx"], route["vy"],
                              route["dir"], route["ints"], lane)
                    self.cars.append(car)

    def _spawn_blocked(self, lane, sx, sy, direction):
        threshold = CAR_LENGTH + MIN_GAP + 10
        for car in self.cars:
            if car.lane_key != lane:
                continue
            if direction in (NORTH, SOUTH):
                if abs(car.y - sy) < threshold:
                    return True
            else:
                if abs(car.x - sx) < threshold:
                    return True
        return False

    # ── helpers ──────────────────────────────────────────────────────

    def _car_targets(self, car, inter):
        """True if the car's NEXT uncleared intersection is *inter*."""
        if car.next_int_idx < len(car.intersections):
            return car.intersections[car.next_int_idx].idx == inter.idx
        return False

    def waiting_at(self, int_idx):
        inter = self.intersections[int_idx]
        return sum(1 for c in self.cars
                   if c.waiting and self._car_targets(c, inter))

    def waiting_count(self):
        return sum(1 for c in self.cars if c.waiting)

    def cars_at(self, int_idx):
        """Total cars (waiting + moving) targeting this intersection."""
        inter = self.intersections[int_idx]
        return sum(1 for c in self.cars if self._car_targets(c, inter))

    def average_wait(self):
        waiters = [c for c in self.cars if c.waiting]
        if not waiters:
            return 0.0
        return sum(c.wait_time for c in waiters) / len(waiters) / 30.0

    def reset(self):
        self.cars.clear()
        for sig in self.signals.values():
            sig.set_state(0)
        for k in self.previous_actions:
            self.previous_actions[k] = 0
            self.target_actions[k] = 0
            self.transition_timers[k] = 0
        self.total_wait_frames = 0
        self.total_cars_served = 0
