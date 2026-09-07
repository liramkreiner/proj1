import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../api'
import { pct } from '../format'
import GoalField from './GoalField'

const WINDUP_MS = 300
const FLIGHT_MS = 680
const HOLD_MS = 1550
const REG = 5 // kicks per side in regulation

function tally(kicks) {
  let you = 0
  let ai = 0
  let youN = 0
  let aiN = 0
  for (const k of kicks) {
    if (k.taker === 'you') {
      youN += 1
      if (k.scored) you += 1
    } else {
      aiN += 1
      if (k.scored) ai += 1
    }
  }
  return { you, ai, youN, aiN }
}

// Standard shootout: 5 each, alternating (you first); stop early once it can't
// be caught; then sudden death, decided after each complete pair.
function status(kicks) {
  const { you, ai, youN, aiN } = tally(kicks)
  const inRegulation = !(youN >= REG && aiN >= REG)
  if (inRegulation) {
    const youRem = REG - youN
    const aiRem = REG - aiN
    if (you > ai + aiRem) return { over: true, winner: 'you', you, ai, phase: 'regulation' }
    if (ai > you + youRem) return { over: true, winner: 'ai', you, ai, phase: 'regulation' }
    return { over: false, you, ai, phase: 'regulation' }
  }
  if (youN === aiN && you !== ai) return { over: true, winner: you > ai ? 'you' : 'ai', you, ai, phase: 'suddenDeath' }
  return { over: false, you, ai, phase: 'suddenDeath' }
}

function Pips({ list, target }) {
  const slots = Math.max(target, list.length)
  return (
    <span className="sb-pips">
      {Array.from({ length: slots }).map((_, i) => {
        const k = list[i]
        const cls = !k ? 'pip' : k.scored ? 'pip pip-goal' : 'pip pip-miss'
        return <i key={i} className={cls} />
      })}
    </span>
  )
}

export default function PlayTab({ zones, activeMatrix = null }) {
  const [kicks, setKicks] = useState([])
  const [phase, setPhase] = useState('idle')
  const [selected, setSelected] = useState(null)
  const [last, setLast] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const timers = useRef([])

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])
  const later = (fn, ms) => timers.current.push(setTimeout(fn, ms))

  const newShootout = useCallback(() => {
    clearTimers()
    setKicks([])
    setPhase('idle')
    setSelected(null)
    setLast(null)
    setBusy(false)
    setError(null)
  }, [clearTimers])

  useEffect(() => {
    newShootout()
    return clearTimers
  }, [activeMatrix, newShootout, clearTimers])

  const st = status(kicks)
  const finished = st.over
  const isYourKick = kicks.length % 2 === 0
  const role = isYourKick ? 'Shooter' : 'Goalkeeper'
  const roundNo = Math.floor(kicks.length / 2) + 1

  async function pick(key) {
    if (busy || finished || phase === 'windup' || phase === 'flight') return
    const zone = zones.find((z) => z.key === key)
    clearTimers()
    setSelected(key)
    setLast(null)
    setPhase('windup')
    setBusy(true)
    setError(null)

    later(async () => {
      try {
        const res = await api.penalty({ role, zone: zone.label, values: activeMatrix })
        const kick = {
          taker: isYourKick ? 'you' : 'ai',
          scored: res.scored,
          shot: res.shooter_zone,
          dive: res.goalkeeper_zone,
        }
        setLast(res)
        setPhase('flight')
        later(() => {
          setKicks((prev) => [...prev, kick])
          setPhase('result')
          setBusy(false)
          later(() => {
            setPhase('idle')
            setSelected(null)
          }, HOLD_MS)
        }, FLIGHT_MS)
      } catch (err) {
        setError(err.message)
        setPhase('idle')
        setSelected(null)
        setBusy(false)
      }
    }, WINDUP_MS)
  }

  const keyOf = (label) => zones.find((z) => z.label === label)?.key ?? null
  const revealed = (phase === 'flight' || phase === 'result') && last
  const shotZone = revealed ? keyOf(last.shooter_zone) : null
  const diveZone = revealed ? keyOf(last.goalkeeper_zone) : null
  const outcome = phase === 'result' && last ? (last.scored ? 'goal' : 'save') : null

  const youKicks = kicks.filter((k) => k.taker === 'you')
  const aiKicks = kicks.filter((k) => k.taker === 'ai')

  const statusLine = finished
    ? st.winner === 'you'
      ? 'You win the shootout'
      : 'AI wins the shootout'
    : st.phase === 'suddenDeath'
      ? `Sudden death — ${isYourKick ? 'your kick' : 'your save'}`
      : `Kick ${roundNo} of ${REG} — ${isYourKick ? 'your kick' : 'your save'}`

  return (
    <div className="duel">
      <section className="pitch-wrap">
        <GoalField
          zones={zones}
          mode={isYourKick ? 'shoot' : 'dive'}
          selectedZone={selected}
          onSelect={pick}
          interactive={phase === 'idle' && !busy && !finished}
          phase={phase}
          shotZone={shotZone}
          diveZone={diveZone}
          outcome={outcome}
        />
        {error && <p className="pitch-error">{error}</p>}
      </section>

      <aside className="scoreboard">
        <div className="sb-head">Penalty shootout</div>

        <div className="sb-row">
          <span className="sb-name">You</span>
          <Pips list={youKicks} target={REG} />
          <span className="sb-score">{st.you}</span>
        </div>
        <div className="sb-row sb-row--ai">
          <span className="sb-name">AI</span>
          <Pips list={aiKicks} target={REG} />
          <span className="sb-score">{st.ai}</span>
        </div>

        <p className={`sb-status ${finished ? 'is-final' : ''} ${st.phase === 'suddenDeath' && !finished ? 'is-sd' : ''}`}>
          {statusLine}
        </p>

        {last && (
          <dl className="sb-last">
            <div>
              <dt>Shot</dt>
              <dd>{last.shooter_zone}</dd>
            </div>
            <div>
              <dt>Keeper</dt>
              <dd>{last.goalkeeper_zone}</dd>
            </div>
            <div>
              <dt>Chance</dt>
              <dd>{pct(last.scoring_probability, 0)}</dd>
            </div>
          </dl>
        )}

        {last && (
          <>
            <div className="sb-mix" aria-hidden="true">
              {last.ai_probabilities.map((e) => (
                <i key={e.label} style={{ height: `${14 + e.probability * 130}%` }} title={`${e.label} ${pct(e.probability, 0)}`} />
              ))}
            </div>
            <p className="sb-mix-cap">
              {isYourKick ? "The keeper's side is drawn" : "The striker's corner is drawn"} from the equilibrium
              mix — you can't read the next one from the last.
            </p>
          </>
        )}

        {!last && (
          <p className="sb-hint">
            You take five kicks and face five, alternating. On your kick, pick a corner; on your save,
            pick a side. Whoever the ball beats, it was drawn from the optimal mix.
          </p>
        )}

        <button type="button" className="sb-reset" onClick={newShootout} disabled={busy}>
          {finished ? 'New shootout' : 'Restart'}
        </button>
      </aside>
    </div>
  )
}
