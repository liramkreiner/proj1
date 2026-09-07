import { fixed } from '../format'

// Payoff matrix as a table. Read-only by default; when `onChange` is supplied
// every cell becomes a number input (Experiment mode).
// `highlight`: optional { row, col } saddle point to mark.
export default function MatrixTable({
  rowLabels,
  columnLabels,
  values,
  rowMinima,
  columnMaxima,
  highlight,
  onChange,
}) {
  const editable = typeof onChange === 'function'

  return (
    <div className="matrix-scroll">
      <table className="matrix-table">
        <thead>
          <tr>
            <th className="corner">Shot ＼ Dive</th>
            {columnLabels.map((label) => (
              <th key={label}>{label}</th>
            ))}
            {rowMinima && <th className="edge">row min</th>}
          </tr>
        </thead>
        <tbody>
          {values.map((row, r) => (
            <tr key={rowLabels[r]}>
              <th scope="row">{rowLabels[r]}</th>
              {row.map((value, c) => {
                const isSaddle = highlight && highlight.row === r && highlight.col === c
                return (
                  <td key={c} className={isSaddle ? 'saddle' : undefined}>
                    {editable ? (
                      <input
                        type="number"
                        min={0}
                        max={1}
                        step={0.05}
                        value={value}
                        onChange={(event) => onChange(r, c, event.target.value)}
                        aria-label={`${rowLabels[r]} vs ${columnLabels[c]}`}
                      />
                    ) : (
                      fixed(value, 2)
                    )}
                  </td>
                )
              })}
              {rowMinima && <td className="edge">{fixed(rowMinima[r], 2)}</td>}
            </tr>
          ))}
          {columnMaxima && (
            <tr>
              <th scope="row" className="edge">
                col max
              </th>
              {columnMaxima.map((value, c) => (
                <td key={c} className="edge">
                  {fixed(value, 2)}
                </td>
              ))}
              <td className="edge" />
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
