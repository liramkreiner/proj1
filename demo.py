"""Phase 1 console demonstration of the zero-sum game-theory engine.

Run:  python demo.py

Solves three games with the *same* generic linear-programming solver and
prints, for each one:

* the payoff matrix (shooter's perspective, entry = P(score))
* maximin and minimax (pure-strategy security levels)
* whether a pure-strategy saddle point exists
* the optimal mixed strategy for the shooter and the goalkeeper
* the game value v
* the numerical equilibrium-validation report

Examples
--------
1. Matching pennies         -> known equilibrium p = q = (0.5, 0.5), v = 0
2. A 2x2 non-uniform game   -> known equilibrium p = (0.2, 0.8), q = (0.6, 0.4), v = 2.4
3. The 6x6 penalty matrix   -> the game actually modelled by the application
"""

from __future__ import annotations

import numpy as np

from game.payoff_matrix import build_default_penalty_payoff_matrix
from game_theory.minimax import analyze_pure_strategies
from game_theory.nash_equilibrium import solve_nash_equilibrium

np.set_printoptions(precision=3, floatmode="fixed", suppress=True)


def _print_matrix(matrix: np.ndarray, row_labels: tuple[str, ...], column_labels: tuple[str, ...]) -> None:
    col_width = max(8, *(len(label) for label in column_labels)) + 2
    row_width = max(len(label) for label in row_labels) + 2
    header = " " * row_width + "".join(f"{label:>{col_width}}" for label in column_labels)
    print(header)
    for label, row in zip(row_labels, matrix, strict=True):
        cells = "".join(f"{value:>{col_width}.3f}" for value in row)
        print(f"{label:<{row_width}}{cells}")


def _print_strategy(title: str, labels: tuple[str, ...], probabilities: np.ndarray) -> None:
    print(f"  {title}")
    for label, probability in zip(labels, probabilities, strict=True):
        bar = "#" * int(round(probability * 40))
        print(f"    {label:<16} {probability:7.4f}  {bar}")


def run_example(
    name: str,
    matrix: np.ndarray,
    row_labels: tuple[str, ...],
    column_labels: tuple[str, ...],
) -> None:
    print("=" * 78)
    print(name)
    print("=" * 78)

    print("\nPayoff matrix (shooter maximises, goalkeeper minimises):")
    _print_matrix(matrix, row_labels, column_labels)

    pure = analyze_pure_strategies(matrix)
    print(f"\nRow minima     : {pure.row_minima}")
    print(f"Column maxima  : {pure.column_maxima}")
    print(f"Maximin        : {pure.maximin:.6f}")
    print(f"Minimax        : {pure.minimax:.6f}")
    if pure.saddle_point is None:
        print("Saddle point   : none (maximin != minimax)  ->  solve for MIXED strategies")
    else:
        r, c = pure.saddle_point
        print(f"Saddle point   : rows[{r}], cols[{c}] = {pure.saddle_point_value:.6f}  (pure equilibrium)")

    equilibrium = solve_nash_equilibrium(matrix, row_labels=row_labels, column_labels=column_labels)

    print("\nMixed-strategy Nash equilibrium:")
    _print_strategy("Shooter strategy p:", row_labels, equilibrium.shooter_strategy.probabilities)
    _print_strategy("Goalkeeper strategy q:", column_labels, equilibrium.goalkeeper_strategy.probabilities)
    print(f"\n  Game value v = {equilibrium.game_value:.6f}")

    print("\nEquilibrium validation:")
    for message in equilibrium.validation.messages:
        print(f"  - {message}")
    print()


def main() -> None:
    run_example(
        "1. MATCHING PENNIES  (textbook check: p = q = (1/2, 1/2), v = 0)",
        np.array([[1.0, -1.0], [-1.0, 1.0]]),
        ("Heads", "Tails"),
        ("Heads", "Tails"),
    )
    run_example(
        "2. NON-UNIFORM 2x2 ZERO-SUM GAME  (check: p = (0.2, 0.8), q = (0.6, 0.4), v = 2.4)",
        np.array([[4.0, 0.0], [2.0, 3.0]]),
        ("Row A", "Row B"),
        ("Col A", "Col B"),
    )

    penalty = build_default_penalty_payoff_matrix()
    run_example(
        "3. PENALTY SHOOTOUT  (the 6x6 game this application actually plays)",
        penalty.values,
        penalty.row_labels,
        penalty.column_labels,
    )


if __name__ == "__main__":
    main()
