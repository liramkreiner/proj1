import { useMemo } from 'react'

/*
 * A televised penalty view — night stadium, real goal, keeper and ball —
 * drawn entirely in inline SVG so it ships in the single Docker image.
 *
 * Contract:
 *   phase    : 'idle' | 'windup' | 'flight' | 'result'
 *   shotZone : zone key the ball travels to     (null until 'flight')
 *   diveZone : zone key the keeper commits to   (null until 'flight')
 *   outcome  : 'goal' | 'save' | null           (meaningful at 'result')
 */

const VB_W = 900
const VB_H = 560
const GOAL = { L: 252, R: 648, T: 116, B: 340 }
const COLS = 3
const ROWS = 2
const CW = (GOAL.R - GOAL.L) / COLS
const CH = (GOAL.B - GOAL.T) / ROWS
const SPOT = { x: 450, y: 502 }
const KEEPER_FEET_Y = GOAL.B - 4

function cell(row, col) {
  const x = GOAL.L + col * CW
  const y = GOAL.T + row * CH
  return { x, y, w: CW, h: CH, cx: x + CW / 2, cy: y + CH / 2 }
}

/* deterministic crowd so the stands never reflow */
function buildCrowd() {
  let s = 918273
  const rnd = () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff)
  const shirts = ['#e0463f', '#3f74e0', '#e8c249', '#eef1f6', '#4fae6b', '#e08a3c', '#9aa6bd', '#b8453f']
  const tiers = [
    { y0: 30, y1: 118 },
    { y0: 118, y1: 210 },
    { y0: 210, y1: 292 },
  ]
  const dots = []
  for (let i = 0; i < 620; i += 1) {
    const t = tiers[Math.floor(rnd() * tiers.length)]
    dots.push({
      x: rnd() * VB_W,
      y: t.y0 + rnd() * (t.y1 - t.y0),
      r: 1.5 + rnd() * 1.7,
      c: shirts[Math.floor(rnd() * shirts.length)],
      o: 0.4 + rnd() * 0.5,
    })
  }
  return dots
}

/* The keeper commits to a SIDE. Row (high/low) tilts the dive and lifts the
 * gloves; it is never a hop to an arbitrary square. */
function keeperPose(diveZone) {
  if (!diveZone) return { tx: SPOT.x, ty: KEEPER_FEET_Y, rot: 0, side: 0, high: false, diving: false }
  const side = diveZone.col === 0 ? -1 : diveZone.col === 2 ? 1 : 0
  const high = diveZone.row === 0
  if (side === 0) {
    return { tx: SPOT.x, ty: KEEPER_FEET_Y - (high ? 34 : 0), rot: 0, side: 0, high, diving: true }
  }
  return {
    tx: SPOT.x + side * 146,
    ty: KEEPER_FEET_Y - (high ? 30 : 2),
    rot: side * (high ? 40 : 66),
    side,
    high,
    diving: true,
  }
}

// Where the gloves actually render, in scene coords — the same translate∘rotate
// the SVG applies to the dive-glove midpoint (local ≈ (1, -149)). Used to rest
// the ball in the keeper's hands on a save.
function glovePoint(pose) {
  const rad = (pose.rot * Math.PI) / 180
  const lx = 1
  const ly = -149
  return {
    x: pose.tx + lx * Math.cos(rad) - ly * Math.sin(rad),
    y: pose.ty + lx * Math.sin(rad) + ly * Math.cos(rad),
  }
}

function Keeper({ diveZone }) {
  const pose = keeperPose(diveZone)
  const { tx, ty, rot, diving } = pose
  const arms = diving
    ? 'M-13 -104 L-24 -150 M13 -104 L26 -148'
    : 'M-16 -98 L-40 -66 M16 -98 L40 -66'
  const gloves = diving
    ? [
        [-24, -150],
        [26, -148],
      ]
    : [
        [-40, -66],
        [40, -66],
      ]
  return (
    <g className={`gk ${diving ? 'is-diving' : ''}`} style={{ transform: `translate(${tx}px, ${ty}px)` }}>
      <ellipse className="gk-shadow" cx="0" cy="4" rx={diving ? 34 : 22} ry="6" />
      <g style={{ transform: `rotate(${rot}deg)` }}>
        {/* legs */}
        <rect className="gk-skin" x="-14" y="-44" width="11" height="44" rx="3" />
        <rect className="gk-skin" x="3" y="-44" width="11" height="44" rx="3" />
        <rect className="gk-sock" x="-14" y="-14" width="11" height="14" rx="2" />
        <rect className="gk-sock" x="3" y="-14" width="11" height="14" rx="2" />
        {/* shorts */}
        <rect className="gk-shorts" x="-17" y="-60" width="34" height="20" rx="3" />
        {/* jersey */}
        <path className="gk-kit" d="M-18 -58 q18 -8 36 0 l-4 -46 q-14 -6 -28 0 z" />
        <text className="gk-num" x="0" y="-78" textAnchor="middle">1</text>
        {/* arms */}
        <path className="gk-kit-line" d={arms} />
        {gloves.map(([gx, gy], i) => (
          <circle key={i} className="gk-glove" cx={gx} cy={gy} r="7" />
        ))}
        {/* head */}
        <circle className="gk-skin" cx="0" cy="-116" r="12" />
        <path className="gk-hair" d="M-12 -118 a12 12 0 0 1 24 0 q-12 -7 -24 0z" />
      </g>
    </g>
  )
}

function Ball({ phase, shotZone, diveZone, outcome }) {
  const flying = (phase === 'flight' || phase === 'result') && shotZone
  let x = SPOT.x
  let y = SPOT.y
  let scale = 1
  let spin = 0
  if (flying) {
    const target = cell(shotZone.row, shotZone.col)
    if (outcome === 'save' && diveZone) {
      // the keeper got there — the ball dies on the gloves
      const g = glovePoint(keeperPose(diveZone))
      x = g.x
      y = g.y
      scale = 0.72
    } else {
      x = target.cx
      y = target.cy
      scale = 0.5 // small: it's deep in the net
    }
    spin = shotZone.col === 0 ? -600 : shotZone.col === 2 ? 600 : 300
  }
  return (
    <>
      {flying && <line className="ball-trail" x1={SPOT.x} y1={SPOT.y} x2={x} y2={y} />}
      <ellipse className="ball-shadow" cx={x} cy={flying ? GOAL.B + 10 : SPOT.y + 15} rx={flying ? 9 : 16} ry={flying ? 3 : 5.5} />
      <g className="ball" style={{ transform: `translate(${x}px, ${y}px) scale(${scale}) rotate(${spin}deg)` }}>
        <circle r="15" fill="url(#ball-shade)" stroke="#c4c9d2" strokeWidth="0.6" />
        <path d="M0 -8 L7.6 -2.5 4.7 6.5 -4.7 6.5 -7.6 -2.5 Z" fill="#20242e" />
        <path d="M0 -15 L3.6 -9.5 -3.6 -9.5 Z" fill="#20242e" />
        <path d="M15 -1.5 l-5.5 3.5 1.6 -7 Z" fill="#20242e" />
        <path d="M-15 -1.5 l5.5 3.5 -1.6 -7 Z" fill="#20242e" />
        <path d="M8 12 l-2.6 -5.4 5.4 1 Z" fill="#20242e" />
        <path d="M-8 12 l2.6 -5.4 -5.4 1 Z" fill="#20242e" />
      </g>
    </>
  )
}

export default function GoalField({
  zones,
  mode = 'shoot',
  selectedZone = null,
  onSelect,
  interactive = true,
  phase = 'idle',
  shotZone = null,
  diveZone = null,
  outcome = null,
}) {
  const crowd = useMemo(buildCrowd, [])
  const shotObj = shotZone ? zones.find((z) => z.key === shotZone) : null
  const diveObj = diveZone ? zones.find((z) => z.key === diveZone) : null

  const stripes = []
  for (let i = 0; i < 12; i += 1) {
    const x0 = (i * VB_W) / 11
    const x1 = ((i + 1) * VB_W) / 11
    stripes.push(
      <path
        key={i}
        d={`M${x0} ${VB_H} L${x1} ${VB_H} L${450 + (x1 - 450) * 0.34} ${GOAL.B} L${450 + (x0 - 450) * 0.34} ${GOAL.B} Z`}
        fill={i % 2 ? '#2f9d47' : '#279141'}
      />,
    )
  }

  const net = []
  for (let d = -12; d <= 22; d += 1) {
    const o = d * 22
    net.push(
      <line key={`a${d}`} x1={GOAL.L + o} y1={GOAL.T} x2={GOAL.L + o - (GOAL.B - GOAL.T)} y2={GOAL.B} />,
      <line key={`b${d}`} x1={GOAL.L + o} y1={GOAL.T} x2={GOAL.L + o + (GOAL.B - GOAL.T)} y2={GOAL.B} />,
    )
  }

  return (
    <div className={`pitch phase-${phase}`}>
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="pitch-svg" role="group" aria-label="Penalty scene">
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0a1226" />
            <stop offset="100%" stopColor="#14224a" />
          </linearGradient>
          <linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1c7538" />
            <stop offset="100%" stopColor="#33a24c" />
          </linearGradient>
          <radialGradient id="ball-shade" cx="38%" cy="32%" r="72%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="72%" stopColor="#eef0f4" />
            <stop offset="100%" stopColor="#c2c7d1" />
          </radialGradient>
          <radialGradient id="flood" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(255,248,220,0.6)" />
            <stop offset="100%" stopColor="rgba(255,248,220,0)" />
          </radialGradient>
          <radialGradient id="vig" cx="50%" cy="44%" r="72%">
            <stop offset="58%" stopColor="rgba(0,0,0,0)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.42)" />
          </radialGradient>
          <clipPath id="mouth">
            <rect x={GOAL.L} y={GOAL.T} width={GOAL.R - GOAL.L} height={GOAL.B - GOAL.T} />
          </clipPath>
        </defs>

        {/* stadium */}
        <rect x="0" y="0" width={VB_W} height={GOAL.B} fill="url(#sky)" />
        <path d={`M0 ${GOAL.B} L0 88 Q450 -6 ${VB_W} 88 L${VB_W} ${GOAL.B} Z`} fill="#0e1a3e" />
        <path d={`M0 ${GOAL.B} L0 160 Q450 92 ${VB_W} 160 L${VB_W} ${GOAL.B} Z`} fill="#122049" opacity="0.9" />
        <g className="crowd">
          {crowd.map((d, i) => (
            <circle key={i} cx={d.x} cy={d.y} r={d.r} fill={d.c} opacity={d.o} />
          ))}
        </g>
        {[128, 772].map((x) => (
          <g key={x} className="flood">
            <rect x={x - 30} y="6" width="60" height="13" rx="3" fill="#cdd0da" />
            <rect x={x - 3} y="19" width="6" height="24" fill="#8b8f9c" />
            <circle cx={x} cy="13" r="66" fill="url(#flood)" />
          </g>
        ))}

        {/* pitch */}
        <rect x="0" y={GOAL.B} width={VB_W} height={VB_H - GOAL.B} fill="url(#grass)" />
        <g opacity="0.45">{stripes}</g>
        <path
          d={`M${SPOT.x - 232} ${VB_H} Q${SPOT.x} ${GOAL.B + 30} ${SPOT.x + 232} ${VB_H}`}
          fill="none"
          stroke="rgba(255,255,255,0.55)"
          strokeWidth="3"
        />
        <path
          d={`M150 ${VB_H} L${VB_W - 150} ${VB_H} L${VB_W - 292} ${GOAL.B + 6} L292 ${GOAL.B + 6} Z`}
          fill="none"
          stroke="rgba(255,255,255,0.5)"
          strokeWidth="3"
        />
        <ellipse cx={SPOT.x} cy={SPOT.y + 3} rx="4" ry="2.4" fill="#fff" />

        {/* goal */}
        <rect x={GOAL.L + 12} y={GOAL.T + 8} width={GOAL.R - GOAL.L - 24} height={GOAL.B - GOAL.T - 8} fill="rgba(9,16,38,0.5)" />
        <g className="net" clipPath="url(#mouth)">{net}</g>
        <g className="goal-frame">
          <rect x={GOAL.L - 7} y={GOAL.T - 7} width="12" height={GOAL.B - GOAL.T + 7} rx="5" fill="#f3f5f9" />
          <rect x={GOAL.R - 5} y={GOAL.T - 7} width="12" height={GOAL.B - GOAL.T + 7} rx="5" fill="#f3f5f9" />
          <rect x={GOAL.L - 7} y={GOAL.T - 7} width={GOAL.R - GOAL.L + 14} height="12" rx="5" fill="#ffffff" />
        </g>

        {/* keeper + ball */}
        <Keeper diveZone={diveObj} />
        <Ball phase={phase} shotZone={shotObj} diveZone={diveObj} outcome={outcome} />

        {/* target zones */}
        {zones.map((zone) => {
          const r = cell(zone.row, zone.col)
          const sel = zone.key === selectedZone
          return (
            <g
              key={zone.key}
              className={`zone ${sel ? 'is-selected' : ''} ${interactive ? 'is-live' : ''}`}
              onClick={() => interactive && onSelect?.(zone.key)}
            >
              <rect x={r.x + 3} y={r.y + 3} width={r.w - 6} height={r.h - 6} rx="5" />
              <circle className="zone-ring" cx={r.cx} cy={r.cy} r="15" />
              <text x={r.cx} y={r.y + 17} textAnchor="middle" className="zone-tag">
                {zone.short}
              </text>
            </g>
          )
        })}

        {phase === 'result' && outcome && (
          <text
            x={VB_W / 2}
            y={GOAL.T - 20}
            textAnchor="middle"
            className={outcome === 'goal' ? 'shout shout-goal' : 'shout shout-save'}
          >
            {outcome === 'goal' ? 'GOAL' : 'SAVED'}
          </text>
        )}

        <rect x="0" y="0" width={VB_W} height={VB_H} fill="url(#vig)" pointerEvents="none" />
      </svg>
      <p className="pitch-caption">{mode === 'shoot' ? 'Your kick pick a corner' : 'Your save pick a side'}</p>
    </div>
  )
}
