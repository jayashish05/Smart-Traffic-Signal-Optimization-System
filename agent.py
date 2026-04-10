"""Q-learning agent for traffic signal control."""

import random
from collections import defaultdict
from typing import Tuple


class QLearningAgent:
    """Tabular Q-learning with epsilon-greedy exploration."""

    def __init__(
        self,
        n_actions: int = 2,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.9995,
    ):
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.q_table: dict[Tuple, float] = defaultdict(float)

    def choose_action(self, state: Tuple) -> int:
        """Select action using epsilon-greedy policy."""
        if random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)

        q_values = [self.q_table[(state, a)] for a in range(self.n_actions)]
        max_q = max(q_values)
        # break ties randomly
        best_actions = [a for a, q in enumerate(q_values) if q == max_q]
        return random.choice(best_actions)

    def update(
        self,
        state: Tuple,
        action: int,
        reward: float,
        next_state: Tuple,
    ):
        """Standard Q-learning update rule."""
        best_next = max(
            self.q_table[(next_state, a)] for a in range(self.n_actions)
        )
        current = self.q_table[(state, action)]
        self.q_table[(state, action)] = current + self.alpha * (
            reward + self.gamma * best_next - current
        )

    def decay_epsilon(self):
        """Decay exploration rate toward minimum."""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def q_table_size(self) -> int:
        return len(self.q_table)
