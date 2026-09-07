"""Command-line entry point for the Tactical Penalty Shootout Simulator.

Usage
-----
    python main.py demo              # run the Phase 1 game-theory console demo
    python main.py serve             # start the web application (FastAPI + built UI)
    python main.py serve --port 9000 --host 0.0.0.0 --reload

The web UI is served by the FastAPI app in ``web.backend.app``.  Build the
front-end first with ``npm --prefix web/frontend install && npm --prefix
web/frontend run build`` (or use the provided Dockerfile, which does it).
"""

from __future__ import annotations

import argparse


def _run_demo() -> None:
    from demo import main as demo_main

    demo_main()


def _run_server(host: str, port: int, reload: bool) -> None:
    import uvicorn

    uvicorn.run("web.backend.app:app", host=host, port=port, reload=reload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tactical Penalty Shootout Simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="Run the console game-theory demonstration.")

    serve = sub.add_parser("serve", help="Run the web application.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    serve.add_argument("--reload", action="store_true", help="Auto-reload on code changes (development).")

    args = parser.parse_args()

    if args.command == "demo":
        _run_demo()
    elif args.command == "serve":
        _run_server(args.host, args.port, args.reload)


if __name__ == "__main__":
    main()
