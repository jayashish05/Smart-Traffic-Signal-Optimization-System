"""Main entry point — Pygame loop, premium road rendering, polished UI overlay."""

import sys
import pygame
import matplotlib
matplotlib.use("Agg")          # so plt.savefig works headlessly; we show with plt.show after
import matplotlib.pyplot as plt

from utils import (
    WIDTH, HEIGHT, FPS,
    CENTER_X, CENTER_Y, HALF_ROAD, ROAD_WIDTH, LANE_WIDTH,
    INT_LEFT, INT_RIGHT, INT_TOP, INT_BOTTOM,
    DECISION_INTERVAL,
    COLOR_BG, COLOR_ROAD, COLOR_ROAD_EDGE, COLOR_LANE_MARK,
    COLOR_CROSSWALK, COLOR_INTERSECTION,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_PANEL_BG,
    COLOR_GREEN, COLOR_RED,
    NORTH, SOUTH, EAST, WEST, DIRECTION_NAMES,
)
from environment import TrafficEnvironment
from agent import QLearningAgent
from traffic_signal import FixedTimerController


# ═══════════════════════════════════════════════════════════════════════
#  Road drawing
# ═══════════════════════════════════════════════════════════════════════

def draw_roads(surface: pygame.Surface):
    """Draw roads, lane markings, crosswalks, and intersection."""

    # ── road surfaces ────────────────────────────────────────────────
    # Vertical road
    v_road = pygame.Rect(CENTER_X - HALF_ROAD, 0, ROAD_WIDTH, HEIGHT)
    pygame.draw.rect(surface, COLOR_ROAD, v_road)
    # Horizontal road
    h_road = pygame.Rect(0, CENTER_Y - HALF_ROAD, WIDTH, ROAD_WIDTH)
    pygame.draw.rect(surface, COLOR_ROAD, h_road)

    # ── intersection fill ────────────────────────────────────────────
    inter = pygame.Rect(INT_LEFT, INT_TOP, ROAD_WIDTH, ROAD_WIDTH)
    pygame.draw.rect(surface, COLOR_INTERSECTION, inter)

    # ── road edges ───────────────────────────────────────────────────
    for offset in (-HALF_ROAD, HALF_ROAD):
        # Vertical edges (skip intersection)
        for seg in [(0, INT_TOP), (INT_BOTTOM, HEIGHT)]:
            pygame.draw.line(surface, COLOR_ROAD_EDGE,
                             (CENTER_X + offset, seg[0]),
                             (CENTER_X + offset, seg[1]), 2)
        # Horizontal edges
        for seg in [(0, INT_LEFT), (INT_RIGHT, WIDTH)]:
            pygame.draw.line(surface, COLOR_ROAD_EDGE,
                             (seg[0], CENTER_Y + offset),
                             (seg[1], CENTER_Y + offset), 2)

    # ── dashed centre lines ──────────────────────────────────────────
    dash, gap = 18, 14
    # Vertical
    y = 0
    while y < HEIGHT:
        if not (INT_TOP - 5 <= y <= INT_BOTTOM + 5):
            ye = min(y + dash, HEIGHT)
            pygame.draw.line(surface, COLOR_LANE_MARK,
                             (CENTER_X, y), (CENTER_X, ye), 2)
        y += dash + gap
    # Horizontal
    x = 0
    while x < WIDTH:
        if not (INT_LEFT - 5 <= x <= INT_RIGHT + 5):
            xe = min(x + dash, WIDTH)
            pygame.draw.line(surface, COLOR_LANE_MARK,
                             (x, CENTER_Y), (xe, CENTER_Y), 2)
        x += dash + gap

    # ── crosswalks ───────────────────────────────────────────────────
    cw_width = 6
    cw_gap = 6
    cw_inset = 8     # distance inside the intersection edge

    # Top crosswalk (horizontal stripes at top of intersection)
    cy = INT_TOP + cw_inset
    x_start = INT_LEFT + 4
    while x_start < INT_RIGHT - 4:
        pygame.draw.rect(surface, COLOR_CROSSWALK,
                         (x_start, cy, cw_width, 3))
        x_start += cw_width + cw_gap

    # Bottom crosswalk
    cy = INT_BOTTOM - cw_inset - 3
    x_start = INT_LEFT + 4
    while x_start < INT_RIGHT - 4:
        pygame.draw.rect(surface, COLOR_CROSSWALK,
                         (x_start, cy, cw_width, 3))
        x_start += cw_width + cw_gap

    # Left crosswalk (vertical stripes)
    cx = INT_LEFT + cw_inset
    y_start = INT_TOP + 4
    while y_start < INT_BOTTOM - 4:
        pygame.draw.rect(surface, COLOR_CROSSWALK,
                         (cx, y_start, 3, cw_width))
        y_start += cw_width + cw_gap

    # Right crosswalk
    cx = INT_RIGHT - cw_inset - 3
    y_start = INT_TOP + 4
    while y_start < INT_BOTTOM - 4:
        pygame.draw.rect(surface, COLOR_CROSSWALK,
                         (cx, y_start, 3, cw_width))
        y_start += cw_width + cw_gap

    # ── direction labels ─────────────────────────────────────────────
    label_font = pygame.font.SysFont("arial", 13, bold=True)
    labels = {
        "N ▲": (CENTER_X + HALF_ROAD + 15, CENTER_Y + HALF_ROAD + 15),
        "S ▼": (CENTER_X - HALF_ROAD - 25, CENTER_Y - HALF_ROAD - 22),
        "E ►": (INT_RIGHT + 15, CENTER_Y + HALF_ROAD + 15),
        "W ◄": (INT_LEFT - 35, CENTER_Y - HALF_ROAD - 22),
    }
    for text, pos in labels.items():
        surf = label_font.render(text, True, COLOR_TEXT_DIM)
        surface.blit(surf, pos)


# ═══════════════════════════════════════════════════════════════════════
#  UI overlay
# ═══════════════════════════════════════════════════════════════════════

def draw_ui(surface: pygame.Surface, font: pygame.font.Font,
            small_font: pygame.font.Font,
            mode: str, env: TrafficEnvironment,
            epsilon: float, episode: int, q_size: int):
    """Render the info panel and per-direction counters."""

    phase = env.signal.get_phase()
    waiting = env.waiting_count()
    avg_wait = env.average_wait()

    # ── main panel (top-left) ────────────────────────────────────────
    panel_w, panel_h = 270, 235
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((*COLOR_PANEL_BG, 220))
    # border
    pygame.draw.rect(panel, (60, 65, 80), (0, 0, panel_w, panel_h),
                     width=1, border_radius=10)
    surface.blit(panel, (12, 12))

    # Title bar
    mode_label = "🤖  RL Agent" if mode == "rl" else "⏱  Fixed Timer"
    mode_color = COLOR_GREEN if mode == "rl" else (250, 200, 50)
    title = font.render(mode_label, True, mode_color)
    surface.blit(title, (24, 20))
    pygame.draw.line(surface, (60, 65, 80), (22, 46), (270, 46), 1)

    state = env.signal.get_state()
    if state == 0:
        sig_str, sig_col = "↕ N/S Green", COLOR_GREEN
    elif state == 1:
        sig_str, sig_col = "↕ N/S Yellow", (250, 200, 50)
    elif state == 2:
        sig_str, sig_col = "↔ E/W Green", COLOR_GREEN
    else:
        sig_str, sig_col = "↔ E/W Yellow", (250, 200, 50)

    # Stats
    lines = [
        (f"Signal:  {sig_str}", sig_col),
        (f"Total Waiting:  {waiting}", COLOR_TEXT),
        (f"Avg Wait:  {avg_wait:.1f}s", COLOR_TEXT),
        (f"Cars Served:  {env.total_cars_served}", COLOR_TEXT),
        (f"Episode:  {episode}", COLOR_TEXT),
    ]
    if mode == "rl":
        lines.append((f"Epsilon:  {epsilon:.4f}", COLOR_TEXT_DIM))
        lines.append((f"Q-table:  {q_size} states", COLOR_TEXT_DIM))

    y = 54
    for text, color in lines:
        surf = small_font.render(text, True, color)
        surface.blit(surf, (24, y))
        y += 24

    # ── per-direction lane counters ──────────────────────────────────
    badge_font = pygame.font.SysFont("arial", 12, bold=True)
    label_font = pygame.font.SysFont("arial", 11)
    greens = env.signal.green_directions()
    per_dir_total   = env.cars_per_direction()
    per_dir_waiting = env.waiting_per_direction()

    # Badge is placed on the road APPROACHING the intersection:
    #   NORTH cars come from bottom → badge above intersection on right lane
    #   SOUTH cars come from top   → badge below intersection on left lane
    #   EAST  cars come from left  → badge right of intersection on bottom lane
    #   WEST  cars come from right → badge left of intersection on top lane
    badge_cfg = {
        NORTH: (CENTER_X + LANE_WIDTH // 2, INT_TOP - 60, "N"),
        SOUTH: (CENTER_X - LANE_WIDTH // 2, INT_BOTTOM + 30, "S"),
        EAST:  (INT_RIGHT + 22, CENTER_Y + LANE_WIDTH // 2, "E"),
        WEST:  (INT_LEFT - 62, CENTER_Y - LANE_WIDTH // 2, "W"),
    }

    for d, (bx, by, dlabel) in badge_cfg.items():
        total   = per_dir_total[d]
        waiting = per_dir_waiting[d]
        is_green = d in greens

        # Outer badge box  (width=60, height=40)
        badge_w, badge_h = 60, 42
        badge_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        bg = (30, 110, 55, 210) if is_green else (130, 35, 30, 210)
        pygame.draw.rect(badge_surf, bg, (0, 0, badge_w, badge_h), border_radius=8)
        pygame.draw.rect(badge_surf, (255, 255, 255, 60),
                         (0, 0, badge_w, badge_h), width=1, border_radius=8)

        # Direction label top-left
        lbl = label_font.render(dlabel, True, (255, 255, 255, 180))
        badge_surf.blit(lbl, (5, 3))

        # Big count in center
        count_txt = badge_font.render(str(total), True, (255, 255, 255))
        badge_surf.blit(count_txt, (badge_w // 2 - count_txt.get_width() // 2, 8))

        # "W:X" waiting sub-label
        wait_txt = label_font.render(f"wait:{waiting}", True, (220, 220, 180))
        badge_surf.blit(wait_txt, (badge_w // 2 - wait_txt.get_width() // 2, 27))

        surface.blit(badge_surf, (bx - badge_w // 2, by))


    # ── controls hint (bottom centre) ────────────────────────────────
    hint_font = pygame.font.SysFont("consolas", 13)
    hints = "SPACE: Toggle Mode    R: Reset    ESC: Quit"
    ht = hint_font.render(hints, True, COLOR_TEXT_DIM)
    # Background bar
    bar = pygame.Surface((ht.get_width() + 30, 26), pygame.SRCALPHA)
    bar.fill((*COLOR_PANEL_BG, 180))
    surface.blit(bar, (WIDTH // 2 - bar.get_width() // 2, HEIGHT - 34))
    surface.blit(ht, (WIDTH // 2 - ht.get_width() // 2, HEIGHT - 30))


# ═══════════════════════════════════════════════════════════════════════
#  Metrics plotting
# ═══════════════════════════════════════════════════════════════════════

def plot_metrics(rl_history: list, fixed_history: list):
    """Show a matplotlib graph comparing RL vs Fixed average waiting cars."""
    matplotlib.use("TkAgg")    # switch back for interactive display
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#1a1b23")
    ax.set_facecolor("#22232b")

    if rl_history:
        ax.plot(rl_history, label="RL Agent", color="#2ecc71", linewidth=2.5)
    if fixed_history:
        ax.plot(fixed_history, label="Fixed Timer", color="#e74c3c",
                linewidth=2.5, linestyle="--")

    ax.set_xlabel("Episode", color="white", fontsize=12)
    ax.set_ylabel("Avg Waiting Cars", color="white", fontsize=12)
    ax.set_title("RL vs Fixed Timer — Performance Comparison",
                 color="white", fontsize=14, pad=15)
    ax.legend(fontsize=11, facecolor="#2d2e3a", edgecolor="#444",
              labelcolor="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_color("#444")
    ax.grid(True, alpha=0.15, color="white")

    plt.tight_layout()
    plt.savefig("performance_comparison.png", dpi=150, facecolor="#1a1b23")
    plt.show()


# ═══════════════════════════════════════════════════════════════════════
#  Main loop
# ═══════════════════════════════════════════════════════════════════════

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🚦 RL Traffic Signal Optimization")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 17, bold=True)
    small_font = pygame.font.SysFont("arial", 15)

    env = TrafficEnvironment()
    agent = QLearningAgent()
    fixed_ctrl = FixedTimerController()

    mode = "rl"
    frame_counter = 0
    episode = 1
    episode_frames = 0
    episode_wait_sum = 0

    rl_episode_history: list[float] = []
    fixed_episode_history: list[float] = []

    prev_state = env.get_state()
    prev_action = agent.choose_action(prev_state)

    EPISODE_LENGTH = DECISION_INTERVAL * 20   # ~100 s per episode

    running = True
    while running:
        # ── events ───────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    mode = "fixed" if mode == "rl" else "rl"
                    fixed_ctrl.reset()
                elif event.key == pygame.K_r:
                    env.reset()
                    frame_counter = 0
                    episode_frames = 0
                    episode_wait_sum = 0

        # ── spawn ────────────────────────────────────────────────────
        env.spawn_cars()

        # ── decision step ────────────────────────────────────────────
        if mode == "rl":
            if frame_counter % DECISION_INTERVAL == 0:
                state_rep = env.get_state()
                action = agent.choose_action(state_rep)
                reward = env.step(action)
                next_state_rep = env.get_state()
                agent.update(prev_state, prev_action, reward, next_state_rep)
                agent.decay_epsilon()
                prev_state = state_rep
                prev_action = action
            else:
                env.tick_cars()
        else:
            fixed_ctrl.tick(env.signal)
            env.tick_cars()

        # ── episode tracking ─────────────────────────────────────────
        waiting = env.waiting_count()
        episode_wait_sum += waiting
        episode_frames += 1

        if episode_frames >= EPISODE_LENGTH:
            avg = episode_wait_sum / max(episode_frames, 1)
            if mode == "rl":
                rl_episode_history.append(avg)
            else:
                fixed_episode_history.append(avg)
            episode += 1
            episode_frames = 0
            episode_wait_sum = 0
            env.reset()
            prev_state = env.get_state()
            prev_action = agent.choose_action(prev_state)
            fixed_ctrl.reset()

        frame_counter += 1

        # ── draw ─────────────────────────────────────────────────────
        screen.fill(COLOR_BG)
        draw_roads(screen)
        env.signal.draw(screen)
        for car in env.cars:
            car.draw(screen)
        draw_ui(screen, font, small_font, mode, env,
                agent.epsilon, episode, agent.q_table_size())

        pygame.display.flip()
        clock.tick(FPS)

    # ── on exit: show plot ───────────────────────────────────────────
    pygame.quit()
    if rl_episode_history or fixed_episode_history:
        plot_metrics(rl_episode_history, fixed_episode_history)
    sys.exit()


if __name__ == "__main__":
    main()
