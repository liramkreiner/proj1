"""The Phase 1 console demo must run end to end without raising."""

from __future__ import annotations

import numpy as np

from demo import run_example


def test_demo_runs_all_examples(capsys) -> None:
    import demo

    demo.main()
    out = capsys.readouterr().out

    assert "MATCHING PENNIES" in out
    assert "PENALTY SHOOTOUT" in out
    assert "Equilibrium VALID within tolerance." in out
    # The known matching-pennies value appears in the output.
    assert "Game value v = 0.000000" in out


def test_run_example_accepts_rectangular_game(capsys) -> None:
    run_example(
        "rectangular",
        np.array([[3.0, -1.0, -3.0], [-2.0, 4.0, -1.0]]),
        ("Row A", "Row B"),
        ("Col A", "Col B", "Col C"),
    )
    assert "Game value" in capsys.readouterr().out
