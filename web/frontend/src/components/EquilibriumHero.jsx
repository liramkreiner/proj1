import { pct } from '../format'

// Zone label -> position in a 2x3 mini goal, and its short code.
const GRID = {
  'Top Left': [0, 0],
  'Top Center': [0, 1],
  'Top Right': [0, 2],
  'Bottom Left': [1, 0],
  'Bottom Center': [1, 1],
  'Bottom Right': [1, 2],
}
const SHORT = {
  'Top Left': 'TL',
  'Top Center': 'TC',
  'Top Right': 'TR',
  'Bottom Left': 'BL',
  'Bottom Center': 'BC',
  'Bottom Right': 'BR',
}

function MiniGoal({ title, entries, tone }) {
  const values = entries.map((e) => e.probability)
  const lo = Math.min(...values)
  const hi = Math.max(...values)
  const span = hi - lo || 1
  const ordered = [...entries].sort(
    (a, b) => GRID[a.label][0] - GRID[b.label][0] || GRID[a.label][1] - GRID[b.label][1],
  )
  return (
    <figure className="mini-goal">
      <figcaption>{title}</figcaption>
      <div className={`mg-grid mg-${tone}`}>
        {ordered.map((entry, i) => (
          <div
            key={entry.label}
            className="mg-cell"
            style={{ '--w': 0.16 + 0.84 * ((entry.probability - lo) / span), '--i': i }}
          >
            <span className="mg-code">{SHORT[entry.label]}</span>
            <span className="mg-pct">{pct(entry.probability, 0)}</span>
          </div>
        ))}
      </div>
    </figure>
  )
}

export default function EquilibriumHero({ equilibrium }) {
  return (
    <section className="eq-hero" aria-label="Optimal strategy at equilibrium">
      <div className="eq-goals">
        <MiniGoal title="Where the striker should aim" entries={equilibrium.shooter_strategy} tone="strike" />
        <MiniGoal title="Where the keeper should dive" entries={equilibrium.goalkeeper_strategy} tone="save" />
      </div>
      <div className="eq-value">
        <span>Game value</span>
        <strong>{pct(equilibrium.game_value)}</strong>
        <p>The striker's scoring rate when neither player misreads the odds.</p>
      </div>
    </section>
  )
}
