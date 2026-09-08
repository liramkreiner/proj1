import { useEffect, useState } from 'react'
import { api } from './api'
import DashboardTab from './components/DashboardTab'
import EquilibriumHero from './components/EquilibriumHero'
import ExperimentTab from './components/ExperimentTab'
import ExplanationTab from './components/ExplanationTab'
import PlayTab from './components/PlayTab'
import SimulationTab from './components/SimulationTab'

const TABS = [
  { id: 'play', label: 'Play' },
  { id: 'dashboard', label: 'Game theory' },
  { id: 'simulation', label: 'Simulation' },
  { id: 'experiment', label: 'Experiment' },
  { id: 'explain', label: 'The maths' },
]

export default function App() {
  const [tab, setTab] = useState('play')
  const [config, setConfig] = useState(null)
  const [equilibrium, setEquilibrium] = useState(null)
  const [baseEquilibrium, setBaseEquilibrium] = useState(null)
  const [activeMatrix, setActiveMatrix] = useState(null)
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
        <p className="boot boot-error">Couldn't reach the analysis engine. {error}</p>
      </div>
    )
  }
  if (!config || !equilibrium) {
    return (
      <div className="app">
        <p className="boot">Setting up the shootout…</p>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="masthead">
        <h1>Penalty shootout</h1>
        <p className="masthead-sub">
          A zero-sum game you can play: six corners, one guess each, taken at the same instant. The
          keeper's dive comes straight from the mixed-strategy Nash equilibrium of the payoff matrix.
        </p>
      </header>

      <EquilibriumHero equilibrium={equilibrium} />
      {activeMatrix !== null && (
        <p className="matrix-flag">You are playing a custom payoff matrix. Reset it in Experiment.</p>
      )}

      <nav className="tabbar" aria-label="Views">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            className={tab === entry.id ? 'active' : ''}
            onClick={() => setTab(entry.id)}
          >
            {entry.label}
          </button>
        ))}
      </nav>

      <main>
        {tab === 'play' && <PlayTab zones={config.zones} activeMatrix={activeMatrix} />}
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
        The striker maximises the chance of scoring, the keeper minimises it. Solved with{' '}
        <code>scipy.optimize.linprog</code> and checked against the minimax conditions on every run.
      </footer>
    </div>
  )
}
