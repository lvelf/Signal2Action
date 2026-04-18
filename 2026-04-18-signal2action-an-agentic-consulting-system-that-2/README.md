# Signal2Action

Signal2Action is a production-style hackathon MVP for an agentic consulting system that turns ambiguous enterprise inputs into structured action plans.

This repo is intentionally built as a modular workflow system, not a chatbot. The frontend presents stage-by-stage outputs and human review gates. The backend exposes each stage as a separate API route with mock-first sponsor adapters.

## Stack

- `frontend/`: Next.js app for the workflow UI
- `backend/`: FastAPI service for stage orchestration and sponsor adapters

## Core Workflow

1. `POST /api/intake`
2. `POST /api/clarify`
3. `POST /api/review`
4. `POST /api/assess`
5. `POST /api/plan`
6. `POST /api/simulate`
7. `POST /api/run-demo`

## Sponsor Integrations

- `VoiceRun`: voice transcript entry point with mock transcript fallback
- `You.com`: external context enrichment in assessment with local mock search fallback
- `Baseten`: solution/action-planning inference backend with mock fallback
- `Veris`: simulation and QA adapter with local mock mode

Live integrations are intentionally kept behind adapter interfaces and environment variables. Where exact API payloads are unknown, the code includes clear `TODO` notes instead of inventing SDK calls.

## Repo Structure

```text
.
├── backend
│   ├── app
│   │   ├── main.py
│   │   ├── schemas.py
│   │   ├── workflow.py
│   │   └── services/
│   ├── sample_data/mock_scenarios.json
│   ├── scripts/seed_demo.py
│   └── tests/
├── frontend
│   ├── app/
│   ├── components/
│   └── lib/
└── .env.example
```

## Local Setup

### 1. Configure environment

Copy `.env.example` to `.env` and adjust values as needed. The default configuration runs entirely in mock mode, which is the recommended hackathon demo path.

### 2. Run the backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

Backend will start on `http://localhost:8000`.

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will start on `http://localhost:3000`.

## Demo Flow

The frontend is preloaded with the example walkthrough:

`Our margins are down in Q3 — what should we do?`

You can:

- click `Run Full Demo` to execute the full workflow in one call
- run each stage manually to show the handoffs and human review step
- edit the approved scope before assessment to demonstrate control and governance

## Seed Script

Generate a demo seed payload:

```bash
python3 backend/scripts/seed_demo.py
```

This writes `backend/sample_data/generated_demo_seed.json`.

## Tests

Run adapter tests:

```bash
source .venv/bin/activate
pytest backend/tests
```

## Notes

- All stage outputs are structured JSON models.
- Secrets are never hardcoded.
- The app is designed to stay demoable even if external APIs are unavailable.
- The mock scenario library lives in `backend/sample_data/mock_scenarios.json` so you can expand it quickly before judging.
