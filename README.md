# Tactical Penalty Shootout Simulator

A zero-sum penalty shootout simulator with a mathematically grounded game-theory engine.

## Desktop app

Run the PyQt6 desktop version:

```powershell
cd c:\Users\liram\Desktop\proj1
C:/Python312/python.exe main.py
```

Run the console demo:

```powershell
C:/Python312/python.exe main.py --demo
```

## Web app

The web version uses a FastAPI backend and a React frontend.

### Development

Start the backend:

```powershell
cd c:\Users\liram\Desktop\proj1
C:/Python312/python.exe -m uvicorn web.backend.app:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in a second terminal:

```powershell
cd c:\Users\liram\Desktop\proj1\web\frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, usually `http://localhost:5173`.

### Production build

Build the frontend:

```powershell
cd c:\Users\liram\Desktop\proj1\web\frontend
npm run build
```

Then run the backend server:

```powershell
cd c:\Users\liram\Desktop\proj1
C:/Python312/python.exe -m uvicorn web.backend.app:app --host 0.0.0.0 --port 8000
```

With the frontend build present in `web/frontend/dist`, the FastAPI app serves the web UI from the same server.

## Notes

- The game-theory solver remains in `game_theory/`.
- The penalty match controller is still shared between desktop and web versions.
- The web backend stores sessions in memory for the current process.