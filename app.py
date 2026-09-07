import json

import numpy as np
import streamlit as st
from solver import PROFILES, apply_risk, get_profile, solve_nash

ACTIONS = ["Left", "Center", "Right"]
PROFILE_NAMES = [p["name"] for p in PROFILES]


def _init_session_state():
    if "profile_name" not in st.session_state:
        st.session_state.profile_name = PROFILE_NAMES[0]
    if "matrix" not in st.session_state:
        st.session_state.matrix = get_profile(PROFILE_NAMES[0])
    if "risk" not in st.session_state:
        st.session_state.risk = 0.0
    if "role" not in st.session_state:
        st.session_state.role = "Kicker"
    if "score" not in st.session_state:
        st.session_state.score = {"goals": 0, "kicks": 0}
    if "history" not in st.session_state:
        st.session_state.history = []


def _sidebar():
    st.sidebar.header("Settings")

    selected = st.sidebar.selectbox(
        "Player Profile",
        PROFILE_NAMES,
        index=PROFILE_NAMES.index(st.session_state.profile_name),
    )
    if selected != st.session_state.profile_name:
        st.session_state.profile_name = selected
        st.session_state.matrix = get_profile(selected)

    st.session_state.risk = st.sidebar.slider(
        "Top Corner Risk (miss chance)",
        min_value=0.0,
        max_value=0.5,
        value=float(st.session_state.risk),
        step=0.01,
        format="%.2f",
        help="Probability the ball misses entirely when aiming for top corners. Applied uniformly to all cells.",
    )

    if st.sidebar.button("Reset to Profile Defaults"):
        st.session_state.matrix = get_profile(st.session_state.profile_name)
        st.rerun()


def _display_matrix(m: np.ndarray):
    cols = st.columns(4)
    cols[0].markdown("")
    for j, a in enumerate(ACTIONS):
        cols[j + 1].markdown(f"**{a}**")
    for i, row_action in enumerate(ACTIONS):
        row_cols = st.columns(4)
        row_cols[0].markdown(f"**{row_action}**")
        for j in range(3):
            row_cols[j + 1].markdown(f"`{m[i, j]:.3f}`")


def _fmt_strategy(probs: np.ndarray) -> str:
    dominant = ACTIONS[int(np.argmax(probs))]
    return f"Favors {dominant}"


def _display_strategy_bar(probs: np.ndarray):
    cols = st.columns(3)
    for i, (col, action) in enumerate(zip(cols, ACTIONS)):
        col.progress(float(probs[i]), text=f"{action}: {probs[i]:.1%}")


def _analysis_tab():
    st.header("Payoff Matrix Editor")
    st.caption(
        "Kicker scoring probability for each (Kicker action, Goalie action) pair. "
        "Rows = Kicker direction, Columns = Goalie direction."
    )

    matrix = st.session_state.matrix.copy()

    header_cols = st.columns(4)
    header_cols[0].markdown("**Kicker \\ Goalie**")
    for j, a in enumerate(ACTIONS):
        header_cols[j + 1].markdown(f"**{a}**")

    for i, row_action in enumerate(ACTIONS):
        row_cols = st.columns(4)
        row_cols[0].markdown(f"**{row_action}**")
        for j in range(3):
            val = row_cols[j + 1].number_input(
                label=f"{row_action}/{ACTIONS[j]}",
                label_visibility="collapsed",
                min_value=0.0,
                max_value=1.0,
                value=float(matrix[i, j]),
                step=0.05,
                key=f"cell_{i}_{j}",
            )
            matrix[i, j] = val

    st.session_state.matrix = matrix

    effective = apply_risk(matrix, st.session_state.risk)

    if st.session_state.risk > 0:
        st.subheader("Effective Matrix (after risk modifier)")
        st.caption(f"Base matrix scaled by (1 - {st.session_state.risk:.2f})")
        _display_matrix(effective)
    else:
        effective = matrix

    st.subheader("Nash Equilibrium")

    nash = solve_nash(effective)

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Game Value",
        f"{nash['value']:.3f}",
        help="Expected scoring probability when both play optimally.",
    )
    col2.metric("Kicker Strategy", _fmt_strategy(nash["kicker"]))
    col3.metric("Goalie Strategy", _fmt_strategy(nash["goalie"]))

    st.markdown("**Kicker optimal mix (probability per action)**")
    _display_strategy_bar(nash["kicker"])

    st.markdown("**Goalie optimal mix (probability per action)**")
    _display_strategy_bar(nash["goalie"])

    with st.expander("What does this mean?"):
        st.markdown(
            f"""
The **Mixed Strategy Nash Equilibrium** is the pair of randomized strategies where neither
player can improve their expected outcome by changing strategy, given the other player's strategy.

- **Kicker** (row player) wants to *maximize* scoring probability.
- **Goalie** (column player) wants to *minimize* it.

At equilibrium, the kicker should go Left with probability **{nash['kicker'][0]:.1%}**,
Center with **{nash['kicker'][1]:.1%}**, and Right with **{nash['kicker'][2]:.1%}**.

The goalie mirrors this logic with their own optimal mix. The **game value** ({nash['value']:.3f})
is the guaranteed expected scoring rate the kicker achieves regardless of what the goalie does.

Solved via the **Minimax theorem** using linear programming (`scipy.optimize.linprog`, HiGHS solver).
"""
        )


def _build_game_html(config_json: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin: 0; background: #1a1a2e; font-family: 'Segoe UI', sans-serif; color: #eee; }}
  canvas {{ display: block; margin: 0 auto; cursor: pointer; }}
  #ui {{ text-align: center; padding: 8px 0 4px; }}
  #score {{ font-size: 1.1em; margin-bottom: 4px; }}
  #msg {{ font-size: 1.4em; font-weight: bold; min-height: 1.8em; color: #ffd700; }}
  #hint {{ font-size: 0.85em; color: #aaa; margin-top: 2px; }}
  #history {{ max-width: 500px; margin: 6px auto 0; font-size: 0.78em; color: #bbb; text-align: left; padding: 0 12px; }}
  #history div {{ border-bottom: 1px solid #333; padding: 2px 0; }}
</style>
</head>
<body>
<div id="ui">
  <div id="score">Goals: <b id="goals">0</b> / Kicks: <b id="kicks">0</b>
    &nbsp;|&nbsp; Nash value: <b id="nash_val"></b></div>
  <div id="msg">Choose a zone to kick!</div>
  <div id="hint"></div>
</div>
<canvas id="c" width="500" height="340"></canvas>
<div id="history"></div>
<script>
const CFG = {config_json};
const LABELS = ['Left','Center','Right'];

// ---- layout constants ----
const W = 500, H = 340;
const POST_X1 = 80, POST_X2 = 420, BAR_Y = 60, GROUND_Y = 280;
const ZONE_W = (POST_X2 - POST_X1) / 3;

// zone centres [x, y] for 3 columns x 2 rows (top/bottom)
function zoneCentre(col, row) {{
  const x = POST_X1 + ZONE_W * col + ZONE_W / 2;
  const y = row === 0 ? BAR_Y + (GROUND_Y - BAR_Y) * 0.28 : BAR_Y + (GROUND_Y - BAR_Y) * 0.72;
  return [x, y];
}}

// keeper body: head circle + body rect centred at (kx, ky)
function keeperCentre(col) {{
  const x = POST_X1 + ZONE_W * col + ZONE_W / 2;
  return [x, GROUND_Y - 55];
}}

// ---- state ----
let goals = 0, kicks = 0;
let phase = 'idle'; // idle | animating | result
let ballX, ballY, ballTX, ballTY;
let keepX, keepY, keepTX, keepTY;
let userCol, aiCol, isGoal, scorePct;
let animT = 0;
const ANIM_DUR = 38; // frames
let historyLog = [];
let hoveredZone = -1; // 0-5 (col*2+row) or -1

const canvas = document.getElementById('c');
const ctx = canvas.getContext('2d');

document.getElementById('nash_val').textContent =
  (CFG.nashValue * 100).toFixed(1) + '%';

// ---- weighted random ----
function weightedChoice(probs) {{
  let r = Math.random(), cum = 0;
  for (let i = 0; i < probs.length; i++) {{
    cum += probs[i];
    if (r <= cum) return i;
  }}
  return probs.length - 1;
}}

// ---- easing ----
function easeOut(t) {{ return 1 - Math.pow(1 - t, 3); }}

// ---- draw ----
function drawGrass() {{
  const grad = ctx.createLinearGradient(0, GROUND_Y, 0, H);
  grad.addColorStop(0, '#2d5a1b');
  grad.addColorStop(1, '#1a3a0f');
  ctx.fillStyle = grad;
  ctx.fillRect(0, GROUND_Y, W, H - GROUND_Y);
  // pitch lines
  ctx.strokeStyle = '#3a7a22';
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i++) {{
    ctx.beginPath();
    ctx.moveTo(0, GROUND_Y + (H - GROUND_Y) * i / 3);
    ctx.lineTo(W, GROUND_Y + (H - GROUND_Y) * i / 3);
    ctx.stroke();
  }}
}}

function drawSky() {{
  const grad = ctx.createLinearGradient(0, 0, 0, GROUND_Y);
  grad.addColorStop(0, '#0a0a1a');
  grad.addColorStop(1, '#1a1a3a');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, GROUND_Y);
}}

function drawGoal() {{
  ctx.strokeStyle = '#ffffff';
  ctx.lineWidth = 4;
  ctx.shadowColor = '#ffffff';
  ctx.shadowBlur = 8;
  // crossbar
  ctx.beginPath();
  ctx.moveTo(POST_X1, BAR_Y);
  ctx.lineTo(POST_X2, BAR_Y);
  ctx.stroke();
  // posts
  ctx.beginPath();
  ctx.moveTo(POST_X1, BAR_Y);
  ctx.lineTo(POST_X1, GROUND_Y);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(POST_X2, BAR_Y);
  ctx.lineTo(POST_X2, GROUND_Y);
  ctx.stroke();
  ctx.shadowBlur = 0;
  // net lines
  ctx.strokeStyle = 'rgba(255,255,255,0.15)';
  ctx.lineWidth = 1;
  for (let i = 1; i < 6; i++) {{
    const nx = POST_X1 + (POST_X2 - POST_X1) * i / 6;
    ctx.beginPath(); ctx.moveTo(nx, BAR_Y); ctx.lineTo(nx, GROUND_Y); ctx.stroke();
  }}
  for (let j = 1; j < 4; j++) {{
    const ny = BAR_Y + (GROUND_Y - BAR_Y) * j / 4;
    ctx.beginPath(); ctx.moveTo(POST_X1, ny); ctx.lineTo(POST_X2, ny); ctx.stroke();
  }}
}}

function drawZones(enabled) {{
  for (let col = 0; col < 3; col++) {{
    for (let row = 0; row < 2; row++) {{
      const zoneId = col * 2 + row;
      const x = POST_X1 + ZONE_W * col;
      const y = row === 0 ? BAR_Y : BAR_Y + (GROUND_Y - BAR_Y) / 2;
      const zh = (GROUND_Y - BAR_Y) / 2;
      const isHov = enabled && hoveredZone === zoneId;
      ctx.fillStyle = isHov ? 'rgba(255,215,0,0.22)' : 'rgba(255,255,255,0.04)';
      ctx.fillRect(x + 2, y + 2, ZONE_W - 4, zh - 4);
      if (isHov) {{
        ctx.strokeStyle = 'rgba(255,215,0,0.7)';
        ctx.lineWidth = 2;
        ctx.strokeRect(x + 2, y + 2, ZONE_W - 4, zh - 4);
      }}
    }}
  }}
  // zone labels (bottom row only, when idle)
  if (enabled) {{
    ctx.fillStyle = 'rgba(255,255,255,0.5)';
    ctx.font = '13px Segoe UI';
    ctx.textAlign = 'center';
    for (let col = 0; col < 3; col++) {{
      const cx = POST_X1 + ZONE_W * col + ZONE_W / 2;
      ctx.fillText(LABELS[col], cx, GROUND_Y - 8);
    }}
  }}
}}

function drawKeeper(x, y, diving, diveDir) {{
  // body
  ctx.fillStyle = '#e74c3c';
  ctx.fillRect(x - 14, y - 30, 28, 38);
  // head
  ctx.beginPath();
  ctx.arc(x, y - 38, 14, 0, Math.PI * 2);
  ctx.fillStyle = '#f5cba7';
  ctx.fill();
  // arms stretched when diving
  if (diving) {{
    const armLen = 32;
    const sign = diveDir < 0 ? -1 : 1;
    ctx.strokeStyle = '#e74c3c';
    ctx.lineWidth = 6;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(x, y - 20);
    ctx.lineTo(x + sign * armLen, y - 20 + 10);
    ctx.stroke();
  }} else {{
    // arms out to sides
    ctx.strokeStyle = '#e74c3c';
    ctx.lineWidth = 6;
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(x - 14, y - 20);
    ctx.lineTo(x - 38, y - 14);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(x + 14, y - 20);
    ctx.lineTo(x + 38, y - 14);
    ctx.stroke();
  }}
}}

function drawBall(x, y, scale) {{
  const r = Math.max(2, 10 * scale);
  ctx.beginPath();
  ctx.arc(x, y, r, 0, Math.PI * 2);
  ctx.fillStyle = '#ffffff';
  ctx.fill();
  ctx.strokeStyle = '#222';
  ctx.lineWidth = 1.5;
  ctx.stroke();
  // pentagon patches
  ctx.fillStyle = '#222';
  ctx.beginPath();
  ctx.arc(x, y, r * 0.35, 0, Math.PI * 2);
  ctx.fill();
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);
  drawSky();
  drawGrass();
  drawGoal();

  const isIdle = phase === 'idle';
  const isResult = phase === 'result';
  drawZones(isIdle);

  // keeper position
  let kx, ky, diving = false, diveDir = 0;
  if (phase === 'idle') {{
    [kx, ky] = keeperCentre(1); // centre
  }} else {{
    const t = easeOut(Math.min(animT / ANIM_DUR, 1));
    kx = keepX + (keepTX - keepX) * t;
    ky = keepY + (keepTY - keepY) * t;
    diving = (aiCol !== 1);
    diveDir = aiCol === 0 ? -1 : 1;
  }}
  drawKeeper(kx, ky, diving && phase !== 'idle', diveDir);

  // ball
  if (phase === 'idle') {{
    drawBall(W / 2, GROUND_Y + 18, 1.2);
  }} else {{
    const t = easeOut(Math.min(animT / ANIM_DUR, 1));
    const bx = ballX + (ballTX - ballX) * t;
    const by = ballY + (ballTY - ballY) * t;
    const scale = 1.2 - 0.5 * t; // shrinks as it goes away
    drawBall(bx, by, scale);
  }}

  // result flash overlay
  if (phase === 'result') {{
    const color = isGoal ? 'rgba(0,200,0,0.18)' : 'rgba(200,0,0,0.18)';
    ctx.fillStyle = color;
    ctx.fillRect(POST_X1, BAR_Y, POST_X2 - POST_X1, GROUND_Y - BAR_Y);
  }}
}}

// ---- animation loop ----
function tick() {{
  if (phase === 'animating') {{
    animT++;
    draw();
    if (animT >= ANIM_DUR) {{
      phase = 'result';
      showResult();
      draw();
    }} else {{
      requestAnimationFrame(tick);
    }}
  }}
}}

function showResult() {{
  const msg = document.getElementById('msg');
  const hint = document.getElementById('hint');
  const aiLabel = LABELS[aiCol];
  const userLabel = LABELS[userCol];
  if (CFG.role === 'Kicker') {{
    msg.textContent = isGoal ? '⚽ GOAL!' : '🧤 SAVED!';
    msg.style.color = isGoal ? '#00e676' : '#ff5252';
    hint.textContent = `You kicked ${{userLabel}} | Keeper dived ${{aiLabel}} | prob ${{(scorePct*100).toFixed(0)}}%`;
  }} else {{
    msg.textContent = isGoal ? '⚽ Goal conceded' : '🧤 SAVED!';
    msg.style.color = isGoal ? '#ff5252' : '#00e676';
    hint.textContent = `You dived ${{userLabel}} | AI kicked ${{aiLabel}} | prob ${{(scorePct*100).toFixed(0)}}%`;
  }}

  goals += isGoal ? 1 : 0;
  kicks += 1;
  document.getElementById('goals').textContent = goals;
  document.getElementById('kicks').textContent = kicks;

  const entry = document.createElement('div');
  const icon = isGoal ? '+ GOAL' : '- Save';
  entry.textContent = `${{icon}} | You: ${{userLabel}} | AI: ${{aiLabel}} | ${{(scorePct*100).toFixed(0)}}%`;
  entry.style.color = isGoal ? '#69f0ae' : '#ff8a80';
  const hist = document.getElementById('history');
  hist.insertBefore(entry, hist.firstChild);
  if (hist.children.length > 5) hist.removeChild(hist.lastChild);

  setTimeout(() => {{
    phase = 'idle';
    document.getElementById('msg').textContent = 'Choose a zone!';
    document.getElementById('msg').style.color = '#ffd700';
    document.getElementById('hint').textContent = '';
    draw();
  }}, 1600);
}}

// ---- input ----
function getZone(mx, my) {{
  for (let col = 0; col < 3; col++) {{
    for (let row = 0; row < 2; row++) {{
      const x = POST_X1 + ZONE_W * col;
      const y = row === 0 ? BAR_Y : BAR_Y + (GROUND_Y - BAR_Y) / 2;
      const zh = (GROUND_Y - BAR_Y) / 2;
      if (mx >= x + 2 && mx <= x + ZONE_W - 4 && my >= y + 2 && my <= y + zh - 4) {{
        return col * 2 + row;
      }}
    }}
  }}
  return -1;
}}

canvas.addEventListener('mousemove', e => {{
  if (phase !== 'idle') return;
  const r = canvas.getBoundingClientRect();
  const mx = (e.clientX - r.left) * (W / r.width);
  const my = (e.clientY - r.top) * (H / r.height);
  const z = getZone(mx, my);
  if (z !== hoveredZone) {{ hoveredZone = z; draw(); }}
}});

canvas.addEventListener('mouseleave', () => {{ hoveredZone = -1; draw(); }});

canvas.addEventListener('click', e => {{
  if (phase !== 'idle') return;
  const r = canvas.getBoundingClientRect();
  const mx = (e.clientX - r.left) * (W / r.width);
  const my = (e.clientY - r.top) * (H / r.height);
  const z = getZone(mx, my);
  if (z < 0) return;

  const col = Math.floor(z / 2); // 0=Left,1=Center,2=Right
  userCol = col;

  // AI picks column from Nash probs
  aiCol = weightedChoice(CFG.aiProbs);

  let kickerCol, goalieCol;
  if (CFG.role === 'Kicker') {{
    kickerCol = userCol; goalieCol = aiCol;
  }} else {{
    kickerCol = aiCol; goalieCol = userCol;
  }}

  scorePct = CFG.payoffMatrix[kickerCol][goalieCol];
  isGoal = Math.random() < scorePct;

  // set up animation
  ballX = W / 2; ballY = GROUND_Y + 18;
  const [btx, bty] = zoneCentre(kickerCol, z % 2);
  ballTX = btx; ballTY = bty;

  const [ksx, ksy] = keeperCentre(1);
  keepX = ksx; keepY = ksy;
  const [ktx, kty] = keeperCentre(goalieCol);
  keepTX = ktx; keepTY = kty;

  animT = 0;
  phase = 'animating';
  document.getElementById('msg').textContent = '...';
  document.getElementById('msg').style.color = '#ffd700';
  requestAnimationFrame(tick);
}});

// initial draw
draw();
</script>
</body>
</html>"""


def _play_tab():
    st.header("Play vs AI")

    effective = apply_risk(st.session_state.matrix, st.session_state.risk)
    nash = solve_nash(effective)

    role = st.radio("Your role", ["Kicker", "Goalie"], horizontal=True)

    # Pass Nash probs and payoff matrix to JS as JSON
    ai_probs = nash["goalie"] if role == "Kicker" else nash["kicker"]
    config = json.dumps({
        "role": role,
        "aiProbs": ai_probs.tolist(),
        # payoff_matrix[kicker_idx][goalie_idx] = scoring probability
        "payoffMatrix": effective.tolist(),
        "nashValue": nash["value"],
    })

    html = _build_game_html(config)
    st.components.v1.html(html, height=620, scrolling=False)


def main():
    st.set_page_config(
        page_title="Penalty Shootout Simulator",
        page_icon=":soccer:",
        layout="wide",
    )
    st.title("Tactical Penalty Shootout Simulator")
    st.caption("A zero-sum game theory model of the penalty kick - Mixed Strategy Nash Equilibrium.")

    _init_session_state()
    _sidebar()

    tab_analysis, tab_play = st.tabs(["Analysis & Math", "Play Simulator"])
    with tab_analysis:
        _analysis_tab()
    with tab_play:
        _play_tab()


if __name__ == "__main__":
    main()
