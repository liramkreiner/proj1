import { pct } from '../format'

// Horizontal probability bars for one player's mixed strategy.
export default function StrategyBars({ title, entries, color }) {
  return (
    <div className="strategy-bars">
      <h4>{title}</h4>
      {entries.map((entry) => (
        <div className="strategy-row" key={entry.label}>
          <span className="strategy-name">{entry.label}</span>
          <div className="strategy-track">
            <div
              className="strategy-fill"
              style={{ width: `${Math.max(entry.probability * 100, 0.5)}%`, background: color }}
            />
          </div>
          <span className="strategy-pct">{pct(entry.probability)}</span>
        </div>
      ))}
    </div>
  )
}
