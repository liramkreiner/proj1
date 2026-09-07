import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { pct } from '../format'
import GoalField from './GoalField'

const IDLE_STATE = {
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

export default function PlayTab({ zones, activeMatrix }) {
  const [role, setRole] = useState('Shooter')
  const [state, setState] = useState(IDLE_STATE)
  const [phase, setPhase] = useState('idle') // idle | shooting | result
  const [selected, setSelected] = useState(null)
  const [lastTurn, setLastTurn] = useState(null)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const timers = useRef([])

  const clearTimers = () => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }

  const newMatch = useCallback(
    async (nextRole) => {
      clearTimers()
      setBusy(true)
      setError(null)
      setPhase('idle')
      setSelected(null)
      setLastTurn(null)
      try {
        const session = await api.startSession({ role: nextRole, values: activeMatrix })
        setState(session)
      } catch (err) {
        setError(err.message)
      } finally {
        setBusy(false)
      }
    },
    [activeMatrix],
  )

  useEffect(() => {
    newMatch(role)
    return clearTimers
  }, [role, newMatch])

  async function pickZone(key) {
    if (busy || phase !== 'idle' || state.finished || !state.session_id) return
    const zone = zones.find((z) => z.key === key)
    setSelected(key)
    setPhase('shooting')
    setBusy(true)
    setError(null)

    timers.current.push(
      setTimeout(async () => {
        try {
          const turn = await api.playTurn(state.session_id, zone.label)
          setLastTurn(turn)
          setState(turn.state)
          setPhase('result')
          if (!turn.finished) {
            timers.current.push(
              setTimeout(() => {
                setPhase('idle')
                setSelected(null)
                setBusy(false)
              }, 1500),
            )
          } else {
            setBusy(false)
          }
        } catch (err) {
          setError(err.message)
          setPhase('idle')
          setSelected(null)
          setBusy(false)
        }
      }, 380),
    )
  }

  const keeperKey = lastTurn
    ? zones.find((z) => z.label === lastTurn.goalkeeper_zone)?.key ?? null
    : null
  const ballKey = lastTurn ? zones.find((z) => z.label === lastTurn.shooter_zone)?.key ?? null : null
  const showBallKey = role === 'Shooter' ? (phase === 'idle' ? selected : ballKey) : ballKey

  return (
    <div className="tab-grid play-grid">
      <section className="card">
        <GoalField
          zones={zones}
          mode={role === 'Shooter' ? 'shoot' : 'dive'}
          selectedKey={selected}
          onSelect={pickZone}
          disabled={busy || phase !== 'idle' || state.finished}
          keeperKey={phase === 'result' ? keeperKey : null}
          ballKey={showBallKey}
          phase={phase}
          scored={phase === 'result' && lastTurn ? lastTurn.scored : null}
        />
        {error && <p className="error-banner">{error}</p>}
      </section>

      <aside className="card side-panel">
        <div className="scorebar">
          <div>
            <span>Penalty</span>
            <strong>
              {Math.min(state.rounds_played + (state.finished ? 0 : 1), Math.max(state.rounds_played, state.total_rounds))} / {state.total_rounds}
            </strong>
          </div>
          <div>
            <span>You</span>
            <strong>{state.user_score}</strong>
          </div>
          <div>
            <span>AI</span>
            <strong>{state.ai_score}</strong>
          </div>
        </div>

        <div className={`status-line ${state.sudden_death ? 'hot' : ''}`}>
          {state.finished
            ? state.winner
              ? `Full time — ${state.winner === 'You' ? 'You win' : 'AI wins'}`
              : 'Full time — tied'
            : state.sudden_death
              ? 'Sudden death'
              : `Playing as ${role}`}
        </div>

        <div className="result-block">
          <h4>Last penalty</h4>
          {lastTurn ? (
            <dl>
              <div>
                <dt>Shot</dt>
                <dd>{lastTurn.shooter_zone}</dd>
              </div>
              <div>
                <dt>Goalkeeper</dt>
                <dd>{lastTurn.goalkeeper_zone}</dd>
              </div>
              <div>
                <dt>Scoring probability</dt>
                <dd>{pct(lastTurn.scoring_probability)}</dd>
              </div>
              <div>
                <dt>Outcome</dt>
                <dd className={lastTurn.scored ? 'goal-text' : 'save-text'}>
                  {lastTurn.scored ? 'GOAL' : 'SAVED'}
                </dd>
              </div>
            </dl>
          ) : (
            <p className="muted">No penalty taken yet. Pick a zone in the goal.</p>
          )}
        </div>

        <div className="button-row">
          <button
            type="button"
            onClick={() => setRole(role === 'Shooter' ? 'Goalkeeper' : 'Shooter')}
            disabled={busy}
          >
            Play as {role === 'Shooter' ? 'Goalkeeper' : 'Shooter'}
          </button>
          <button type="button" className="primary" onClick={() => newMatch(role)} disabled={busy}>
            New match
          </button>
        </div>

        <p className="fine-print">
          The AI samples its zone from the mixed-strategy Nash equilibrium of the current payoff
          matrix — it is deliberately unpredictable, not greedy.
        </p>
      </aside>
    </div>
  )
}
