import { fixed, pct, SERIES } from '../format'
import BarChart from './BarChart'
import MatrixTable from './MatrixTable'
import StrategyBars from './StrategyBars'

export default function DashboardTab({ equilibrium }) {
  if (!equilibrium) return <p className="muted">Loading analysis…</p>

  const { payoff_matrix: matrix, pure_analysis: pure, validation } = equilibrium
  const saddle = pure.saddle_point ? { row: pure.saddle_point[0], col: pure.saddle_point[1] } : null

  const chartGroups = matrix.row_labels.map((label, i) => ({
    label: matrix.column_labels[i]?.replace('Bottom ', 'B ').replace('Top ', 'T ') ?? label,
    bars: [
      { name: 'Shooter', value: equilibrium.shooter_strategy[i].probability, color: SERIES.shooter },
      { name: 'Goalkeeper', value: equilibrium.goalkeeper_strategy[i].probability, color: SERIES.goalkeeper },
    ],
  }))

  return (
    <div className="tab-stack">
      <section className="card">
        <h3>Payoff matrix — P(score | shot, dive)</h3>
        <p className="muted">
          Entry A[i,j] is the shooter's payoff; the goalkeeper's payoff is −A[i,j], so the game is
          zero-sum. Row minima and column maxima drive the pure-strategy bounds.
        </p>
        <MatrixTable
          rowLabels={matrix.row_labels}
          columnLabels={matrix.column_labels}
          values={matrix.values}
          rowMinima={pure.row_minima}
          columnMaxima={pure.column_maxima}
          highlight={saddle}
        />
      </section>

      <div className="two-col">
        <section className="card">
          <h3>Pure-strategy analysis</h3>
          <div className="metric-grid">
            <div>
              <span>Maximin (shooter secures)</span>
              <strong>{fixed(pure.maximin)}</strong>
            </div>
            <div>
              <span>Minimax (keeper concedes)</span>
              <strong>{fixed(pure.minimax)}</strong>
            </div>
            <div>
              <span>Saddle point</span>
              <strong>
                {saddle
                  ? `${matrix.row_labels[saddle.row]} / ${matrix.column_labels[saddle.col]}`
                  : 'None'}
              </strong>
            </div>
          </div>
          <p className="muted">
            {pure.has_pure_equilibrium
              ? 'maximin = minimax ⇒ a pure-strategy equilibrium exists at the saddle point.'
              : `maximin (${fixed(pure.maximin, 2)}) ≠ minimax (${fixed(pure.minimax, 2)}) ⇒ no pure equilibrium — the players must randomise.`}
          </p>
        </section>

        <section className="card game-value-card">
          <span>Game value v</span>
          <strong>{pct(equilibrium.game_value)}</strong>
          <p className="muted">Optimal expected scoring probability under equilibrium play.</p>
        </section>
      </div>

      <section className="card">
        <h3>Mixed-strategy Nash equilibrium</h3>
        <div className="two-col">
          <StrategyBars
            title="Shooter strategy p"
            entries={equilibrium.shooter_strategy}
            color={SERIES.shooter}
          />
          <StrategyBars
            title="Goalkeeper strategy q"
            entries={equilibrium.goalkeeper_strategy}
            color={SERIES.goalkeeper}
          />
        </div>
        <BarChart groups={chartGroups} />
      </section>

      <section className="card">
        <h3>
          Equilibrium validation{' '}
          <span className={validation.valid ? 'pill pill-ok' : 'pill pill-bad'}>
            {validation.valid ? 'VALID' : 'INVALID'}
          </span>
        </h3>
        <ul className="check-list">
          {validation.messages.map((message) => (
            <li key={message}>{message}</li>
          ))}
        </ul>
      </section>
    </div>
  )
}
