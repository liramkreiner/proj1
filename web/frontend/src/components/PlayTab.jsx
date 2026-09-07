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

// phase: idle -> windup -> flight -> result -> idle
const WINDUP_MS = 300
const FLIGHT_MS = 680
const RESULT_MS = 1250

export default function PlayTab({ zones, activeMatrix = null }) {
  const [role, setRole] = useState('Shooter')
  const [state, setState] = useState(IDLE_STATE)
  const [phase, setPhase] = useState('idle')
  const [selected, setSelected] = useState(null)
  const [lastTurn, setLastTurn] = useState(null)
  const [history, setHistory] = useState([])
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const timers = useRef([])

  const clearTimers = () => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }
  const later = (fn, ms) => timers.current.push(setTimeout(fn, ms))

  const newMatch = useCallback(
    async (nextRole) => {
      clearTimers()
      setBusy(true)
      setError(null)
      setPhase('idle')
      setSelected(null)
      setLastTurn(null)
      setHistory([])
      try {
        setState(await api.startSession({ role: nextRole, values: activeMatrix }))
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
    setPhase('windup')
    setBusy(true)
    setError(null)

    later(async () => {
      try {
        const turn = await api.playTurn(state.session_id, zone.label)
        setLastTurn(turn)
        setState(turn.state)
        setHistory((h) => [turn, ...h].slice(0, 6))
        setPhase('flight')
        later(() => setPhase('result'), FLIGHT_MS)
        later(
          () => {
            if (!turn.finished) {
              setPhase('idle')
              setSelected(null)
            }
            setBusy(false)
          },
          FLIGHT_MS + RESULT_MS,
        )
      } catch (err) {
        setError(err.message)
        setPhase('idle')
        setSelected(null)
        setBusy(false)
      }
    }, WINDUP_MS)
  }

  const keyOf = (label) => zones.find((z) => z.label === label)?.key ?? null
  const revealed = phase === 'flight' || phase === 'result'
  const shotZone = revealed
    ? role === 'Shooter'
      ? selected
      : keyOf(lastTurn?.shooter_zone)
    : null
  const diveZone = revealed
    ? role === 'Goalkeeper'
      ? selected
      : keyOf(lastTurn?.goalkeeper_zone)
    : null

  const penaltyLabel = state.sudden_death
    ? `Sudden death · kick ${state.rounds_played + 1}`
    : `Penalty ${Math.min(state.rounds_played + (state.finished ? 0 : 1), state.total_rounds)} / ${state.total_rounds}`

  return (
    <div className="tab-grid play-grid">
      <section className="card scene-card">
        <GoalField
          zones={zones}
          mode={role === 'Shooter' ? 'shoot' : 'dive'}
          selectedZone={selected}
          onSelect={pickZone}
          interactive={phase === 'idle' && !state.finished && !busy}
          phase={phase}
          shotZone={shotZone}
          diveZone={diveZone}
          scored={phase === 'result' && lastTurn ? lastTurn.scored : null}
        />
        {error && <p className="error-banner">{error}</p>}
      </section>

      <aside className="side-column">
        <div className="card scoreboard">
          <div className="score-team">
            <span>{role === 'Shooter' ? 'You (kicker)' : 'You (keeper)'}</span>
            <strong>{state.user_score}</strong>
          </div>
          <div className="score-sep">
            <em>{penaltyLabel}</em>
            <span>vs</span>
          </div>
          <div className="score-team">
            <span>AI</span>
            <strong>{state.ai_score}</strong>
          </div>
        </div>

        <div className={`card status-line ${state.sudden_death ? 'hot' : ''} ${state.finished ? 'done' : ''}`}>
          {state.finished
            ? state.winner
              ? state.winner === 'You'
                ? '🏆 You win the shootout'
                : 'AI wins the shootout'
              : 'Shootout tied'
            : phase === 'windup'
              ? 'Run-up…'
              : phase === 'flight'
                ? 'Struck!'
                : phase === 'result' && lastTurn
                  ? lastTurn.scored
                    ? 'GOAL'
                    : 'Saved'
                  : role === 'Shooter'
                    ? 'Pick a target zone'
                    : 'Pick a dive zone'}
        </div>

        <div className="card result-block">
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
                <dt>Scoring chance</dt>
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
            <p className="muted">No penalty taken yet.</p>
          )}
          {history.length > 1 && (
            <div className="shot-strip">
              {history.map((turn, i) => (
                <span
                  key={history.length - i}
                  className={turn.scored ? 'dot dot-goal' : 'dot dot-save'}
                  title={`${turn.shooter_zone} vs ${turn.goalkeeper_zone}`}
                />
              ))}
            </div>
          )}
        </div>

        <div className="card button-row">
          <button
            type="button"
            onClick={() => setRole(role === 'Shooter' ? 'Goalkeeper' : 'Shooter')}
            disabled={busy}
          >
            Switch to {role === 'Shooter' ? 'keeper' : 'kicker'}
          </button>
          <button type="button" className="primary" onClick={() => newMatch(role)} disabled={busy}>
            New match
          </button>
        </div>

        <p className="fine-print">
          The AI draws its zone from the mixed-strategy Nash equilibrium of the current payoff matrix
          — deliberately unpredictable, never greedy.
        </p>
      </aside>
    </div>
  )
}
