<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Pygame-2.x-00979D?style=for-the-badge&logo=python&logoColor=white" alt="Pygame"/>
  <img src="https://img.shields.io/badge/Reinforcement_Learning-Q--Learning-FF6F00?style=for-the-badge" alt="RL"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

# 🚦 Smart Traffic Signal Optimization System

> **A dual-junction intelligent traffic signal system powered by Q-Learning Reinforcement Learning with persistent memory, featuring real-time Pygame simulation that demonstrates how RL agents outperform traditional fixed-timer signals.**

---

## 📖 Table of Contents

- [Overview](#-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [How It Works](#-how-it-works)
- [Installation](#-installation)
- [Usage](#-usage)
- [Controls](#-controls)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Performance Results](#-performance-results)
- [Technologies Used](#-technologies-used)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

Urban traffic congestion is a growing global challenge. Traditional fixed-timer traffic signals operate on static cycles regardless of actual traffic conditions, leading to unnecessary delays and increased emissions.

This project implements a **multi-agent Q-Learning system** where **two independent RL agents** each control a traffic signal at a connected dual-junction intersection. The agents observe waiting vehicles in each direction and learn optimal signal-switching policies that minimize overall wait times.

**Persistent memory** ensures that trained Q-tables are saved to disk — each subsequent run starts from the previously learned policy, enabling continuous improvement across sessions.

A **real-time Pygame simulation** (1400×800) provides visual feedback, and a **fixed-timer baseline** is included for direct A/B performance comparison.

---

## ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🤖 Dual RL Agents** | Independent Q-learning agent per junction with ε-greedy exploration and online training |
| **💾 Persistent Memory** | Q-tables saved to disk (`.pkl`) — agents remember and improve across runs |
| **🔗 Connected Junctions** | Two intersections linked by a shared horizontal road; E/W cars cross both junctions |
| **🟢🟡🔴 Yellow Clearance** | Full Green → Yellow → Red transition cycle prevents intersection collisions |
| **🚗 Lane-Aware Car-Following** | Cars grouped by lane key; maintains safe following distance within each lane |
| **🚘 Multi-Intersection Traversal** | E/W cars sequentially check signals at each junction they encounter |
| **📊 Live Dashboard** | Real-time mode, waiting count, avg wait, cars served, epsilon, Q-table size |
| **🏷 Per-Junction Panels** | Signal state, car count, and Q-table info displayed below each intersection |
| **📈 Performance Plotting** | Matplotlib chart comparing RL vs Fixed-timer generated on exit |
| **⏱ Fixed-Timer Baseline** | Traditional controller for real-time A/B comparison (toggle with SPACE) |
| **🎨 Premium Dark Theme** | Dashed lane markings, crosswalks, car shadows, windshields, glowing signals |

---

## 🏗 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        main.py                               │
│  Pygame loop · Road rendering · UI overlay · Episode mgmt    │
└────────────┬──────────────────────────────────┬──────────────┘
             │                                  │
             ▼                                  ▼
┌─────────────────────┐              ┌──────────────────────┐
│   environment.py    │              │     agent.py (×2)    │
│  Dual-junction env  │◄────────────▶│  Q-Learning + disk   │
│  Car spawning/tick  │              │  save/load (pickle)  │
│  Per-junction state │              └──────────────────────┘
└──────┬──────────────┘
       │
       ▼
┌──────────────┐    ┌───────────────────┐    ┌──────────────┐
│   car.py     │    │ traffic_signal.py │    │  utils.py    │
│ Multi-int'n  │    │ G→Y→R phases      │    │ Constants,   │
│ stop logic,  │    │ FixedTimer ctrl   │    │ Geometry,    │
│ car-following│    │ Signal rendering  │    │ Routes       │
└──────────────┘    └───────────────────┘    └──────────────┘
```

### Dual Junction Layout

```
                 ▲ N                              ▲ N
                 │                                │
    ┌────────────┼────────────┐      ┌────────────┼────────────┐
    │            │            │      │            │            │
W ──┤  Junction  │     1      ├──────┤  Junction  │     2      ├── E
◄───┤            │            │      │            │            ├──►
    │            │            │      │            │            │
    └────────────┼────────────┘      └────────────┼────────────┘
                 │                                │
                 ▼ S                              ▼ S
```

- **Horizontal road** spans the full 1400px width
- **Vertical roads** at x=400 and x=1000 (one per junction)
- **E/W cars** travel the entire width, crossing **both** junctions
- **N/S cars** are local to their respective junction

---

## 🧠 How It Works

### Multi-Agent Q-Learning

Each junction has its own **independent Q-learning agent**:

**State** (per junction): `(N_waiting, S_waiting, E_waiting, W_waiting)` — 4-tuple of discretized counts (capped at 5), yielding 6⁴ = 1,296 possible states per agent.

**Actions**: `0` = N/S Green, `1` = E/W Green

**Reward**: `R = −(waiting cars at this junction) − penalty × (signal switched)`

### Persistent Memory

```
Run 1: Agent learns from scratch → saves Q-table to q_table_junction_0.pkl
Run 2: Loads Q-table → continues learning from where it left off
Run 3: Loads again → agent is now well-trained, near-optimal policy
```

Q-tables and epsilon values are automatically:
- **Loaded** on startup (if files exist)
- **Saved** at every episode boundary and on exit

### Yellow Clearance Phase

When an agent switches the signal direction:
1. Current direction goes **Yellow** (1.5s / 45 frames)
2. All directions see **Red** — no one gets green
3. Cars already in the intersection clear safely
4. New direction goes **Green**

### Car-Following & Multi-Intersection Logic

- Cars are grouped by **lane key** (e.g., `"N0"`, `"E"`, `"W"`)
- Each car maintains safe following distance to the car directly ahead in its lane
- **E/W cars** have an ordered list of intersections to cross; they check signals at each one sequentially
- Once a car's front passes the stop line on green, it **commits** (`inside_current = True`) and won't stop even if the light turns red

---

## 🚀 Installation

### Prerequisites
- **Python 3.9+**

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/jayashish05/Smart-Traffic-Signal-Optimization-System.git
cd Smart-Traffic-Signal-Optimization-System

# 2. (Optional) Create a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install pygame numpy matplotlib
```

---

## 🎮 Usage

```bash
python3 main.py
```

The simulation window (1400×800) opens immediately. The RL agents begin training from frame 1 — or resume from saved Q-tables if previous training data exists.

### First Run
```
[Junction 1] No saved Q-table — starting fresh
[Junction 2] No saved Q-table — starting fresh
```

### Subsequent Runs
```
[Junction 1] Loaded Q-table (847 entries, eps=0.0500)
[Junction 2] Loaded Q-table (912 entries, eps=0.0500)
```

---

## ⌨ Controls

| Key | Action |
|-----|--------|
| `SPACE` | Toggle between **RL Agent** and **Fixed Timer** modes |
| `R` | **Reset** the simulation (clears all cars, resets episode) |
| `ESC` | **Quit** — saves Q-tables and shows performance chart |

---

## 📁 Project Structure

```
Smart-Traffic-Signal-Optimization-System/
│
├── main.py              # Entry point: Pygame loop, dual-road rendering, UI
├── environment.py       # RL environment: two junctions, spawning, yellow logic
├── agent.py             # Q-learning agent with pickle save/load persistence
├── car.py               # Vehicle: multi-intersection stop logic, car-following
├── traffic_signal.py    # Signal: 4-state phase machine, fixed-timer controller
├── utils.py             # Constants, IntersectionConfig, routes, colors
├── README.md            # This file
├── LICENSE              # MIT License
├── .gitignore           # Python/IDE/output ignores
└── assets/              # Screenshots & demo media
```

### Generated at Runtime (git-ignored)
```
├── q_table_junction_0.pkl     # Persisted Q-table for Junction 1
├── q_table_junction_1.pkl     # Persisted Q-table for Junction 2
└── performance_comparison.png # RL vs Fixed chart (on ESC)
```

---

## ⚙ Configuration

### Simulation (`utils.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `WIDTH × HEIGHT` | 1400 × 800 | Window size |
| `FPS` | 30 | Frame rate |
| `ROAD_WIDTH` | 120 | Road width (2 lanes, 60px each) |
| `CAR_SPEED` | 3 | Pixels per frame |
| `SPAWN_PROB` | 0.02 | Per-route spawn probability per frame |
| `DECISION_INTERVAL` | 150 | Frames between RL decisions (~5s) |
| `SWITCH_PENALTY` | 2 | Reward penalty for changing signal phase |

### Agent (`agent.py`)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `alpha` | 0.1 | Learning rate |
| `gamma` | 0.95 | Discount factor |
| `epsilon` | 1.0 → 0.05 | Exploration rate (decays 0.9995×/step) |

### Junction Positions (`utils.py`)

| Junction | Center | Intersection Box |
|----------|--------|-----------------|
| Junction 1 | (400, 400) | [340, 340] – [460, 460] |
| Junction 2 | (1000, 400) | [940, 340] – [1060, 460] |

---

## 📈 Performance Results

Upon pressing **ESC**, the simulation saves Q-tables and generates `performance_comparison.png`:

- **RL agents** typically achieve **20–40% reduction** in average waiting cars vs fixed timer
- **Persistent memory** means performance improves across multiple runs
- **Cross-junction coordination** emerges naturally as E/W traffic patterns stabilize

---

## 🛠 Technologies Used

| Technology | Purpose |
|------------|---------|
| **Python 3** | Core language |
| **Pygame** | Real-time simulation and rendering |
| **NumPy** | Numerical support |
| **Matplotlib** | Performance visualization |
| **Pickle** | Q-table persistence |
| **Q-Learning** | Tabular RL for signal optimization |

---

## 🤝 Contributing

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. Open a **Pull Request**

### Ideas for Extension
- Deep Q-Network (DQN) for continuous state spaces
- Three or more connected intersections (corridor)
- Coordinated "green wave" between junctions
- Turn lanes and pedestrian crossings
- Emergency vehicle priority
- Real-world traffic data integration

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  <b>⭐ If you found this project useful, please give it a star! ⭐</b>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/jayashish05">Jayashish</a>
</p>
