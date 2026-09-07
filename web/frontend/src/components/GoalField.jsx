// SVG penalty scene: goal frame, six clickable target zones, goalkeeper, ball.
// All motion is CSS transition on SVG geometry attributes.

const VB_W = 400
const VB_H = 270
const GOAL = { x0: 46, x1: 354, y0: 26, y1: 196 }
const COLS = 3
const ROWS = 2
const CELL_W = (GOAL.x1 - GOAL.x0) / COLS
const CELL_H = (GOAL.y1 - GOAL.y0) / ROWS

function zoneRect(row, col) {
  return {
    x: GOAL.x0 + col * CELL_W,
    y: GOAL.y0 + row * CELL_H,
    w: CELL_W,
    h: CELL_H,
    cx: GOAL.x0 + col * CELL_W + CELL_W / 2,
    cy: GOAL.y0 + row * CELL_H + CELL_H / 2,
  }
}

export default function GoalField({
  zones,
  mode = 'shoot',
  selectedKey,
  onSelect,
  disabled = false,
  keeperKey = null,
  ballKey = null,
  phase = 'idle',
  scored = null,
}) {
  const spot = { x: VB_W / 2, y: 250 }
  const keeperZone = keeperKey ? zones.find((z) => z.key === keeperKey) : null
  const keeperPos = keeperZone ? zoneRect(keeperZone.row, keeperZone.col) : { cx: VB_W / 2, cy: GOAL.y1 - CELL_H / 2 }

  const ballZone = ballKey ? zones.find((z) => z.key === ballKey) : null
  let ballPos = spot
  if (phase !== 'idle' && ballZone) {
    const r = zoneRect(ballZone.row, ballZone.col)
    ballPos = { x: r.cx, y: r.cy }
  }

  return (
    <div className="goalfield">
      <p className="goalfield-prompt">
        {mode === 'shoot' ? 'Choose where to shoot' : 'Choose where to dive'}
      </p>
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="goalfield-svg" role="group" aria-label="Penalty goal">
        <defs>
          <linearGradient id="grass" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#1f7a3d" />
            <stop offset="100%" stopColor="#125427" />
          </linearGradient>
        </defs>

        <rect x="0" y="0" width={VB_W} height={VB_H} fill="url(#grass)" />
        <ellipse cx={VB_W / 2} cy={GOAL.y1 + 46} rx="150" ry="30" fill="none" stroke="rgba(255,255,255,0.25)" />
        <circle cx={spot.x} cy={spot.y - 6} r="2.5" fill="#fff" />

        {/* net */}
        <rect
          x={GOAL.x0}
          y={GOAL.y0}
          width={GOAL.x1 - GOAL.x0}
          height={GOAL.y1 - GOAL.y0}
          fill="rgba(255,255,255,0.05)"
        />
        {Array.from({ length: 13 }).map((_, i) => (
          <line
            key={`v${i}`}
            x1={GOAL.x0 + (i * (GOAL.x1 - GOAL.x0)) / 12}
            y1={GOAL.y0}
            x2={GOAL.x0 + (i * (GOAL.x1 - GOAL.x0)) / 12}
            y2={GOAL.y1}
            stroke="rgba(255,255,255,0.12)"
          />
        ))}
        {Array.from({ length: 8 }).map((_, i) => (
          <line
            key={`h${i}`}
            x1={GOAL.x0}
            y1={GOAL.y0 + (i * (GOAL.y1 - GOAL.y0)) / 7}
            x2={GOAL.x1}
            y2={GOAL.y0 + (i * (GOAL.y1 - GOAL.y0)) / 7}
            stroke="rgba(255,255,255,0.12)"
          />
        ))}

        {/* keeper */}
        <g
          className={`gk ${phase === 'result' ? 'gk-dive' : ''}`}
          style={{ transform: `translate(${keeperPos.cx - VB_W / 2}px, ${keeperPos.cy - (GOAL.y1 - CELL_H / 2)}px)` }}
        >
          <circle cx={VB_W / 2} cy={GOAL.y1 - CELL_H / 2 - 12} r="8" fill="#ffd15b" />
          <rect x={VB_W / 2 - 10} y={GOAL.y1 - CELL_H / 2 - 4} width="20" height="26" rx="5" fill="#ffd15b" />
        </g>

        {/* clickable zones */}
        {zones.map((zone) => {
          const r = zoneRect(zone.row, zone.col)
          const selected = zone.key === selectedKey
          return (
            <g key={zone.key} className={`zone ${selected ? 'zone-selected' : ''} ${disabled ? 'zone-disabled' : ''}`}>
              <rect
                x={r.x + 3}
                y={r.y + 3}
                width={r.w - 6}
                height={r.h - 6}
                rx="6"
                onClick={() => !disabled && onSelect?.(zone.key)}
              />
              <text x={r.cx} y={r.cy + 5} textAnchor="middle" className="zone-code">
                {zone.short}
              </text>
            </g>
          )
        })}

        {/* goal frame */}
        <path
          d={`M${GOAL.x0} ${GOAL.y1} L${GOAL.x0} ${GOAL.y0} L${GOAL.x1} ${GOAL.y0} L${GOAL.x1} ${GOAL.y1}`}
          fill="none"
          stroke="#fff"
          strokeWidth="5"
          strokeLinecap="round"
        />

        {/* ball */}
        <circle
          className={`ball ${phase}`}
          cx={ballPos.x}
          cy={ballPos.y}
          r={phase === 'idle' ? 7 : 5}
          fill="#fff"
          stroke="#111"
          strokeWidth="1"
        />

        {phase === 'result' && scored !== null && (
          <text
            x={VB_W / 2}
            y={GOAL.y0 - 8}
            textAnchor="middle"
            className={scored ? 'verdict verdict-goal' : 'verdict verdict-save'}
          >
            {scored ? 'GOAL' : 'SAVED'}
          </text>
        )}
      </svg>
    </div>
  )
}
