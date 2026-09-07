import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { pct } from '../format'
import GoalField from './GoalField'

const WINDUP_MS = 320
const FLIGHT_MS = 700

const EMPTY_RECORD = { hits: 0, total: 0 }

export default function PlayTab({ zones, activeMatrix = null }) {
  const [role, setRole] = useState('Shooter')
  const [phase, setPhase] = useState('idle')
  const [selected, setSelected] = useState(null)
  const [last, setLast] = useState(null)
  const [record, setRecord] = useState(EMPTY_RECORD)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const timers = useRef([])

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])
  const later = (fn, ms) => timers.current.push(setTimeout(fn, ms))

  useEffect(() => {
    // new opponent, fresh scouting record
    clearTimers()
    setPhase('idle')
    setSelected(null)
    setLast(null)
    setRecord(EMPTY_RECORD)
    setError(null)
    setBusy(false)
    return clearTimers
  }, [role, activeMatrix, clearTimers])

  function reset() {
    clearTimers()
    setPhase('idle')
    setSelected(null)
    setBusy(false)
  }

  async function pickZone(key) {
    if (busy || phase === 'windup' || phase === 'flight') return
    const zone = zones.find((z) => z.key === key)
    clearTimers()
    setSelected(key)
    setPhase('windup')
    setBusy(true)
    setError(null)

    later(async () => {
      try {
        const result = await api.penalty({ role, zone: zone.label, values: activeMatrix })
        setLast(result)
        setRecord((r) => ({
          hits: r.hits + (role === 'Shooter' ? (result.scored ? 1 : 0) : result.scored ? 0 : 1),
          total: r.total + 1,
        }))
        setPhase('flight')
        later(() => {
          setPhase('result')
          setBusy(false)
        }, FLIGHT_MS)
      } catch (err) {
        setError(err.message)
        reset()
      }
    }, WINDUP_MS)
  }

  const keyOf = (label) => zones.find((z) => z.label === label)?.key ?? null
  const interactive = (phase === 'idle' || phase === 'result') && !busy
  const revealed = phase === 'flight' || phase === 'result'
  const shotZone = revealed ? (role === 'Shooter' ? selected : keyOf(last?.shooter_zone)) : null
  const diveZone = revealed ? (role === 'Goalkeeper' ? selected : keyOf(last?.goalkeeper_zone)) : null

  const verdict = last
    ? role === 'Shooter'
      ? last.scored
        ? 'Goal'
        : 'Saved'
      : last.scored
        ? 'Conceded'
        : 'Saved'
    : null
  const verdictGood = last && (role === 'Shooter' ? last.scored : !last.scored)

  const recordText =
    record.total === 0
      ? role === 'Shooter'
        ? 'No kicks taken yet'
        : 'No penalties faced yet'
      : role === 'Shooter'
        ? `Scored ${record.hits} of ${record.total}`
        : `Saved ${record.hits} of ${record.total}`

  return (
    <div className="duel">
      <section className="board-wrap">
        <GoalField
          zones={zones}
          mode={role === 'Shooter' ? 'shoot' : 'dive'}
          selectedZone={selected}
          onSelect={pickZone}
          interactive={interactive}
          phase={phase}
          shotZone={shotZone}
          diveZone={diveZone}
          scored={phase === 'result' && last ? last.scored : null}
        />
        {error && <p className="board-error">{error}</p>}
      </section>

      <aside className="clipboard">
        <div className="clip"></div>

        <div className="role-switch" role="group" aria-label="Choose your side">
          <button
            type="button"
            className={role === 'Shooter' ? 'on' : ''}
            onClick={() => setRole('Shooter')}
            disabled={busy}
          >
            Take the kick
          </button>
          <button
            type="button"
            className={role === 'Goalkeeper' ? 'on' : ''}
            onClick={() => setRole('Goalkeeper')}
            disabled={busy}
          >
            Keep goal
          </button>
        </div>

        <p className="record">{recordText}</p>

        <div className="note">
          {last ? (
            <>
              <div className="note-row">
                <span>Your call</span>
                <b>{role === 'Shooter' ? last.shooter_zone : last.goalkeeper_zone}</b>
              </div>
              <div className="note-row">
                <span>{role === 'Shooter' ? 'Keeper went' : 'Striker went'}</span>
                <b>{role === 'Shooter' ? last.goalkeeper_zone : last.shooter_zone}</b>
              </div>
              <div className="note-row">
                <span>Chance on that pairing</span>
                <b>{pct(last.scoring_probability, 0)}</b>
              </div>
              <p className={`verdict-word ${verdictGood ? 'good' : 'bad'}`}>{verdict}</p>
              <div className="ai-mix" aria-hidden="true">
                {last.ai_probabilities.map((entry) => (
                  <i key={entry.label} style={{ height: `${18 + entry.probability * 120}%` }} title={`${entry.label} ${pct(entry.probability, 0)}`} />
                ))}
              </div>
              <p className="mix-caption">
                {role === 'Shooter' ? 'Where the keeper commits' : 'Where the striker aims'}, drawn from the
                equilibrium mix. Never the same read twice.
              </p>
            </>
          ) : (
            <p className="note-empty">
              {role === 'Shooter'
                ? 'Choose a corner on the board. The keeper commits at the same instant, so you cannot out-guess a player who is guessing well.'
                : 'Choose which way to go. The striker picks a corner at the same instant, sampled from the optimal mix.'}
            </p>
          )}
        </div>

        {last && (
          <button
            type="button"
            className="take-another"
            onClick={reset}
            disabled={phase === 'windup' || phase === 'flight'}
          >
            Take another
          </button>
        )}
      </aside>
    </div>
  )
}
