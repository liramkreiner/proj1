# Tactical Penalty Shootout Simulator

### A mixed-strategy zero-sum game

A desktop-grade **web application** that models a football penalty shootout as a
finite two-player **zero-sum game** and solves it exactly. You can play against an
AI that samples from the game's **mixed-strategy Nash equilibrium**, inspect the
payoff matrix and the minimax solution, run Monte Carlo experiments that show
empirical play converging to the theory, and edit the payoff matrix to prove the
engine is fully generic.

The game-theory engine is the core of the project. The UI never does any
mathematics — it only calls the engine and renders the result.

---

## 1. Project overview

| Layer | Package | Responsibility |
|---|---|---|
| Mathematics | `game_theory/` | Pure/mixed strategy analysis, linear-programming solver, equilibrium validation |
| Domain | `game/` | Goal zones, payoff-matrix model, penalty resolution, Monte Carlo, match flow |
| Agents | `agents/` | `OptimalAgent` (samples the equilibrium), `HumanAgent` |
| Transport | `web/backend/` | FastAPI: turns JSON into engine calls, serves the built UI |
| Interface | `web/frontend/` | React SPA: Play, Game Theory, Simulation, Experiment, Explanation |

## 2. Game rules

* The goal mouth is divided into **6 zones**: Top/Bottom × Left/Centre/Right.
* Each penalty, the **shooter** picks a target zone and the **goalkeeper** picks a
  dive zone, **simultaneously** (imperfect information).
* Whether the shot is scored is a random event with probability
  $A[i,j] = P(\text{score}\mid \text{shot } i,\ \text{dive } j)$.
* A shootout is **5 penalties per side**; if level, **sudden death** continues one
  pair of penalties at a time until someone leads.

## 3. Mathematical model

The shooter is the **row / maximiser**, the goalkeeper the **column / minimiser**.
The shooter's payoff for a pure outcome is $A[i,j]$; the goalkeeper's payoff is
$-A[i,j]$. The payoffs sum to zero, so this is a **zero-sum game** and the whole
game is described by the single matrix $A$.

A **mixed strategy** is a probability distribution over zones: the shooter plays
$p=(p_1,\dots,p_6)$, the goalkeeper $q=(q_1,\dots,q_6)$ with

$$\sum_i p_i = 1,\quad p_i \ge 0,\qquad \sum_j q_j = 1,\quad q_j \ge 0.$$

The shooter's **expected payoff** (expected scoring probability) is

$$E(p,q) = p^\top A\, q = \sum_i \sum_j p_i\, A[i,j]\, q_j.$$

## 4. Payoff matrix

The default scoring-probability matrix (configurable in
`game/payoff_matrix.py`). Diagonal = keeper guesses the shot zone:

|          | Dive TL | Dive TC | Dive TR | Dive BL | Dive BC | Dive BR |
|----------|:------:|:------:|:------:|:------:|:------:|:------:|
| **Shot TL** | 0.30 | 0.85 | 0.90 | 0.80 | 0.85 | 0.90 |
| **Shot TC** | 0.85 | 0.35 | 0.85 | 0.90 | 0.80 | 0.90 |
| **Shot TR** | 0.90 | 0.85 | 0.30 | 0.80 | 0.85 | 0.90 |
| **Shot BL** | 0.75 | 0.85 | 0.80 | 0.30 | 0.85 | 0.80 |
| **Shot BC** | 0.85 | 0.75 | 0.85 | 0.85 | 0.40 | 0.85 |
| **Shot BR** | 0.80 | 0.85 | 0.75 | 0.80 | 0.85 | 0.30 |

`PayoffMatrix` rejects any entry outside $[0,1]$ and any non-2-D / empty input.

## 5. Pure-strategy analysis

For each shooter row we take the worst column (`row_minima`); for each
goalkeeper column we take the best row (`column_maxima`). Then

$$\text{maximin} = \max_i \min_j A[i,j], \qquad
  \text{minimax} = \min_j \max_i A[i,j].$$

If $\text{maximin} = \text{minimax}$ the game has a **pure-strategy saddle
point** and that cell is the solution. For the default matrix

$$\text{maximin} = 0.40 \neq 0.85 = \text{minimax},$$

so **no pure equilibrium exists** and randomisation is strictly better.

## 6. Minimax theorem

Von Neumann's theorem: for every finite zero-sum game

$$\max_{p}\ \min_{q}\ p^\top A\, q \;=\; \min_{q}\ \max_{p}\ p^\top A\, q \;=\; v.$$

The common value $v$ is the **value of the game**. For the default matrix
$v \approx 0.7515$: with optimal play the shooter scores about **75.2%** of
penalties, and neither side can do better against a competent opponent.

## 7. Nash equilibrium

Because the game is zero-sum, the minimax pair $(p^\*, q^\*)$ is a **Nash
equilibrium**: given $q^\*$ every zone in the shooter's support returns exactly
$v$, so unilateral deviation cannot help — and symmetrically for the keeper. The
Play-tab AI simply samples from $q^\*$ (or $p^\*$), which is why its next move
cannot be predicted from its past moves.

## 8. Linear-programming formulation

Fix the shooter's mix $p$. The keeper replies with the worst column, so
$\min_q p^\top A q = \min_j (p^\top A)_j$. The shooter therefore solves

$$
\begin{aligned}
\text{maximise } & v \\
\text{s.t. } & (p^\top A)_j \ge v \quad \forall j \\
             & \textstyle\sum_i p_i = 1,\quad p_i \ge 0.
\end{aligned}
$$

The goalkeeper solves the **dual**

$$
\begin{aligned}
\text{minimise } & w \\
\text{s.t. } & (A q)_i \le w \quad \forall i \\
             & \textstyle\sum_j q_j = 1,\quad q_j \ge 0.
\end{aligned}
$$

LP **strong duality** forces the two optimal objective values to coincide, and
that shared number is $v$ — this is exactly the minimax theorem. The
implementation (`game_theory/linear_programming.py`) builds both programs,
solves them with `scipy.optimize.linprog` (HiGHS), and **cross-checks** the two
values; `game_theory/nash_equilibrium.py` then verifies

$$p^\top A \ge v - \varepsilon, \qquad A q \le v + \varepsilon, \qquad
  p^\top A q \approx v.$$

The solver is general over any $m \times n$ matrix, not just $2\times2$ or square.

## 9. Software architecture

```
proj1/
├── main.py                 CLI: `python main.py demo` | `python main.py serve`
├── demo.py                 Phase 1 console demonstration (3 worked examples)
├── game/
│   ├── models.py           GoalZone enum, dataclasses (PayoffMatrix, EquilibriumResult, ...)
│   ├── config.py           geometry, tolerances, MatchRules — no magic numbers elsewhere
│   ├── payoff_matrix.py    PenaltyProbabilityModel -> PayoffMatrix
│   ├── penalty_engine.py   ProbabilitySampler, PenaltyShootoutEngine, match + sudden death
│   ├── simulation.py       run_penalty_monte_carlo (vectorised)
│   └── match_controller.py stateful single-match flow, re-solves for a custom matrix
├── game_theory/
│   ├── minimax.py          row_minima / column_maxima / maximin / minimax / saddle point
│   ├── linear_programming.py   row & column LPs (+ full minimax<->LP derivation in docstring)
│   ├── mixed_strategy.py   orchestrates both LPs, checks duality
│   └── nash_equilibrium.py solve + validate_equilibrium (detailed report)
├── agents/                 base / human / optimal (samples the equilibrium)
├── web/
│   ├── backend/app.py      FastAPI endpoints
│   ├── backend/schemas.py  Pydantic DTOs
│   └── frontend/           React + Vite SPA (5 tabs)
├── tests/                  pytest suite (60+ tests)
├── Dockerfile              multi-stage: node build -> python runtime, single container
└── docker-compose.yml
```

The mathematics has **no dependency** on FastAPI, React, or any UI code.

### API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | liveness |
| GET | `/api/config` | zone list, grid size, defaults |
| GET | `/api/equilibrium` | full analysis of the default matrix |
| POST | `/api/analyze` | Experiment mode: analyse a user-edited matrix |
| POST | `/api/simulate` | Monte Carlo run (theory vs empirical) |
| POST | `/api/penalty` | one shot, one save — the AI samples its side from the equilibrium |
| POST | `/api/sessions` `…/turn` `…/reset` | 5-round shootout with sudden death (engine kept for completeness) |

The web UI's **The duel** tab is a single-penalty duel (`/api/penalty`): pick a
corner, the keeper commits its side from the equilibrium mix at the same
instant, and you see the verdict. The full shootout logic still lives in
`game/penalty_engine.py` and the session endpoints.

## 10. Installation

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt                   # runtime + pytest + httpx
```

Front-end build tooling (Node 20+):

```bash
npm --prefix web/frontend install
```

## 11. Running the application

**Development** (two processes, hot reload):

```bash
python main.py serve --reload            # API on http://127.0.0.1:8000
npm --prefix web/frontend run dev        # UI on http://localhost:5173 (proxies /api)
```

**Production, single process:**

```bash
npm --prefix web/frontend run build      # -> web/frontend/dist
python main.py serve --host 0.0.0.0 --port 8000
# open http://localhost:8000
```

**Docker (single container, deploy-ready):**

```bash
docker build -t tactical-penalty-shootout .
docker run --rm -p 8000:8000 tactical-penalty-shootout
# or:  docker compose up --build
```

The image respects `$PORT`, so it runs unchanged on Cloud Run, Render, Railway,
or Fly.io. It runs as a non-root user and ships a `/api/health` HEALTHCHECK.

## 12. Running tests

```bash
pytest
```

Covers: payoff-matrix validation, maximin/minimax and saddle-point detection,
the LP layer, mixed-strategy solutions for **matching pennies**
($p=q=(\tfrac12,\tfrac12)$, $v=0$), a **non-uniform** $2\times2$ game
($p=(0.2,0.8)$, $q=(0.6,0.4)$, $v=2.4$), rock–paper–scissors, a game with a pure
saddle point, Monte Carlo convergence, the agents (the AI samples the whole
support, not the argmax), the match engine (goal / save / score tracking /
sudden death / completion) and every API endpoint.

## 13. Running simulations

Console:

```bash
python main.py demo          # prints the 3 worked examples with full validation
```

In the app, open **Simulation**, set the penalty count (presets up to 100 000),
optionally a seed, and **Run**. You get the theoretical value, the observed
scoring rate, the absolute error, and per-zone bar charts of theoretical vs
empirical frequencies with their $L^1$ error.

## 14. Example results

`python main.py demo` (abridged):

```
1. MATCHING PENNIES
   Maximin -1.000000   Minimax 1.000000   Saddle point: none
   Shooter p:  Heads 0.5000  Tails 0.5000
   Keeper  q:  Heads 0.5000  Tails 0.5000
   Game value v = 0.000000                      Equilibrium VALID

2. NON-UNIFORM 2x2  [[4,0],[2,3]]
   Shooter p = (0.2000, 0.8000)   Keeper q = (0.6000, 0.4000)
   Game value v = 2.400000                      Equilibrium VALID

3. PENALTY SHOOTOUT (6x6)
   Maximin 0.400000   Minimax 0.850000   Saddle point: none
   Shooter p ≈ (0.146, 0.157, 0.141, 0.148, 0.201, 0.206)
   Keeper  q ≈ (0.197, 0.203, 0.197, 0.115, 0.174, 0.115)
   Game value v = 0.751529                      Equilibrium VALID
```

Monte Carlo, 200 000 penalties at equilibrium: observed scoring rate within
~$5\times10^{-3}$ of $v$, and empirical zone frequencies within ~$10^{-2}$ of
$p$ and $q$ — the AI *is* the equilibrium distribution, seen in aggregate.

---

### Note on the technology stack

The original brief specified a PyQt6 desktop app with Matplotlib charts. This
build is **web-only** by request: PyQt6/Streamlit are removed, and the charts
are rendered client-side (SVG) so the whole thing ships as one Docker image with
no display server. The mathematical core, the architecture boundaries, and every
Phase-1–7 requirement are unchanged.
