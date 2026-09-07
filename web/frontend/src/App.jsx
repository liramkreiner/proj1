import { useEffect, useState } from 'react'
import { api } from './api'
import { pct } from './format'
import DashboardTab from './components/DashboardTab'
import ExperimentTab from './components/ExperimentTab'
import ExplanationTab from './components/ExplanationTab'
import PlayTab from './components/PlayTab'
import SimulationTab from './components/SimulationTab'

const TABS = [
  { id: 'play', label: 'Play' },
  { id: 'dashboard', label: 'Game Theory' },
  { id: 'simulation', label: 'Simulation' },
  { id: 'experiment', label: 'Experiment' },
  { id: 'explain', label: 'Explanation' },
]

export default function App() {
  const [tab, setTab] = useState('play')
  const [config, setConfig] = useState(null)
  const [equilibrium, setEquilibrium] = useState(null) // analysis for the ACTIVE matrix
  const [baseEquilibrium, setBaseEquilibrium] = useState(null) // default matrix analysis
  const [activeMatrix, setActiveMatrix] = useState(null) // null => backend default
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([api.config(), api.equilibrium()])
      .then(([cfg, eq]) => {
        setConfig(cfg)
        setEquilibrium(eq)
        setBaseEquilibrium(eq)
      })
      .catch((err) => setError(err.message))
  }, [])

  function applyMatrix(values, newEquilibrium) {
    setActiveMatrix(values)
    setEquilibrium(newEquilibrium)
  }

  if (error) {
    return (
      <div className="app">
        <div className="card error-banner">Could not start: {error}</div>
      </div>
    )
  }

  if (!config || !equilibrium) {
    return (
      <div className="app">
        <div className="card muted">Loading the game-theory engine…</div>
      </div>
    )
  }

  const zones = config.zones
  const customActive = activeMatrix !== null

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <p className="eyebrow">Zero-sum game · mixed-strategy Nash equilibrium</p>
          <h1>Tactical Penalty Shootout Simulator</h1>
        </div>
        <div className="header-value">
          <span>Game value</span>
          <strong>{pct(equilibrium.game_value)}</strong>
          {customActive && <em>custom matrix</em>}
        </div>
      </header>

      <nav className="tabbar">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            className={tab === entry.id ? 'active' : ''}
            onClick={() => setTab(entry.id)}
            type="button"
          >
            {entry.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'play' && <PlayTab zones={zones} activeMatrix={activeMatrix} />}
        {tab === 'dashboard' && <DashboardTab equilibrium={equilibrium} />}
        {tab === 'simulation' && <SimulationTab activeMatrix={activeMatrix} config={config} />}
        {tab === 'experiment' && (
          <ExperimentTab
            baseEquilibrium={baseEquilibrium}
            defaultValues={baseEquilibrium.payoff_matrix.values}
            onApply={applyMatrix}
          />
        )}
        {tab === 'explain' && <ExplanationTab equilibrium={equilibrium} />}
      </main>

      <footer className="app-footer">
        Shooter maximises P(score); goalkeeper minimises it. Solver: <code>scipy.optimize.linprog</code>{' '}
        (HiGHS). All strategies validated against the minimax conditions.
      </footer>
    </div>
  )
}
