"""Desktop entry point and optional console demo for the penalty simulator."""

from __future__ import annotations

import argparse
import numpy as np

from PyQt6.QtWidgets import QApplication

from game.payoff_matrix import build_default_penalty_payoff_matrix
from game_theory.minimax import analyze_pure_strategies
from game_theory.nash_equilibrium import solve_nash_equilibrium
from ui.main_window import MainWindow
from ui.styles import APP_STYLE


def _format_matrix(values: np.ndarray) -> str:
    return np.array2string(values, precision=3, floatmode="fixed")


def _format_strategy(labels: tuple[str, ...], probabilities: np.ndarray) -> str:
    lines = [f"  {label}: {probability:.3%}" for label, probability in zip(labels, probabilities, strict=True)]
    return "\n".join(lines)


def run_example(name: str, matrix: np.ndarray, row_labels: tuple[str, ...], column_labels: tuple[str, ...]) -> None:
    print(f"\n=== {name} ===")
    print("Payoff matrix (shooter perspective):")
    print(_format_matrix(matrix))

    pure_analysis = analyze_pure_strategies(matrix)
    equilibrium = solve_nash_equilibrium(matrix)

    print(f"Maximin: {pure_analysis.maximin:.6f}")
    print(f"Minimax: {pure_analysis.minimax:.6f}")
    print("Shooter optimal strategy:")
    print(_format_strategy(row_labels, equilibrium.shooter_strategy.probabilities))
    print("Goalkeeper optimal strategy:")
    print(_format_strategy(column_labels, equilibrium.goalkeeper_strategy.probabilities))
    print(f"Game value: {equilibrium.game_value:.6f}")
    print("Equilibrium validation:")
    for message in equilibrium.validation.messages:
        print(f"  - {message}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tactical Penalty Shootout Simulator")
    parser.add_argument("--demo", action="store_true", help="Run the console math demo instead of the GUI.")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return

    app = QApplication([])
    app.setStyleSheet(APP_STYLE)
    window = MainWindow()
    window.show()
    app.exec()


def run_demo() -> None:
    matching_pennies = np.array([[1.0, -1.0], [-1.0, 1.0]], dtype=float)
    non_uniform_game = np.array([[4.0, 0.0], [2.0, 3.0]], dtype=float)
    penalty_matrix = build_default_penalty_payoff_matrix()

    run_example(
        "Matching Pennies",
        matching_pennies,
        ("Heads", "Tails"),
        ("Heads", "Tails"),
    )
    run_example(
        "Non-uniform Zero-Sum Game",
        non_uniform_game,
        ("Row 1", "Row 2"),
        ("Column 1", "Column 2"),
    )
    run_example(
        "Penalty Shootout Matrix",
        penalty_matrix.values,
        penalty_matrix.row_labels,
        penalty_matrix.column_labels,
    )


if __name__ == "__main__":
    main()