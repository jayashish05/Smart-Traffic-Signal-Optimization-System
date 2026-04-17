"""Q-learning agent with persistent Q-table (pickle save/load)."""

import os
import pickle
import random
from collections import defaultdict

SAVE_DIR = os.path.dirname(os.path.abspath(__file__))


class QLearningAgent:
    """Tabular Q-learning with epsilon-greedy exploration and disk persistence."""

    def __init__(
        self,
        n_actions: int = 2,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.9995,
        save_name: str = "q_table",
    ):
        self.n_actions = n_actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.q_table: dict = defaultdict(float)
        self.save_path = os.path.join(SAVE_DIR, f"{save_name}.pkl")

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.randint(0, self.n_actions - 1)
        q_values = [self.q_table[(state, a)] for a in range(self.n_actions)]
        max_q = max(q_values)
        best = [a for a, q in enumerate(q_values) if q == max_q]
        return random.choice(best)

    def update(self, state, action, reward, next_state):
        best_next = max(
            self.q_table[(next_state, a)] for a in range(self.n_actions)
        )
        current = self.q_table[(state, action)]
        self.q_table[(state, action)] = current + self.alpha * (
            reward + self.gamma * best_next - current
        )

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def q_table_size(self) -> int:
        return len(self.q_table)

    # ── persistence ──────────────────────────────────────────────────

    def save(self):
        """Write Q-table and epsilon to disk."""
        data = {"q_table": dict(self.q_table), "epsilon": self.epsilon}
        with open(self.save_path, "wb") as f:
            pickle.dump(data, f)

    def load(self) -> bool:
        """Load Q-table from disk. Returns True if a file was found."""
        if os.path.exists(self.save_path):
            with open(self.save_path, "rb") as f:
                data = pickle.load(f)
            self.q_table = defaultdict(float, data["q_table"])
            self.epsilon = data.get("epsilon", self.epsilon_min)
            return True
        return False
