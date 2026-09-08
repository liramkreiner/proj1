import { useState } from 'react'
import { api } from '../api'
import { fixed, pct, SERIES } from '../format'
import MatrixTable from './MatrixTable'
import StrategyBars from './StrategyBars'

export default function ExperimentTab({ baseEquilibrium, defaultValues, onApply }) {
  const [draft, setDraft] = useState(() => defaultValues.map((row) => [...row]))
  const [result, setResult] = useState(baseEquilibrium)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [applied, setApplied] = useState(true)

  function editCell(r, c, raw) {
    const value = raw === '' ? 0 : Number(raw)
    setDraft((prev) => {
      const next = prev.map((row) => [...row])
      next[r][c] = value
      return next
    })
    setApplied(false)
  }

  async function recalc() {
    setBusy(true)
    setError(null)
    try {
      const equilibrium = await api.analyze(draft)
      setResult(equilibrium)
      onApply(draft, equilibrium)
      setApplied(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function resetDefault() {
    const copy = defaultValues.map((row) => [...row])
    setDraft(copy)
    setResult(baseEquilibrium)
    onApply(null, baseEquilibrium)
    setApplied(true)
    setError(null)
  }

  const pure = result?.pure_analysis
  const saddle = pure?.saddle_point ? { row: pure.saddle_point[0], col: pure.saddle_point[1] } : null

  return (
    <div className="tab-stack">
      <section className="card">
        <h3>Edit the payoff matrix</h3>
        <p className="muted">
          Change any scoring probabilities (0–1), then recalculate. The solver is generic: it
          re-runs the same linear program, re-detects saddle points, and the Play-tab AI immediately
          adopts the new equilibrium strategy.
        </p>
        <MatrixTable
          rowLabels={result.payoff_matrix.row_labels}
          columnLabels={result.payoff_matrix.column_labels}
          values={draft}
          onChange={editCell}
        />
        <div className="button-row">
          <button type="button" className="primary" onClick={recalc} disabled={busy}>
            {busy ? 'Solving…' : 'Recalculate equilibrium'}
          </button>
          <button type="button" onClick={resetDefault} disabled={busy}>
            Reset to default
          </button>
          <span className={applied ? 'pill pill-ok' : 'pill pill-warn'}>
            {applied ? 'AI is using this matrix' : 'Unsaved edits — recalculate to apply'}
          </span>
        </div>
        {error && <p className="error-banner">{error}</p>}
      </section>

      {result && (
        <div className="two-col">
          <section className="card">
            <h4>Recalculated analysis</h4>
            <div className="metric-grid">
              <div>
                <span>Maximin</span>
                <strong>{fixed(pure.maximin)}</strong>
              </div>
              <div>
                <span>Minimax</span>
                <strong>{fixed(pure.minimax)}</strong>
              </div>
              <div>
                <span>Saddle point</span>
                <strong>
                  {saddle
                    ? `${result.payoff_matrix.row_labels[saddle.row]} / ${result.payoff_matrix.column_labels[saddle.col]}`
                    : 'None'}
                </strong>
              </div>
              <div>
                <span>Game value</span>
                <strong>{pct(result.game_value)}</strong>
              </div>
            </div>
            <p className={result.validation.valid ? 'pill pill-ok' : 'pill pill-bad'}>
              {result.validation.valid ? 'Equilibrium validated' : 'Validation failed'}
            </p>
          </section>

          <section className="card">
            <h4>New equilibrium strategies</h4>
            <StrategyBars
              title="Shooter p"
              entries={result.shooter_strategy}
              color={SERIES.shooter}
            />
            <StrategyBars
              title="Goalkeeper q"
              entries={result.goalkeeper_strategy}
              color={SERIES.goalkeeper}
            />
          </section>
        </div>
      )}
    </div>
  )
}
