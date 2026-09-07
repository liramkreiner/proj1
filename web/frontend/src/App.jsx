import { useEffect, useState } from 'react'
import { api } from './api'
import DashboardTab from './components/DashboardTab'
import ExperimentTab from './components/ExperimentTab'
import ExplanationTab from './components/ExplanationTab'
import PlayTab from './components/PlayTab'
import SimulationTab from './components/SimulationTab'

const TABS = [
  { id: 'play', label: 'Shootout' },
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
      <div className="page">
        <p className="boot boot-error">Couldn't reach the analysis engine. {error}</p>
      </div>
    )
  }
  if (!config || !equilibrium) {
    return (
      <div className="page">
        <p className="boot">Chalking the board…</p>
      </div>
    )
  }

  return (
    <div className="page">
      <header className="masthead">
        <h1>Penalty&nbsp;Kick</h1>
        <p>
          A penalty is close to a coin&#8209;flip. Game theory decides where to put it, and the
          striker&rsquo;s real job is to stay unreadable.
        </p>
      </header>

      <nav className="tabs">
        {TABS.map((entry) => (
          <button
            key={entry.id}
            type="button"
            className={tab === entry.id ? 'on' : ''}
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

      <footer className="colophon">
        The striker maximises the chance of scoring, the keeper minimises it. Solved as a zero&#8209;sum
        game with <code>scipy.optimize.linprog</code>, every strategy checked against the minimax
        conditions.
      </footer>
    </div>
  )
}
