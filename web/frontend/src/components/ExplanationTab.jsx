import { fixed, pct } from '../format'

export default function ExplanationTab({ equilibrium }) {
  const v = equilibrium ? fixed(equilibrium.game_value) : 'v'
  const maximin = equilibrium ? fixed(equilibrium.pure_analysis.maximin, 2) : 'maximin'
  const minimax = equilibrium ? fixed(equilibrium.pure_analysis.minimax, 2) : 'minimax'

  return (
    <div className="tab-stack explain">
      <section className="card">
        <h3>Zero-sum game</h3>
        <p>
          The shooter wants to <em>maximise</em> the probability of scoring; the goalkeeper wants to{' '}
          <em>minimise</em> it. One player's gain is exactly the other's loss, so if the shooter's
          payoff for an outcome is <code>A[i,j]</code>, the goalkeeper's payoff is <code>−A[i,j]</code>.
          The whole game is described by the single matrix <code>A</code>.
        </p>
      </section>

      <section className="card">
        <h3>Imperfect information &amp; mixed strategies</h3>
        <p>
          Both players commit simultaneously — neither sees the other's choice — so no deterministic
          rule is safe: whatever fixed zone you pick, the opponent could exploit it. A{' '}
          <strong>mixed strategy</strong> is a probability distribution over zones. The shooter plays{' '}
          <code>p = (p₁,…,p₆)</code>, the goalkeeper <code>q = (q₁,…,q₆)</code>, with{' '}
          <code>Σpᵢ = 1</code>, <code>pᵢ ≥ 0</code>.
        </p>
      </section>

      <section className="card">
        <h3>Expected payoff</h3>
        <p>
          For strategies <code>p</code> and <code>q</code> the shooter's expected scoring
          probability is
        </p>
        <pre>E = pᵀ A q = Σᵢ Σⱼ pᵢ · A[i,j] · qⱼ</pre>
      </section>

      <section className="card">
        <h3>Pure-strategy bounds: maximin and minimax</h3>
        <p>
          If the shooter had to reveal a single row, the safe choice guarantees{' '}
          <code>maximin = maxᵢ minⱼ A[i,j] = {maximin}</code>. If the goalkeeper had to reveal a
          single column, it concedes at most <code>minimax = minⱼ maxᵢ A[i,j] = {minimax}</code>.
          When these differ (as here) there is no pure-strategy equilibrium and randomisation
          strictly helps.
        </p>
      </section>

      <section className="card">
        <h3>Minimax theorem</h3>
        <p>Von Neumann proved that for every finite zero-sum game</p>
        <pre>maxₚ min_q pᵀ A q  =  min_q maxₚ pᵀ A q  =  v</pre>
        <p>
          The common value <code>v</code> is the <strong>value of the game</strong>. Here{' '}
          <code>v = {v}</code> — the shooter can guarantee an expected scoring probability of at
          least <code>{equilibrium ? pct(equilibrium.game_value) : 'v'}</code>, and the goalkeeper
          can hold it to no more than that.
        </p>
      </section>

      <section className="card">
        <h3>Linear-programming formulation</h3>
        <p>Fixing the shooter's mix, the goalkeeper replies with the worst column, so the shooter solves</p>
        <pre>{`maximise  v
subject to  (pᵀ A)ⱼ ≥ v   for every column j
            Σ pᵢ = 1,  pᵢ ≥ 0`}</pre>
        <p>The goalkeeper solves the dual</p>
        <pre>{`minimise  w
subject to  (A q)ᵢ ≤ w   for every row i
            Σ qⱼ = 1,  qⱼ ≥ 0`}</pre>
        <p>
          LP strong duality forces the two optima to coincide, and that shared number is{' '}
          <code>v</code>. This app solves both programs with <code>scipy.optimize.linprog</code> and
          cross-checks them.
        </p>
      </section>

      <section className="card">
        <h3>Nash equilibrium</h3>
        <p>
          The optimal pair <code>(p*, q*)</code> is a <strong>Nash equilibrium</strong>: given{' '}
          <code>q*</code>, every zone in the shooter's support yields exactly <code>v</code>, so the
          shooter cannot do better by deviating — and symmetrically for the goalkeeper. Because the
          game is zero-sum, this equilibrium is also unique in value and interchangeable. The Play
          tab's AI simply samples from <code>q*</code> (or <code>p*</code>), which is why it cannot
          be read or exploited.
        </p>
      </section>
    </div>
  )
}
