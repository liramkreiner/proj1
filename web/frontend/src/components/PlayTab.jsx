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

// How much a keeper who had spotted your realised shooting pattern could take
// off your scoring rate. exploited = min_j (p̂ᵀ A)_j ≤ v for any p̂, with
// equality only when p̂ is the equilibrium mix.
function readShooting(career, equilibrium) {
  const n = career.total
  if (!equilibrium || n < 3) return { ready: false, n }
  const rows = equilibrium.payoff_matrix.row_labels
  const A = equilibrium.payoff_matrix.values
  const v = equilibrium.game_value
  const pHat = rows.map((label) => (career.shots[label] || 0) / n)

  let exploited = Infinity
  for (let j = 0; j < A[0].length; j += 1) {
    let s = 0
    for (let i = 0; i < rows.length; i += 1) s += pHat[i] * A[i][j]
    if (s < exploited) exploited = s
  }

  const pStar = equilibrium.shooter_strategy
  let worst = 0
  for (let i = 1; i < rows.length; i += 1) {
    if (pHat[i] - pStar[i].probability > pHat[worst] - pStar[worst].probability) worst = i
  }

  return {
    ready: true,
    n,
    v,
    exploited,
    leak: v - exploited,
    worst: { label: rows[worst], you: pHat[worst], opt: pStar[worst].probability },
  }
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

export default function PlayTab({ zones, activeMatrix = null, equilibrium = null }) {
  const [kicks, setKicks] = useState([])
  const [phase, setPhase] = useState('idle')
  const [selected, setSelected] = useState(null)
  const [last, setLast] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  // your shooting pattern, kept across shootouts (reset only when the matrix changes)
  const [career, setCareer] = useState({ total: 0, shots: {} })
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

  // a different payoff matrix is a different game — start the readability tally over
  useEffect(() => {
    setCareer({ total: 0, shots: {} })
  }, [activeMatrix])

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
          if (kick.taker === 'you') {
            setCareer((c) => ({
              total: c.total + 1,
              shots: { ...c.shots, [kick.shot]: (c.shots[kick.shot] || 0) + 1 },
            }))
          }
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
  // Resolve the outcome the moment the ball leaves the spot so it flies to ONE
  // target (net on a goal, gloves on a save) instead of the corner and then the
  // gloves. The GOAL/SAVED caption is still shown only at 'result' inside GoalField.
  const outcome = revealed ? (last.scored ? 'goal' : 'save') : null

  const youKicks = kicks.filter((k) => k.taker === 'you')
  const aiKicks = kicks.filter((k) => k.taker === 'ai')
  const read = readShooting(career, equilibrium)

  const statusLine = finished
    ? st.winner === 'you'
      ? 'You win the shootout'
      : 'AI wins the shootout'
    : st.phase === 'suddenDeath'
      ? `Sudden death, ${isYourKick ? 'your kick' : 'your save'}`
      : `Kick ${roundNo} of ${REG}, ${isYourKick ? 'your kick' : 'your save'}`

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
        <div className="sb-head">
          <span>Penalty shootout</span>
          {!finished && (
            <span className={`sb-role sb-role--${isYourKick ? 'shooter' : 'keeper'}`}>
              You: {isYourKick ? 'Striker' : 'Keeper'}
            </span>
          )}
        </div>

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

        <div className="sb-edge">
          <div className="sb-edge-head">How readable you are</div>
          {read.ready ? (
            <>
              <div className="sb-edge-stat">
                <strong className={read.leak > 0.03 ? 'leak' : 'tight'}>{pct(read.exploited, 0)}</strong>
                <span>a keeper who had read your {read.n} kicks</span>
              </div>
              <p className="sb-edge-note">
                {read.leak > 0.03
                  ? `That is ${pct(read.leak, 0)} below the equilibrium's ${pct(read.v, 0)}. You lean on ${read.worst.label} — ${pct(read.worst.you, 0)} of your kicks, against an optimal ${pct(read.worst.opt, 0)}.`
                  : `The equilibrium scores ${pct(read.v, 0)}; you are mixing about as well as the maths allows.`}
              </p>
            </>
          ) : (
            <p className="sb-edge-note">
              Take a few kicks. This shows what a keeper who spotted your pattern could hold you to.
            </p>
          )}
        </div>

        <button type="button" className="sb-reset" onClick={newShootout} disabled={busy}>
          {finished ? 'New shootout' : 'Restart'}
        </button>
      </aside>
    </div>
  )
}
