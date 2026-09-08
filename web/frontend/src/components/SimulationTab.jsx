import { useState } from 'react'
import { api } from '../api'
import { fixed, pct, SERIES } from '../format'
import BarChart from './BarChart'

const PRESETS = [100, 1000, 10000, 100000]

export default function SimulationTab({ activeMatrix, config }) {
  const [games, setGames] = useState(config?.default_monte_carlo_games ?? 10000)
  const [seed, setSeed] = useState('')
  const [result, setResult] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  async function run() {
    setRunning(true)
    setError(null)
    try {
      const payload = await api.simulate({
        values: activeMatrix,
        games: Number(games),
        seed: seed === '' ? null : Number(seed),
      })
      setResult(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setRunning(false)
    }
  }

  const toGroups = (rows) =>
    rows.map((row) => ({
      label: row.label.replace('Bottom ', 'B ').replace('Top ', 'T '),
      bars: [
        { name: 'Theoretical', value: row.theoretical, color: SERIES.theoretical },
        { name: 'Empirical', value: row.empirical, color: SERIES.empirical },
      ],
    }))

  return (
    <div className="tab-stack">
      <section className="card">
        <h3>Monte Carlo simulation</h3>
        <p className="muted">
          Both players sample their equilibrium mixed strategies for every penalty. By the law of
          large numbers the observed scoring rate must approach the game value v, and the observed
          action frequencies must approach p and q.
        </p>
        <div className="sim-controls">
          <label>
            Number of penalties
            <input
              type="number"
              min={1}
              max={config?.max_monte_carlo_games ?? 2000000}
              value={games}
              onChange={(event) => setGames(event.target.value)}
            />
          </label>
          <label>
            Seed (optional)
            <input
              type="number"
              placeholder="random"
              value={seed}
              onChange={(event) => setSeed(event.target.value)}
            />
          </label>
          <div className="preset-row">
            {PRESETS.map((value) => (
              <button key={value} type="button" onClick={() => setGames(value)}>
                {value.toLocaleString()}
              </button>
            ))}
          </div>
          <button type="button" className="primary" onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run simulation'}
          </button>
        </div>
        {error && <p className="error-banner">{error}</p>}
      </section>

      {result && (
        <>
          <section className="card">
            <div className="metric-grid big">
              <div>
                <span>Theoretical game value</span>
                <strong>{fixed(result.theoretical_value)}</strong>
              </div>
              <div>
                <span>Observed scoring rate</span>
                <strong>{fixed(result.observed_scoring_rate)}</strong>
              </div>
              <div>
                <span>Absolute error</span>
                <strong>{fixed(result.absolute_error)}</strong>
              </div>
              <div>
                <span>Penalties simulated</span>
                <strong>{result.games.toLocaleString()}</strong>
              </div>
            </div>
          </section>

          <div className="two-col">
            <section className="card">
              <h4>
                Shooter: theoretical vs empirical{' '}
                <span className="muted">(L1 error {fixed(result.shooter_l1_error)})</span>
              </h4>
              <BarChart groups={toGroups(result.shooter)} />
            </section>
            <section className="card">
              <h4>
                Goalkeeper: theoretical vs empirical{' '}
                <span className="muted">(L1 error {fixed(result.goalkeeper_l1_error)})</span>
              </h4>
              <BarChart groups={toGroups(result.goalkeeper)} />
            </section>
          </div>
          <p className="muted center">
            Increase the penalty count and the empirical bars converge onto the theoretical bars. The
            AI's behaviour is the equilibrium distribution, observed in aggregate.
          </p>
        </>
      )}
    </div>
  )
}
