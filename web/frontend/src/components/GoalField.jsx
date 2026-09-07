import { useMemo } from 'react'

/*
 * Cinematic penalty scene, drawn entirely in SVG so it ships inside the
 * single Docker image with no external assets or licences.
 *
 * Contract (all motion is CSS transition on the group `transform`):
 *   phase     : 'idle' | 'windup' | 'flight' | 'result'
 *   shotZone  : zone key the ball travels to   (null until known)
 *   diveZone  : zone key the keeper commits to (null until known)
 *   scored    : boolean | null                 (only meaningful at 'result')
 */

const VB_W = 900
const VB_H = 560
const MOUTH = { L: 250, R: 650, T: 118, B: 330 }
const COLS = 3
const ROWS = 2
const CELL_W = (MOUTH.R - MOUTH.L) / COLS
const CELL_H = (MOUTH.B - MOUTH.T) / ROWS
const SPOT = { x: 450, y: 486 }
const KEEPER_Y = 300

function cell(row, col) {
  const x = MOUTH.L + col * CELL_W
  const y = MOUTH.T + row * CELL_H
  return { x, y, w: CELL_W, h: CELL_H, cx: x + CELL_W / 2, cy: y + CELL_H / 2 }
}

// Deterministic crowd so the stands never reflow between renders.
function buildCrowd() {
  let s = 20260907
  const rnd = () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff)
  const palette = ['#d15b5b', '#5b78d1', '#d8c65a', '#e9e9ef', '#5fae72', '#e0954a', '#b0b6c6']
  const tiers = [
    { y0: 34, y1: 132, jitter: 5 },
    { y0: 132, y1: 224, jitter: 4 },
    { y0: 224, y1: 300, jitter: 3 },
  ]
  const dots = []
  for (let i = 0; i < 560; i += 1) {
    const tier = tiers[Math.floor(rnd() * tiers.length)]
    dots.push({
      x: rnd() * VB_W,
      y: tier.y0 + rnd() * (tier.y1 - tier.y0),
      r: 1.5 + rnd() * (tier.jitter - 1),
      c: palette[Math.floor(rnd() * palette.length)],
      o: 0.35 + rnd() * 0.5,
    })
  }
  return dots
}

function Keeper({ diveZone }) {
  let tx = 0
  let angle = 0
  let reach = 0
  if (diveZone) {
    const target = cell(diveZone.row, diveZone.col)
    tx = target.cx - SPOT.x
    const side = diveZone.col === 0 ? -1 : diveZone.col === 2 ? 1 : 0
    angle = side * 62
    reach = side * 14
    if (side === 0) angle = diveZone.row === 0 ? -10 : 6
  }
  return (
    <g
      className="gk"
      style={{ transform: `translate(${SPOT.x + tx * 0.62}px, ${KEEPER_Y}px) rotate(${angle}deg)` }}
    >
      <ellipse className="gk-blur" cx={reach * -3} cy={4} rx={diveZone ? 46 : 0} ry="14" />
      {/* legs */}
      <path d="M-9 6 L-13 40 -4 40 -2 8 Z" fill="#1f2937" />
      <path d="M9 6 L13 40 4 40 2 8 Z" fill="#111827" />
      {/* jersey */}
      <path d="M-19 -34 Q0 -42 19 -34 L16 10 Q0 16 -16 10 Z" fill="#e23b3b" />
      <path d="M-19 -34 Q0 -42 19 -34 L17 -24 Q0 -32 -17 -24 Z" fill="#b52a2a" />
      <text x="0" y="-6" textAnchor="middle" className="gk-number">1</text>
      {/* arms + gloves */}
      <g className="gk-arm gk-arm-l">
        <path d="M-17 -30 q-20 4 -30 20" stroke="#e23b3b" strokeWidth="8" fill="none" strokeLinecap="round" />
        <rect x={-52} y={-16} width="14" height="16" rx="4" fill="#f4d35e" stroke="#caa93b" />
      </g>
      <g className="gk-arm gk-arm-r">
        <path d="M17 -30 q20 4 30 20" stroke="#e23b3b" strokeWidth="8" fill="none" strokeLinecap="round" />
        <rect x={38} y={-16} width="14" height="16" rx="4" fill="#f4d35e" stroke="#caa93b" />
      </g>
      {/* head */}
      <circle cx="0" cy="-46" r="11" fill="#e8b98f" />
      <path d="M-11 -49 a11 11 0 0 1 22 0 q-11 -6 -22 0Z" fill="#3a2a20" />
    </g>
  )
}

function Ball({ phase, shotZone }) {
  const flying = (phase === 'flight' || phase === 'result') && shotZone
  let tx = SPOT.x
  let ty = SPOT.y
  let scale = 1
  let spin = 0
  if (flying) {
    const target = cell(shotZone.row, shotZone.col)
    tx = target.cx
    ty = target.cy
    scale = 0.62
    spin = shotZone.col === 0 ? -720 : 720
  }
  return (
    <>
      <ellipse
        className="ball-shadow"
        cx={tx}
        cy={flying ? MOUTH.B + 6 : SPOT.y + 16}
        rx={flying ? 12 : 20}
        ry={flying ? 4 : 7}
      />
      <g
        className={`ball-orb ${flying ? 'flying' : ''}`}
        style={{ transform: `translate(${tx}px, ${ty}px) scale(${scale}) rotate(${spin}deg)` }}
      >
        <circle r="17" fill="url(#ballShade)" stroke="#c8ccd4" strokeWidth="0.6" />
        <path d="M0 -9 L8.5 -3 5 7 -5 7 -8.5 -3 Z" fill="#1f2430" />
        <path d="M0 -17 L4 -11 -4 -11 Z" fill="#1f2430" />
        <path d="M17 -2 l-6 4 2 -8 Z" fill="#1f2430" />
        <path d="M-17 -2 l6 4 -2 -8 Z" fill="#1f2430" />
        <path d="M9 13 l-3 -6 6 1 Z" fill="#1f2430" />
        <path d="M-9 13 l3 -6 -6 1 Z" fill="#1f2430" />
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
  scored = null,
}) {
  const crowd = useMemo(buildCrowd, [])
  const shotZoneObj = shotZone ? zones.find((z) => z.key === shotZone) : null
  const diveZoneObj = diveZone ? zones.find((z) => z.key === diveZone) : null

  const stripes = []
  for (let i = 0; i < 11; i += 1) {
    const x0 = (i * VB_W) / 10
    const x1 = ((i + 1) * VB_W) / 10
    stripes.push(
      <path
        key={i}
        d={`M${x0} ${VB_H} L${x1} ${VB_H} L${450 + (x1 - 450) * 0.42} ${MOUTH.B} L${450 + (x0 - 450) * 0.42} ${MOUTH.B} Z`}
        fill={i % 2 ? '#2f8f43' : '#278A3C'}
      />,
    )
  }

  const mesh = []
  for (let d = -14; d <= 22; d += 1) {
    const off = d * 20
    mesh.push(
      <line key={`a${d}`} x1={MOUTH.L + off} y1={MOUTH.T} x2={MOUTH.L + off - (MOUTH.B - MOUTH.T)} y2={MOUTH.B} />,
      <line key={`b${d}`} x1={MOUTH.L + off} y1={MOUTH.T} x2={MOUTH.L + off + (MOUTH.B - MOUTH.T)} y2={MOUTH.B} />,
    )
  }

  return (
    <div className={`goalfield phase-${phase}`}>
      <p className="goalfield-prompt">{mode === 'shoot' ? 'Choose where to shoot' : 'Choose where to dive'}</p>
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="goalfield-svg" role="group" aria-label="Penalty scene">
        <defs>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0a1330" />
            <stop offset="100%" stopColor="#14224b" />
          </linearGradient>
          <linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1c6f33" />
            <stop offset="100%" stopColor="#2f9647" />
          </linearGradient>
          <radialGradient id="ballShade" cx="38%" cy="32%" r="72%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="70%" stopColor="#eef0f3" />
            <stop offset="100%" stopColor="#c3c8d1" />
          </radialGradient>
          <radialGradient id="flood" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(255,247,214,0.55)" />
            <stop offset="100%" stopColor="rgba(255,247,214,0)" />
          </radialGradient>
          <radialGradient id="vignette" cx="50%" cy="42%" r="70%">
            <stop offset="60%" stopColor="rgba(0,0,0,0)" />
            <stop offset="100%" stopColor="rgba(0,0,0,0.45)" />
          </radialGradient>
          <filter id="soft" x="-40%" y="-40%" width="180%" height="180%">
            <feDropShadow dx="0" dy="5" stdDeviation="5" floodColor="#000" floodOpacity="0.4" />
          </filter>
          <clipPath id="mouthClip">
            <rect x={MOUTH.L} y={MOUTH.T} width={MOUTH.R - MOUTH.L} height={MOUTH.B - MOUTH.T} />
          </clipPath>
        </defs>

        {/* sky + stands + crowd */}
        <rect x="0" y="0" width={VB_W} height={MOUTH.B} fill="url(#sky)" />
        <path d={`M0 ${MOUTH.B} L0 96 Q450 -8 ${VB_W} 96 L${VB_W} ${MOUTH.B} Z`} fill="#0e1a3c" />
        <path d={`M0 ${MOUTH.B} L0 168 Q450 96 ${VB_W} 168 L${VB_W} ${MOUTH.B} Z`} fill="#122048" opacity="0.85" />
        <g className="crowd">
          {crowd.map((dot, i) => (
            <circle key={i} cx={dot.x} cy={dot.y} r={dot.r} fill={dot.c} opacity={dot.o} />
          ))}
        </g>

        {/* floodlights */}
        {[140, 760].map((x) => (
          <g key={x} className="floodlight">
            <rect x={x - 26} y="8" width="52" height="14" rx="3" fill="#c9ccd6" />
            <rect x={x - 3} y="20" width="6" height="26" fill="#8b8f9c" />
            <circle cx={x} cy="15" r="60" fill="url(#flood)" />
          </g>
        ))}

        {/* pitch */}
        <rect x="0" y={MOUTH.B} width={VB_W} height={VB_H - MOUTH.B} fill="url(#grass)" />
        <g opacity="0.5">{stripes}</g>
        <path
          d={`M${SPOT.x - 210} ${VB_H} Q${SPOT.x} ${MOUTH.B + 34} ${SPOT.x + 210} ${VB_H}`}
          fill="none"
          stroke="rgba(255,255,255,0.5)"
          strokeWidth="3"
        />
        <path
          d={`M180 ${VB_H} L${VB_W - 180} ${VB_H} L${VB_W - 300} ${MOUTH.B + 8} L300 ${MOUTH.B + 8} Z`}
          fill="none"
          stroke="rgba(255,255,255,0.45)"
          strokeWidth="3"
        />
        <ellipse cx={SPOT.x} cy={SPOT.y + 2} rx="4" ry="2.4" fill="#fff" />

        {/* goal: back net plane, mesh, posts */}
        <rect
          x={MOUTH.L + 14}
          y={MOUTH.T + 10}
          width={MOUTH.R - MOUTH.L - 28}
          height={MOUTH.B - MOUTH.T - 10}
          fill="rgba(10,18,40,0.55)"
        />
        <path d={`M${MOUTH.L} ${MOUTH.T} L${MOUTH.L + 14} ${MOUTH.T + 10}`} stroke="#eef1f6" strokeWidth="3" />
        <path d={`M${MOUTH.R} ${MOUTH.T} L${MOUTH.R - 14} ${MOUTH.T + 10}`} stroke="#eef1f6" strokeWidth="3" />
        <g className="net" clipPath="url(#mouthClip)">{mesh}</g>
        <g className="goal-frame" filter="url(#soft)">
          <rect x={MOUTH.L - 7} y={MOUTH.T - 7} width="12" height={MOUTH.B - MOUTH.T + 7} rx="5" fill="#f4f6fa" />
          <rect x={MOUTH.R - 5} y={MOUTH.T - 7} width="12" height={MOUTH.B - MOUTH.T + 7} rx="5" fill="#f4f6fa" />
          <rect x={MOUTH.L - 7} y={MOUTH.T - 7} width={MOUTH.R - MOUTH.L + 14} height="12" rx="5" fill="#ffffff" />
        </g>

        {/* keeper + ball */}
        <Keeper diveZone={diveZoneObj} />
        <Ball phase={phase} shotZone={shotZoneObj} />

        {/* clickable zones */}
        {zones.map((zone) => {
          const r = cell(zone.row, zone.col)
          const isSelected = zone.key === selectedZone
          return (
            <g
              key={zone.key}
              className={`zone ${isSelected ? 'zone-selected' : ''} ${interactive ? 'zone-live' : ''}`}
              onClick={() => interactive && onSelect?.(zone.key)}
            >
              <rect x={r.x + 4} y={r.y + 4} width={r.w - 8} height={r.h - 8} rx="8" />
              <g className="reticle" transform={`translate(${r.cx} ${r.cy})`}>
                <circle r="17" fill="none" strokeWidth="2.5" />
                <path d="M0 -24 V-11 M0 11 V24 M-24 0 H-11 M11 0 H24" strokeWidth="2.5" />
              </g>
              <text x={r.cx} y={r.y + 18} textAnchor="middle" className="zone-code">
                {zone.short}
              </text>
            </g>
          )
        })}

        {/* impact FX */}
        {phase === 'result' && scored !== null && (
          <g className="fx">
            <rect
              x={MOUTH.L}
              y={MOUTH.T}
              width={MOUTH.R - MOUTH.L}
              height={MOUTH.B - MOUTH.T}
              fill={scored ? 'rgba(57,217,138,0.22)' : 'rgba(245,165,36,0.22)'}
            />
            <text x={VB_W / 2} y={MOUTH.T - 22} textAnchor="middle" className={`stamp ${scored ? 'stamp-goal' : 'stamp-save'}`}>
              {scored ? 'GOAL!' : 'SAVED!'}
            </text>
          </g>
        )}

        <rect x="0" y="0" width={VB_W} height={VB_H} fill="url(#vignette)" pointerEvents="none" />
      </svg>
    </div>
  )
}
