"""Traffic environment: state, car spawning, reward calculation, with yellow light transition."""

import random
from typing import Tuple

from car import Car
from traffic_signal import TrafficSignal
from utils import (
    NORTH, SOUTH, EAST, WEST,
    SPAWN_POS, VELOCITY, SPAWN_PROB,
    discretize_count, SWITCH_PENALTY,
)

YELLOW_DURATION = 45 # 1.5 seconds at 30 FPS

class TrafficEnvironment:
    """Wraps cars + signal into an RL-friendly environment."""

    DIRECTIONS = [NORTH, SOUTH, EAST, WEST]

    def __init__(self):
        self.signal = TrafficSignal()
        self.cars: list[Car] = []
        self.previous_action: int = 0
        self.target_action: int = 0
        self.transition_timer: int = 0

        self.total_wait_frames: int = 0
        self.total_cars_served: int = 0

    def _cars_by_direction(self) -> dict[int, list[Car]]:
        groups: dict[int, list[Car]] = {d: [] for d in self.DIRECTIONS}
        for car in self.cars:
            groups[car.direction].append(car)
        return groups

    def get_state(self) -> Tuple[int, int, int, int]:
        counts = {d: 0 for d in self.DIRECTIONS}
        for car in self.cars:
            if car.waiting:
                counts[car.direction] += 1
        return tuple(discretize_count(counts[d]) for d in self.DIRECTIONS)

    def step(self, action: int) -> float:
        """
        RL calls this every DECISION_INTERVAL.
        """
        self.target_action = action
        if action != self.previous_action:
            if self.previous_action == 0:
                self.signal.set_state(1) # NS Yellow
            else:
                self.signal.set_state(3) # EW Yellow
            self.transition_timer = YELLOW_DURATION
        else:
            if action == 0:
                self.signal.set_state(0)
            else:
                self.signal.set_state(2)
            self.transition_timer = 0
        
        self.previous_action = action
        
        self._update_all_cars()
        waiting = self.waiting_count()
        reward = -waiting
        if action != self.previous_action:
            reward -= SWITCH_PENALTY
        return reward

    def tick_cars(self):
        """Advance cars one frame."""
        if self.transition_timer > 0:
            self.transition_timer -= 1
            if self.transition_timer == 0:
                # Transition complete, switch to target green
                if self.target_action == 0:
                    self.signal.set_state(0)
                else:
                    self.signal.set_state(2)

        self._update_all_cars()

    def _update_all_cars(self):
        greens = self.signal.green_directions()
        groups = self._cars_by_direction()

        for car in self.cars:
            car.update(greens, groups[car.direction])

        self.total_wait_frames += sum(1 for c in self.cars if c.waiting)
        before = len(self.cars)
        self.cars = [c for c in self.cars if not c.has_exited()]
        self.total_cars_served += before - len(self.cars)

    def spawn_cars(self):
        for d in self.DIRECTIONS:
            if random.random() < SPAWN_PROB:
                sx, sy = SPAWN_POS[d]
                if not self._spawn_blocked(d, sx, sy):
                    vx, vy = VELOCITY[d]
                    self.cars.append(Car(sx, sy, vx, vy, d))

    def _spawn_blocked(self, direction: int, sx: float, sy: float) -> bool:
        from utils import CAR_LENGTH, MIN_GAP
        threshold = CAR_LENGTH + MIN_GAP + 10
        for car in self.cars:
            if car.direction != direction:
                continue
            if direction in (NORTH, SOUTH):
                if abs(car.y - sy) < threshold:
                    return True
            else:
                if abs(car.x - sx) < threshold:
                    return True
        return False

    def waiting_count(self) -> int:
        return sum(1 for c in self.cars if c.waiting)

    def waiting_per_direction(self) -> dict[int, int]:
        counts = {d: 0 for d in self.DIRECTIONS}
        for car in self.cars:
            if car.waiting:
                counts[car.direction] += 1
        return counts

    def cars_per_direction(self) -> dict[int, int]:
        counts = {d: 0 for d in self.DIRECTIONS}
        for car in self.cars:
            counts[car.direction] += 1
        return counts

    def average_wait(self) -> float:
        waiters = [c for c in self.cars if c.waiting]
        if not waiters:
            return 0.0
        return sum(c.wait_time for c in waiters) / len(waiters) / 30.0

    def reset(self):
        self.cars.clear()
        self.signal.set_state(0)
        self.previous_action = 0
        self.target_action = 0
        self.transition_timer = 0
        self.total_wait_frames = 0
        self.total_cars_served = 0
