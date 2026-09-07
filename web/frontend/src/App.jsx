import { useEffect, useMemo, useState } from 'react'

const ZONES = [
  { key: 'TOP_LEFT', short: 'TL', label: 'Top Left', row: 0, col: 0 },
  { key: 'TOP_CENTER', short: 'TC', label: 'Top Center', row: 0, col: 1 },
  { key: 'TOP_RIGHT', short: 'TR', label: 'Top Right', row: 0, col: 2 },
  { key: 'BOTTOM_LEFT', short: 'BL', label: 'Bottom Left', row: 1, col: 0 },
  { key: 'BOTTOM_CENTER', short: 'BC', label: 'Bottom Center', row: 1, col: 1 },
  { key: 'BOTTOM_RIGHT', short: 'BR', label: 'Bottom Right', row: 1, col: 2 },
]

const defaultState = {
  session_id: null,
  role: 'Shooter',
  rounds_played: 0,
  total_rounds: 5,
  user_score: 0,
  ai_score: 0,
  finished: false,
  winner: null,
  sudden_death: false,
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`
}

function zoneByKey(key) {
  return ZONES.find((zone) => zone.key === key) ?? ZONES[1]
}

function App() {
  const [session, setSession] = useState(defaultState)
  const [equilibrium, setEquilibrium] = useState(null)
  const [activeTab, setActiveTab] = useState('play')
  const [status, setStatus] = useState('Loading match...')
  const [selectedZone, setSelectedZone] = useState(null)
  const [hoveredZone, setHoveredZone] = useState(null)
  const [turnState, setTurnState] = useState('idle')
  const [lastTurn, setLastTurn] = useState(null)
  const [busy, setBusy] = useState(false)

  const matrix = equilibrium?.payoff_matrix

  useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      try {
        const [equilibriumResponse, sessionResponse] = await Promise.all([
          fetch('/api/equilibrium').then((response) => response.json()),
          fetch('/api/sessions', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role: 'Shooter' }),
          }).then((response) => response.json()),
        ])

        if (!cancelled) {
          setEquilibrium(equilibriumResponse)
          setSession(sessionResponse)
          setStatus('Kickoff ready')
        }
      } catch (error) {
        if (!cancelled) {
          setStatus(`Failed to load application: ${error.message}`)
        }
      }
    }

    bootstrap()
    return () => {
      cancelled = true
    }
  }, [])

  async function resetSession(role = session.role) {
    if (!session.session_id || busy) {
      return
    }

    setBusy(true)
    setTurnState('idle')
    setSelectedZone(null)
    setHoveredZone(null)
    setLastTurn(null)

    try {
      const response = await fetch(`/api/sessions/${session.session_id}/reset`, { method: 'POST' })
      const data = await response.json()
      setSession(data)
      setStatus(`New match started as ${role}`)
    } finally {
      setBusy(false)
    }
  }

  async function startRole(role) {
    if (busy) {
      return
    }

    setBusy(true)
    setTurnState('idle')
    setSelectedZone(null)
    setHoveredZone(null)
    setLastTurn(null)

    try {
      const response = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role }),
      })
      const data = await response.json()
      setSession(data)
      setStatus(`Playing as ${role}`)
    } finally {
      setBusy(false)
    }
  }

  async function playZone(zone) {
    if (!session.session_id || session.finished || busy) {
      return
    }

    setBusy(true)
    setSelectedZone(zone.key)
    setHoveredZone(zone.key)
    setTurnState('windup')
    setStatus('Run-up...')

    await sleep(280)

    try {
      setTurnState('strike')
      const response = await fetch(`/api/sessions/${session.session_id}/turn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ zone: zone.label }),
      })
      const data = await response.json()

      setSession(data.state)
      setLastTurn(data)
      setTurnState(data.scored ? 'goal' : 'save')
      setStatus(data.status_message)

      await sleep(500)

      if (data.finished) {
        setTurnState('final')
        setHoveredZone(null)
      } else {
        setTurnState('idle')
        setHoveredZone(zone.key)
      }
    } finally {
      setBusy(false)
    }
  }

  const analysisLines = useMemo(() => {
    if (!equilibrium) {
      return []
    }

    return [
      `Maximin: ${equilibrium.maximin.toFixed(3)}`,
      `Minimax: ${equilibrium.minimax.toFixed(3)}`,
      `Saddle point: ${equilibrium.saddle_point ? equilibrium.saddle_point.join(', ') : 'None'}`,
      `Game value: ${formatPercent(equilibrium.game_value)}`,
    ]
  }, [equilibrium])

  const activeShot = selectedZone ? zoneByKey(selectedZone) : null
  const keeperZone = lastTurn ? zoneByKey(lastTurn.ai_zone.replace(/ /g, '_').toUpperCase()) : null
  const highlightedZone = hoveredZone ? zoneByKey(hoveredZone) : null

  return (
    <div className="app-shell penalty-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Penalty Shootout Simulator</p>
          <h1>Penalty Shot</h1>
          <p className="subhead">A simple school project about mixed strategy decision making in a penalty shootout.</p>
        </div>

        <div className="scoreboard">
          <div>
            <span>Round</span>
            <strong>{session.rounds_played} / {session.total_rounds}</strong>
          </div>
          <div>
            <span>You</span>
            <strong>{session.user_score}</strong>
          </div>
          <div>
            <span>AI</span>
            <strong>{session.ai_score}</strong>
          </div>
        </div>
      </header>

      <nav className="tabs">
        <button className={activeTab === 'play' ? 'active' : ''} onClick={() => setActiveTab('play')}>Match</button>
        <button className={activeTab === 'theory' ? 'active' : ''} onClick={() => setActiveTab('theory')}>Theory</button>
      </nav>

      {activeTab === 'play' ? (
        <section className="main-grid">
          <div className="scene-card">
            <div className="scene-head">
              <div>
                <p className="panel-kicker">Live match</p>
                <h2>{session.role === 'Shooter' ? 'Choose a target' : 'Choose a save'}</h2>
              </div>
              <div className="panel-badges">
                <span className="badge">{session.role}</span>
                <span className={`badge ${session.sudden_death ? 'badge-hot' : ''}`}>{session.sudden_death ? 'Sudden death' : 'Normal time'}</span>
              </div>
            </div>

            <div className="penalty-scene">
              <div className="field-shadow" aria-hidden="true" />
              <div className="penalty-spot" aria-hidden="true" />

              <div className="shooter-area" aria-hidden="true">
                <div className={`shooter-dot ${turnState === 'windup' ? 'shooting' : ''}`} />
                <div className="shooter-leg" />
              </div>

              <div className="ball-wrap" aria-hidden="true">
                <div
                  className={`ball ${selectedZone ? `ball-${selectedZone}` : 'ball-center'} ${turnState}`}
                  data-result={lastTurn?.scored ? 'goal' : 'save'}
                />
              </div>

              <div className="goal-box">
                <div className="goal-post goal-post-left" aria-hidden="true" />
                <div className="goal-post goal-post-right" aria-hidden="true" />
                <div className="goal-bar" aria-hidden="true" />
                <div className="goal-net" aria-hidden="true" />

                <div className="zone-grid">
                  {ZONES.map((zone) => (
                    <button
                      key={zone.key}
                      className={`zone zone-${zone.row}-${zone.col} ${selectedZone === zone.key ? 'selected' : ''} ${hoveredZone === zone.key ? 'hovered' : ''}`}
                      onClick={() => playZone(zone)}
                      disabled={session.finished || busy}
                      aria-label={zone.label}
                      onMouseEnter={() => setHoveredZone(zone.key)}
                      onMouseLeave={() => setHoveredZone(selectedZone)}
                    >
                      <span className="zone-code">{zone.short}</span>
                    </button>
                  ))}
                </div>

                <div className={`keeper-dot ${keeperZone ? `keeper-${keeperZone.key}` : 'keeper-center'} ${turnState === 'save' ? 'keeper-dive' : ''} ${turnState === 'goal' ? 'keeper-miss' : ''}`} aria-hidden="true" />
                <div className={`zone-glow ${highlightedZone ? `zone-glow-${highlightedZone.key}` : ''}`} aria-hidden="true" />
              </div>

              <div className="scene-status">
                <span>Penalty spot</span>
                <strong>{status}</strong>
              </div>
            </div>
          </div>

          <aside className="side-column">
            <div className="info-card">
              <div className="panel-header compact">
                <div>
                  <p className="panel-kicker">Match status</p>
                  <h2>{session.finished ? (session.winner ? `${session.winner} wins` : 'Match tied') : 'Still in play'}</h2>
                </div>
              </div>

              <div className="info-list">
                <div><span>Role</span><strong>{session.role}</strong></div>
                <div><span>Last call</span><strong>{status}</strong></div>
                <div><span>Winner</span><strong>{session.winner ?? '—'}</strong></div>
              </div>

              <div className="controls">
                <button onClick={() => startRole(session.role === 'Shooter' ? 'Goalkeeper' : 'Shooter')} disabled={busy}>Switch Side</button>
                <button onClick={() => resetSession(session.role)} disabled={busy}>New Match</button>
              </div>
            </div>

            <div className="info-card">
              <div className="panel-header compact">
                <div>
                  <p className="panel-kicker">Last play</p>
                  <h2>{lastTurn ? (lastTurn.scored ? 'Goal' : 'Saved') : 'No shot yet'}</h2>
                </div>
              </div>

              {lastTurn ? (
                <div className="result-grid">
                  <div><span>Shot</span><strong>{lastTurn.user_zone}</strong></div>
                  <div><span>Keeper</span><strong>{lastTurn.ai_zone}</strong></div>
                  <div><span>Chance</span><strong>{formatPercent(lastTurn.scoring_probability)}</strong></div>
                  <div><span>Outcome</span><strong>{lastTurn.scored ? 'GOAL' : 'SAVED'}</strong></div>
                </div>
              ) : (
                <p className="muted-copy">Pick one target zone. The penalty scene stays focused on the kick, the save, and the result.</p>
              )}
            </div>
          </aside>
        </section>
      ) : (
        <section className="theory-grid">
          <div className="info-card">
            <div className="panel-header compact">
              <div>
                <p className="panel-kicker">Payoff matrix</p>
                <h2>Scoring probabilities</h2>
              </div>
            </div>

            <div className="matrix-wrap">
              {matrix ? (
                <table className="matrix">
                  <thead>
                    <tr>
                      <th></th>
                      {matrix.column_labels.map((label) => <th key={label}>{label}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {matrix.values.map((row, rowIndex) => (
                      <tr key={matrix.row_labels[rowIndex]}>
                        <th>{matrix.row_labels[rowIndex]}</th>
                        {row.map((value, colIndex) => <td key={`${rowIndex}-${colIndex}`}>{value.toFixed(2)}</td>)}
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}
            </div>
          </div>

          <div className="info-card">
            <div className="panel-header compact">
              <div>
                <p className="panel-kicker">Strategy summary</p>
                <h2>Equilibrium</h2>
              </div>
            </div>

            <div className="stat-stack">
              {analysisLines.map((line) => <div key={line}>{line}</div>)}
            </div>

            <div className="strategy-columns">
              <div>
                <h3>Shooter</h3>
                {equilibrium?.shooter_strategy.map((value, index) => (
                  <div className="bar-row" key={`s-${index}`}>
                    <span>{matrix?.row_labels[index] ?? ZONES[index].short}</span>
                    <div className="bar"><div style={{ width: `${value * 100}%` }} /></div>
                    <strong>{formatPercent(value)}</strong>
                  </div>
                ))}
              </div>

              <div>
                <h3>Goalkeeper</h3>
                {equilibrium?.goalkeeper_strategy.map((value, index) => (
                  <div className="bar-row" key={`g-${index}`}>
                    <span>{matrix?.column_labels[index] ?? ZONES[index].short}</span>
                    <div className="bar"><div style={{ width: `${value * 100}%` }} /></div>
                    <strong>{formatPercent(value)}</strong>
                  </div>
                ))}
              </div>
            </div>

            <div className="result-card">
              <h3>Validation</h3>
              <p>{equilibrium?.valid ? 'Equilibrium validated within numerical tolerance.' : 'Validation failed.'}</p>
            </div>
          </div>
        </section>
      )}
    </div>
  )
}

export default App
