"""Main entry point — dual-junction Pygame simulation with persistent RL agents."""

import sys
import pygame
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from utils import (
    WIDTH, HEIGHT, FPS,
    CENTER_Y, HALF_ROAD, ROAD_WIDTH, LANE_WIDTH,
    INTERSECTIONS, DECISION_INTERVAL, SWITCH_PENALTY,
    COLOR_BG, COLOR_ROAD, COLOR_ROAD_EDGE, COLOR_LANE_MARK,
    COLOR_CROSSWALK, COLOR_INTERSECTION,
    COLOR_TEXT, COLOR_TEXT_DIM, COLOR_PANEL_BG,
    COLOR_GREEN, COLOR_YELLOW,
    NORTH, SOUTH, EAST, WEST,
)
from environment import TrafficEnvironment
from agent import QLearningAgent
from traffic_signal import FixedTimerController


# ═══════════════════════════════════════════════════════════════════════
#  Road drawing
# ═══════════════════════════════════════════════════════════════════════

def draw_roads(surface):
    """Draw horizontal road, two vertical roads, intersections, and markings."""

    # Horizontal road (full width)
    pygame.draw.rect(surface, COLOR_ROAD,
                     pygame.Rect(0, CENTER_Y - HALF_ROAD, WIDTH, ROAD_WIDTH))

    # Vertical roads
    for inter in INTERSECTIONS:
        pygame.draw.rect(surface, COLOR_ROAD,
                         pygame.Rect(inter.left, 0, ROAD_WIDTH, HEIGHT))

    # Intersection fills
    for inter in INTERSECTIONS:
        pygame.draw.rect(surface, COLOR_INTERSECTION,
                         pygame.Rect(inter.left, inter.top, ROAD_WIDTH, ROAD_WIDTH))

    # Vertical road edges (skip intersection zone)
    for inter in INTERSECTIONS:
        for x_off in (inter.left, inter.right):
            for y0, y1 in [(0, inter.top), (inter.bottom, HEIGHT)]:
                pygame.draw.line(surface, COLOR_ROAD_EDGE,
                                 (x_off, y0), (x_off, y1), 2)

    # Horizontal road edges (skip intersection zones)
    for y_off in (CENTER_Y - HALF_ROAD, CENTER_Y + HALF_ROAD):
        segs = [(0, INTERSECTIONS[0].left)]
        for i in range(len(INTERSECTIONS) - 1):
            segs.append((INTERSECTIONS[i].right, INTERSECTIONS[i + 1].left))
        segs.append((INTERSECTIONS[-1].right, WIDTH))
        for x0, x1 in segs:
            pygame.draw.line(surface, COLOR_ROAD_EDGE,
                             (x0, y_off), (x1, y_off), 2)

    # Dashed centre lines — vertical roads
    dash, gap = 18, 14
    for inter in INTERSECTIONS:
        y = 0
        while y < HEIGHT:
            if not (inter.top - 5 <= y <= inter.bottom + 5):
                pygame.draw.line(surface, COLOR_LANE_MARK,
                                 (inter.cx, y), (inter.cx, min(y + dash, HEIGHT)), 2)
            y += dash + gap

    # Dashed centre line — horizontal road
    x = 0
    while x < WIDTH:
        skip = False
        for inter in INTERSECTIONS:
            if inter.left - 5 <= x <= inter.right + 5:
                skip = True
                break
        if not skip:
            pygame.draw.line(surface, COLOR_LANE_MARK,
                             (x, CENTER_Y), (min(x + dash, WIDTH), CENTER_Y), 2)
        x += dash + gap

    # Crosswalks
    cw_w, cw_gap = 6, 6
    for inter in INTERSECTIONS:
        for cy in (inter.top + 8, inter.bottom - 11):
            xs = inter.left + 4
            while xs < inter.right - 4:
                pygame.draw.rect(surface, COLOR_CROSSWALK, (xs, cy, cw_w, 3))
                xs += cw_w + cw_gap
        for cx in (inter.left + 8, inter.right - 11):
            ys = inter.top + 4
            while ys < inter.bottom - 4:
                pygame.draw.rect(surface, COLOR_CROSSWALK, (cx, ys, 3, cw_w))
                ys += cw_w + cw_gap

    # Junction labels
    lbl_font = pygame.font.SysFont("arial", 14, bold=True)
    for i, inter in enumerate(INTERSECTIONS):
        lbl = lbl_font.render(f"Junction {i + 1}", True, COLOR_TEXT_DIM)
        surface.blit(lbl, (inter.cx - lbl.get_width() // 2, inter.top - 24))


# ═══════════════════════════════════════════════════════════════════════
#  UI overlay
# ═══════════════════════════════════════════════════════════════════════

def draw_ui(surface, font, small_font, mode, env, agents, episode):
    """Info panel, per-junction badges, and controls hint."""

    waiting = env.waiting_count()
    avg_wait = env.average_wait()

    # ── main panel (top-left) ────────────────────────────────────────
    panel_w, panel_h = 280, 210
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((*COLOR_PANEL_BG, 220))
    pygame.draw.rect(panel, (60, 65, 80), (0, 0, panel_w, panel_h),
                     width=1, border_radius=10)
    surface.blit(panel, (12, 12))

    mode_label = "RL Agent" if mode == "rl" else "Fixed Timer"
    mode_color = COLOR_GREEN if mode == "rl" else COLOR_YELLOW
    title = font.render(mode_label, True, mode_color)
    surface.blit(title, (24, 20))
    pygame.draw.line(surface, (60, 65, 80), (22, 44), (280, 44), 1)

    lines = [
        (f"Total Waiting:  {waiting}", COLOR_TEXT),
        (f"Avg Wait:  {avg_wait:.1f}s", COLOR_TEXT),
        (f"Cars on Road:  {len(env.cars)}", COLOR_TEXT),
        (f"Cars Served:  {env.total_cars_served}", COLOR_TEXT),
        (f"Episode:  {episode}", COLOR_TEXT),
    ]
    if mode == "rl":
        a0 = agents[0]
        lines.append((f"Epsilon:  {a0.epsilon:.4f}", COLOR_TEXT_DIM))
        total_q = sum(a.q_table_size() for a in agents)
        lines.append((f"Q-entries:  {total_q}", COLOR_TEXT_DIM))
        lines.append((f"Memory:  Persistent", (80, 200, 120)))

    y = 50
    for text, color in lines:
        surf = small_font.render(text, True, color)
        surface.blit(surf, (24, y))
        y += 20

    # ── per-junction info boxes ──────────────────────────────────────
    lbl_font = pygame.font.SysFont("arial", 12, bold=True)
    sub_font = pygame.font.SysFont("arial", 11)

    for inter in INTERSECTIONS:
        sig = env.signals[inter.idx]
        st = sig.get_state()
        if st == 0:
            sig_str, sig_col = "N/S Green", COLOR_GREEN
        elif st == 1:
            sig_str, sig_col = "N/S Yellow", COLOR_YELLOW
        elif st == 2:
            sig_str, sig_col = "E/W Green", COLOR_GREEN
        else:
            sig_str, sig_col = "E/W Yellow", COLOR_YELLOW

        w_count = env.waiting_at(inter.idx)
        t_count = env.cars_at(inter.idx)

        box_w, box_h = 120, 58
        bx = inter.cx - box_w // 2
        by = inter.bottom + 70

        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((*COLOR_PANEL_BG, 210))
        pygame.draw.rect(box, (60, 65, 80), (0, 0, box_w, box_h),
                         width=1, border_radius=8)

        t1 = lbl_font.render(f"J{inter.idx + 1}: {sig_str}", True, sig_col)
        box.blit(t1, (box_w // 2 - t1.get_width() // 2, 4))

        t2 = sub_font.render(f"Cars: {t_count}  Wait: {w_count}", True, COLOR_TEXT)
        box.blit(t2, (box_w // 2 - t2.get_width() // 2, 22))

        if mode == "rl":
            agent = agents[inter.idx]
            t3 = sub_font.render(f"Q: {agent.q_table_size()} entries", True, COLOR_TEXT_DIM)
            box.blit(t3, (box_w // 2 - t3.get_width() // 2, 38))

        surface.blit(box, (bx, by))

    # ── controls hint ────────────────────────────────────────────────
    hint_font = pygame.font.SysFont("consolas", 13)
    hints = "SPACE: Toggle Mode    R: Reset    ESC: Quit & Save"
    ht = hint_font.render(hints, True, COLOR_TEXT_DIM)
    bar = pygame.Surface((ht.get_width() + 30, 26), pygame.SRCALPHA)
    bar.fill((*COLOR_PANEL_BG, 180))
    surface.blit(bar, (WIDTH // 2 - bar.get_width() // 2, HEIGHT - 34))
    surface.blit(ht, (WIDTH // 2 - ht.get_width() // 2, HEIGHT - 30))


# ═══════════════════════════════════════════════════════════════════════
#  Metrics plotting
# ═══════════════════════════════════════════════════════════════════════

def plot_metrics(rl_history, fixed_history):
    matplotlib.use("TkAgg")
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.patch.set_facecolor("#1a1b23")
    ax.set_facecolor("#22232b")

    if rl_history:
        ax.plot(rl_history, label="RL Agent", color="#2ecc71", linewidth=2.5)
    if fixed_history:
        ax.plot(fixed_history, label="Fixed Timer", color="#e74c3c",
                linewidth=2.5, linestyle="--")

    ax.set_xlabel("Episode", color="white", fontsize=12)
    ax.set_ylabel("Avg Waiting Cars", color="white", fontsize=12)
    ax.set_title("RL vs Fixed Timer — Dual Junction Performance",
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
    pygame.display.set_caption("RL Traffic Signal Optimization — Dual Junction")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 17, bold=True)
    small_font = pygame.font.SysFont("arial", 14)

    env = TrafficEnvironment()

    # One persistent agent per intersection
    agents = []
    for inter in INTERSECTIONS:
        agent = QLearningAgent(save_name=f"q_table_junction_{inter.idx}")
        loaded = agent.load()
        if loaded:
            print(f"[Junction {inter.idx + 1}] Loaded Q-table "
                  f"({agent.q_table_size()} entries, eps={agent.epsilon:.4f})")
        else:
            print(f"[Junction {inter.idx + 1}] No saved Q-table — starting fresh")
        agents.append(agent)

    fixed_ctrls = [FixedTimerController() for _ in INTERSECTIONS]

    mode = "rl"
    frame_counter = 0
    episode = 1
    episode_frames = 0
    episode_wait_sum = 0

    rl_episode_history: list[float] = []
    fixed_episode_history: list[float] = []

    prev_states = {
        inter.idx: env.get_state(inter.idx) for inter in INTERSECTIONS
    }
    prev_actions = {
        inter.idx: agents[inter.idx].choose_action(prev_states[inter.idx])
        for inter in INTERSECTIONS
    }

    EPISODE_LENGTH = DECISION_INTERVAL * 20

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
                    for ctrl in fixed_ctrls:
                        ctrl.reset()
                elif event.key == pygame.K_r:
                    env.reset()
                    frame_counter = 0
                    episode_frames = 0
                    episode_wait_sum = 0

        # ── spawn ────────────────────────────────────────────────────
        env.spawn_cars()

        # ── decision / tick ──────────────────────────────────────────
        if mode == "rl":
            if frame_counter % DECISION_INTERVAL == 0:
                # 1) All agents pick actions and set signals
                cur_states = {}
                cur_actions = {}
                for inter in INTERSECTIONS:
                    idx = inter.idx
                    state = env.get_state(idx)
                    action = agents[idx].choose_action(state)
                    env.step(idx, action)
                    cur_states[idx] = state
                    cur_actions[idx] = action

                # 2) Tick cars once
                env.tick_cars()

                # 3) Observe next state, compute reward, update Q-tables
                for inter in INTERSECTIONS:
                    idx = inter.idx
                    next_state = env.get_state(idx)
                    reward = -env.waiting_at(idx)
                    if cur_actions[idx] != prev_actions[idx]:
                        reward -= SWITCH_PENALTY
                    agents[idx].update(
                        prev_states[idx], prev_actions[idx], reward, next_state
                    )
                    agents[idx].decay_epsilon()
                    prev_states[idx] = cur_states[idx]
                    prev_actions[idx] = cur_actions[idx]
            else:
                env.tick_cars()
        else:
            for i, inter in enumerate(INTERSECTIONS):
                fixed_ctrls[i].tick(env.signals[inter.idx])
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
            prev_states = {
                inter.idx: env.get_state(inter.idx) for inter in INTERSECTIONS
            }
            prev_actions = {
                inter.idx: agents[inter.idx].choose_action(prev_states[inter.idx])
                for inter in INTERSECTIONS
            }
            for ctrl in fixed_ctrls:
                ctrl.reset()

            # Save Q-tables at each episode end
            if mode == "rl":
                for agent in agents:
                    agent.save()

        frame_counter += 1

        # ── draw ─────────────────────────────────────────────────────
        screen.fill(COLOR_BG)
        draw_roads(screen)
        for inter in INTERSECTIONS:
            env.signals[inter.idx].draw(screen, inter.cx, inter.cy)
        for car in env.cars:
            car.draw(screen)
        draw_ui(screen, font, small_font, mode, env, agents, episode)

        pygame.display.flip()
        clock.tick(FPS)

    # ── on exit: save Q-tables and show plot ─────────────────────────
    for agent in agents:
        agent.save()
    print("Q-tables saved to disk.")

    pygame.quit()
    if rl_episode_history or fixed_episode_history:
        plot_metrics(rl_episode_history, fixed_episode_history)
    sys.exit()


if __name__ == "__main__":
    main()
