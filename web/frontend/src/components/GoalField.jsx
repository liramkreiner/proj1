import { useMemo } from 'react'

/*
 * The board: the penalty drawn in chalk on turf, from behind the spot.
 * Everything is inline SVG so it ships in the single Docker image with no
 * external art. The shot is the only thing that animates.
 *
 * Contract:
 *   phase    : 'idle' | 'windup' | 'flight' | 'result'
 *   shotZone : zone key the ball travels to   (null until 'flight')
 *   diveZone : zone key the keeper commits to (null until 'flight')
 *   scored   : boolean | null                 (meaningful at 'result')
 */

const VB_W = 900
const VB_H = 486
const MOUTH = { L: 198, R: 702, T: 124, B: 366 }
const COLS = 3
const ROWS = 2
const CELL_W = (MOUTH.R - MOUTH.L) / COLS
const CELL_H = (MOUTH.B - MOUTH.T) / ROWS
const SPOT = { x: 450, y: 440 }
const KEEPER_X = 450
const KEEPER_FEET = MOUTH.B - 4

function cell(row, col) {
  const x = MOUTH.L + col * CELL_W
  const y = MOUTH.T + row * CELL_H
  return { x, y, w: CELL_W, h: CELL_H, cx: x + CELL_W / 2, cy: y + CELL_H / 2 }
}

// The keeper commits to a SIDE — left, right, or stays central. High vs low
// only changes how high the dive is, never a hop to an arbitrary square.
function keeperPose(diveZone) {
  if (!diveZone) return { tx: KEEPER_X, ty: KEEPER_FEET, diving: false, side: 0, high: false }
  const side = diveZone.col === 0 ? -1 : diveZone.col === 2 ? 1 : 0
  const high = diveZone.row === 0
  if (side === 0) {
    return { tx: KEEPER_X, ty: KEEPER_FEET - (high ? 16 : 0), diving: true, side: 0, high }
  }
  return { tx: KEEPER_X + side * 138, ty: KEEPER_FEET - (high ? 40 : 8), diving: true, side, high }
}

function Keeper({ diveZone }) {
  const { tx, ty, diving, side, high } = keeperPose(diveZone)
  return (
    <g className={`gk ${diving ? 'gk--diving' : ''}`} style={{ transform: `translate(${tx}px, ${ty}px)` }}>
      <ellipse className="gk-streak" cx={-side * 48} cy={-28} rx={side ? 78 : 0} ry="12" />
      {side === 0 ? (
        // standing: ready crouch, a touch taller for a high ball
        <g style={{ transform: `translateY(${high ? -8 : 0}px)` }}>
          <path className="gk-line" d="M0 -2 L-14 42 M0 -2 L14 42" />
          <path className="gk-line" d="M0 -2 L0 -44" />
          <path className="gk-line gk-arms" d={high ? 'M0 -40 L-24 -66 M0 -40 L24 -66' : 'M0 -38 L-32 -18 M0 -38 L32 -18'} />
          <circle className="gk-head" cx="0" cy="-56" r="11" />
        </g>
      ) : (
        // full-length dive toward the near post: body near horizontal, gloves leading.
        // Figure is drawn reaching +x; scaleX(side) points it at the correct post.
        <g style={{ transform: `scaleX(${side})` }}>
          <path className="gk-line" d="M0 8 L64 -12" />
          <path className="gk-line" d="M0 8 L-52 30 M0 8 L-44 42" />
          <path className="gk-line gk-arms" d="M52 -8 L100 -26 M52 -8 L98 -8" />
          <circle className="gk-glove" cx={100} cy={-26} r="7" />
          <circle className="gk-glove" cx={98} cy={-8} r="7" />
          <circle className="gk-head" cx={64} cy={-14} r="11" />
        </g>
      )}
    </g>
  )
}

function Ball({ phase, shotZone }) {
  const flying = (phase === 'flight' || phase === 'result') && shotZone
  let x = SPOT.x
  let y = SPOT.y
  let scale = 1
  let spin = 0
  if (flying) {
    const t = cell(shotZone.row, shotZone.col)
    x = t.cx
    y = t.cy
    scale = 0.66
    spin = shotZone.col === 0 ? -540 : shotZone.col === 2 ? 540 : 300
  }
  return (
    <>
      {flying && (
        <line className="ball-trail" x1={SPOT.x} y1={SPOT.y} x2={x} y2={y} />
      )}
      <ellipse className="ball-shadow" cx={x} cy={flying ? MOUTH.B + 8 : SPOT.y + 14} rx={flying ? 10 : 17} ry={flying ? 3.5 : 6} />
      <g className="ball" style={{ transform: `translate(${x}px, ${y}px) scale(${scale}) rotate(${spin}deg)` }}>
        <circle r="15" className="ball-body" />
        <path className="ball-mark" d="M-9 -4 L9 4 M-4 9 L4 -9" />
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
  const shotZoneObj = shotZone ? zones.find((z) => z.key === shotZone) : null
  const diveZoneObj = diveZone ? zones.find((z) => z.key === diveZone) : null

  // mowing arcs on the turf, drawn as faint chalk
  const arcs = useMemo(
    () =>
      [96, 150, 210].map((r, i) => (
        <path
          key={i}
          className="turf-arc"
          d={`M${SPOT.x - r} ${VB_H} A ${r} ${r * 0.5} 0 0 1 ${SPOT.x + r} ${VB_H}`}
        />
      )),
    [],
  )

  // goal net as sparse chalk hatching
  const net = useMemo(() => {
    const lines = []
    for (let i = 1; i < 12; i += 1) {
      const x = MOUTH.L + (i * (MOUTH.R - MOUTH.L)) / 12
      lines.push(<line key={`v${i}`} x1={x} y1={MOUTH.T} x2={x} y2={MOUTH.B} />)
    }
    for (let j = 1; j < 5; j += 1) {
      const y = MOUTH.T + (j * (MOUTH.B - MOUTH.T)) / 5
      lines.push(<line key={`h${j}`} x1={MOUTH.L} y1={y} x2={MOUTH.R} y2={y} />)
    }
    return lines
  }, [])

  return (
    <div className={`board phase-${phase}`}>
      <svg viewBox={`0 0 ${VB_W} ${VB_H}`} className="board-svg" role="group" aria-label="Penalty, drawn on the tactics board">
        <defs>
          <filter id="rough" x="-20%" y="-20%" width="140%" height="140%">
            <feTurbulence type="fractalNoise" baseFrequency="0.014 0.02" numOctaves="2" seed="7" result="n" />
            <feDisplacementMap in="SourceGraphic" in2="n" scale="4.5" xChannelSelector="R" yChannelSelector="G" />
          </filter>
          <filter id="grain">
            <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" result="t" />
            <feColorMatrix in="t" type="saturate" values="0" />
          </filter>
        </defs>

        <rect x="0" y="0" width={VB_W} height={VB_H} className="board-ground" />
        <g className="turf">{arcs}</g>

        {/* chalk drawing — roughened as a group so the lines look hand-made */}
        <g filter="url(#rough)">
          {/* penalty box + arc */}
          <path
            className="pitch-line"
            d={`M120 ${VB_H} L120 ${MOUTH.B + 4} L780 ${MOUTH.B + 4} L780 ${VB_H}`}
            fill="none"
          />
          <path className="pitch-line" d={`M${SPOT.x - 132} ${MOUTH.B + 4} A 132 78 0 0 1 ${SPOT.x + 132} ${MOUTH.B + 4}`} fill="none" />
          <circle className="pitch-line" cx={SPOT.x} cy={SPOT.y} r="3.5" />

          {/* net + goal frame */}
          <g className="net">{net}</g>
          <path
            className="frame"
            d={`M${MOUTH.L} ${MOUTH.B} L${MOUTH.L} ${MOUTH.T} L${MOUTH.R} ${MOUTH.T} L${MOUTH.R} ${MOUTH.B}`}
            fill="none"
          />

          {/* target corners */}
          {zones.map((zone) => {
            const r = cell(zone.row, zone.col)
            const isSel = zone.key === selectedZone
            return (
              <g key={`o-${zone.key}`} className={`corner ${isSel ? 'corner--sel' : ''}`}>
                <rect x={r.x + 8} y={r.y + 8} width={r.w - 16} height={r.h - 16} rx="2" fill="none" />
                {isSel && (
                  <path
                    className="corner-x"
                    d={`M${r.cx - 13} ${r.cy - 13} L${r.cx + 13} ${r.cy + 13} M${r.cx + 13} ${r.cy - 13} L${r.cx - 13} ${r.cy + 13}`}
                  />
                )}
              </g>
            )
          })}
        </g>

        {/* keeper + ball sit above the chalk, drawn cleaner */}
        <Keeper diveZone={diveZoneObj} />
        <Ball phase={phase} shotZone={shotZoneObj} />

        {/* hit areas + quiet labels (crisp, not roughened) */}
        {zones.map((zone) => {
          const r = cell(zone.row, zone.col)
          return (
            <g
              key={`h-${zone.key}`}
              className={`hit ${interactive ? 'hit--live' : ''}`}
              onClick={() => interactive && onSelect?.(zone.key)}
            >
              <rect x={r.x} y={r.y} width={r.w} height={r.h} fill="transparent" />
              <text x={r.x + 12} y={r.y + 20} className="corner-tag">
                {zone.short}
              </text>
            </g>
          )
        })}

        {phase === 'result' && scored !== null && (
          <g className="verdict">
            <text x={VB_W / 2} y={MOUTH.T - 26} textAnchor="middle" className={scored ? 'verdict-goal' : 'verdict-save'}>
              {scored ? 'GOAL' : 'SAVED'}
            </text>
            <path
              className={scored ? 'verdict-rule verdict-rule--goal' : 'verdict-rule verdict-rule--save'}
              d={`M${VB_W / 2 - 66} ${MOUTH.T - 12} q 66 -10 132 0`}
            />
          </g>
        )}

        <rect x="0" y="0" width={VB_W} height={VB_H} filter="url(#grain)" className="board-grain" />
      </svg>
      <p className="board-caption">{mode === 'shoot' ? 'Pick your corner' : 'Pick your dive'}</p>
    </div>
  )
}
