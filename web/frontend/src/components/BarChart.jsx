import { pct } from '../format'

// Grouped vertical bar chart, pure SVG (no chart library).
// `groups`: [{ label, bars: [{ name, value, color }] }]
export default function BarChart({ groups, maxValue, height = 190, unit = 'pct' }) {
  const top = maxValue ?? Math.max(0.0001, ...groups.flatMap((g) => g.bars.map((b) => b.value)))
  const fmt = unit === 'pct' ? (v) => pct(v, 1) : (v) => v.toFixed(3)

  return (
    <div className="barchart">
      <div className="barchart-plot" style={{ height }}>
        {groups.map((group) => (
          <div className="barchart-group" key={group.label} title={group.label}>
            <div className="barchart-bars">
              {group.bars.map((bar) => (
                <div
                  key={bar.name}
                  className="barchart-bar"
                  style={{ height: `${(bar.value / top) * 100}%`, background: bar.color }}
                >
                  <span className="barchart-value">{fmt(bar.value)}</span>
                </div>
              ))}
            </div>
            <div className="barchart-label">{group.label}</div>
          </div>
        ))}
      </div>
      {groups[0]?.bars.length > 1 && (
        <div className="barchart-legend">
          {groups[0].bars.map((bar) => (
            <span key={bar.name}>
              <i style={{ background: bar.color }} /> {bar.name}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
