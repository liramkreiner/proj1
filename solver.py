import numpy as np
from scipy.optimize import linprog

PROFILES = [
    {
        "name": "Symmetric",
        "matrix": np.array([
            [0.55, 0.70, 0.55],
            [0.70, 0.40, 0.70],
            [0.55, 0.70, 0.55],
        ]),
    },
    {
        "name": "Right-Footed",
        "matrix": np.array([
            [0.65, 0.80, 0.45],
            [0.75, 0.40, 0.65],
            [0.40, 0.65, 0.50],
        ]),
    },
    {
        "name": "Powerful",
        "matrix": np.array([
            [0.60, 0.85, 0.60],
            [0.80, 0.50, 0.80],
            [0.60, 0.85, 0.60],
        ]),
    },
]

_profile_map = {p["name"]: p["matrix"] for p in PROFILES}


def get_profile(name: str) -> np.ndarray:
    if name not in _profile_map:
        raise ValueError(f"Unknown profile: {name}")
    return _profile_map[name].copy()


def apply_risk(matrix: np.ndarray, risk: float) -> np.ndarray:
    result = matrix * (1.0 - risk)
    return np.clip(result, 0.0, 1.0)


def solve_nash(matrix: np.ndarray) -> dict:
    n = matrix.shape[0]
    uniform = np.ones(n) / n

    # First, check if symmetric solution is a valid equilibrium
    is_symmetric = np.allclose(matrix, matrix.T)
    if is_symmetric:
        payoff_uniform_k = matrix @ uniform
        payoff_uniform_g = uniform @ matrix

        # Check if uniform strategy is Nash equilibrium
        if np.allclose(payoff_uniform_k, payoff_uniform_k[0]) and np.allclose(payoff_uniform_g, payoff_uniform_g[0]):
            value = float(np.dot(uniform, matrix @ uniform))
            return {"kicker": uniform.copy(), "goalie": uniform.copy(), "value": value}

    shift = -matrix.min() + 1e-6
    A = matrix + shift

    try:
        # Goalie (minimizer / column player)
        c_g = np.zeros(n + 1)
        c_g[-1] = -1.0

        A_ub_g = np.hstack([-A.T, np.ones((n, 1))])
        b_ub_g = np.zeros(n)

        A_eq_g = np.ones((1, n + 1))
        A_eq_g[0, -1] = 0.0
        b_eq_g = np.array([1.0])

        bounds_g = [(0, None)] * n + [(None, None)]
        res_g = linprog(c_g, A_ub=A_ub_g, b_ub=b_ub_g,
                        A_eq=A_eq_g, b_eq=b_eq_g,
                        bounds=bounds_g, method="highs")

        # Kicker (maximizer / row player)
        c_k = np.zeros(n + 1)
        c_k[-1] = 1.0

        A_ub_k = np.hstack([A, -np.ones((n, 1))])
        b_ub_k = np.zeros(n)

        A_eq_k = np.ones((1, n + 1))
        A_eq_k[0, -1] = 0.0
        b_eq_k = np.array([1.0])

        bounds_k = [(0, None)] * n + [(None, None)]
        res_k = linprog(c_k, A_ub=A_ub_k, b_ub=b_ub_k,
                        A_eq=A_eq_k, b_eq=b_eq_k,
                        bounds=bounds_k, method="highs")

        if res_g.success and res_k.success:
            goalie = np.clip(res_g.x[:n], 0, None)
            kicker = np.clip(res_k.x[:n], 0, None)

            # Clean up near-zero values for numerical stability
            goalie[goalie < 1e-8] = 0
            kicker[kicker < 1e-8] = 0

            goalie_sum = goalie.sum()
            kicker_sum = kicker.sum()

            if goalie_sum > 1e-10:
                goalie /= goalie_sum
            if kicker_sum > 1e-10:
                kicker /= kicker_sum

            value = float(res_k.x[-1]) - shift
            value = float(np.clip(value, matrix.min(), matrix.max()))
            return {"kicker": kicker, "goalie": goalie, "value": value}

    except Exception:
        pass

    value = float(np.dot(uniform, matrix @ uniform))
    return {"kicker": uniform.copy(), "goalie": uniform.copy(), "value": value}
