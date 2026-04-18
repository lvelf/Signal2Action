# Signal2Action
### An Agentic Consulting System That Turns Ambiguity Into Action

> *"Most enterprises don't lack data — they lack a clear path from signal to decision."*

Signal2Action is a multi-agent AI system built for enterprise and consulting scenarios. It transforms unstructured inputs — a voice note, a financial report, a competitive analysis, a half-formed idea — into structured assessments, functional decompositions, solution recommendations, and executable action plans.

---

## The Problem

In real consulting and enterprise workflows:

- Inputs arrive in every format: voice, spreadsheets, PDFs, market data, financial reports
- Requirements shift through rounds of miscommunication
- Analysis and execution remain disconnected
- Teams end up knowing what the problem is — but not what to do next

Signal2Action closes that gap.

---

## How It Works

Signal2Action follows a consulting-style pipeline powered by three specialized agents, a human review checkpoint, and a simulation QA layer.

```
┌─────────────────────────────────────────────────────────────────┐
│  Input sources                                                  │
│  Voice · Text · Excel/PDF · Financial data · Competitive · ...  │
│                        [VoiceRun]                               │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  Agent 1 — Intake + clarification                                │
│  Parses all input types · Extracts signal · Asks clarifying      │
│  questions · Converges on a clear problem statement              │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
              ┌────────────────────────┐
              │   Human review         │ ← revise if needed ↩
              │   Scope confirmation   │
              └────────────┬───────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  Agent 2 — Assessment + decomposition          [You.com]         │
│  Evaluates current state · Identifies gaps · Breaks problem      │
│  into functional modules                                         │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  Agent 3 — Solution + action planning          [Baseten]         │
│  Generates recommendations · Prioritizes trade-offs ·            │
│  Outputs executable roadmap                                      │
└──────────────────────────┬───────────────────────────────────────┘
                           ↓
              ┌────────────────────────────────────────┐
              │  Deliverable output                    │
              │  Assessment · Decomposition ·          │
              │  Solution · Action plan                │
              └────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────────┐
│  Veris — simulation + QA layer                                   │
│  Stress-tests all input types and agent behaviors across         │
│  edge cases · Validates reliability before deployment            │
└──────────────────────────────────────────────────────────────────┘
```

**Core flow:** `Signal → Clarify → Review → Assess → Decompose → Solve → Act`

---

## What Makes It Different

**It accepts inputs the way enterprises actually work.**
Users don't always type a clean problem statement. They drop in an Excel file, paste a financial summary, share a voice note, or upload a competitor teardown. Signal2Action ingests all of it and extracts the signal underneath.

**It follows consulting logic, not chatbot logic.**
The pipeline mirrors how a real consulting engagement runs: understand the brief → align on scope → assess current state → design solution → define next actions. Each agent owns exactly one step.

**Human review is built in, not bolted on.**
After Agent 1 clarifies the problem, the system pauses for a human to confirm scope before any analysis begins. This catches misunderstandings at the cheapest possible moment — before the work is done.

**Outputs are structured deliverables, not open-ended answers.**
Every stage produces a defined artifact: a clarified request, a state assessment, a functional decomposition, a solution recommendation, or an action plan. The system delivers documents, not conversations.

---

## Agent Breakdown

### Agent 1 — Intake + Clarification
Accepts any input format — voice (via VoiceRun), text, Excel, PDF, financial data, competitive reports — and normalizes it into a processable signal. Runs an iterative clarification loop to identify missing context and converge on a well-defined problem statement before passing anything downstream.

### Agent 2 — Assessment + Decomposition
Takes the confirmed problem scope and evaluates the current state: constraints, resources, dependencies, and gaps. Then breaks the problem into a functional tree of modules and sub-tasks — the bridge between understanding and design. Uses **You.com** search to enrich analysis with real-time external context.

### Agent 3 — Solution + Action Planning
Generates structured solution recommendations with trade-offs and prioritization, then converts the selected path into a concrete roadmap with sequenced next steps and success metrics. Powered by **Baseten** for model inference.

### Veris — Simulation + QA Layer
The entire pipeline is stress-tested using **Veris** sandbox environments. We simulate diverse input types, edge cases, and ambiguous user requests to validate agent behavior and guarantee reliability — without touching real production data.

---

## Sponsor Integrations

| Sponsor | Role |
|---------|------|
| **VoiceRun** | Voice input capture and transcription into Agent 1 |
| **You.com** | Real-time external context retrieval during assessment |
| **Baseten** | Model inference backend for solution and action planning |
| **Veris** | Simulation sandbox for pipeline stress-testing and QA |

---

## Example Walkthrough

**Input:** User uploads a Q3 financial report and says (via voice): *"Our margins are down — what should we do?"*

| Stage | Output |
|-------|--------|
| **Intake** | Parses PDF + voice · Extracts: margin compression, Q3 timeframe, cost vs revenue question |
| **Clarification** | Asks: which product lines? which cost centers? what's the target margin? |
| **Human review** | Confirms scope: focus on COGS reduction in product line A |
| **Assessment** | Gaps: procurement inefficiency, 3 underperforming SKUs, no cost tracking by line |
| **Decomposition** | Modules: cost attribution layer, SKU performance analysis, procurement audit |
| **Solution** | Recommended: discontinue 2 SKUs, renegotiate top 3 supplier contracts |
| **Action plan** | Week 1: SKU analysis. Week 2: supplier outreach. Week 3: revised margin model |

---

## Built With

- **Python** — Agent orchestration
- **Anthropic Claude** — Core reasoning across all agents
- **VoiceRun** — Voice input and transcription
- **Baseten** — Model deployment and inference
- **You.com API** — Search-augmented context retrieval
- **Veris AI** — Agent simulation and stress testing

---

## Team

Built at **Veris Agent Jam — Enterprise AI Agent Hackathon** 

- Shenghan Gao
- Kimberly Huang
- Rosemary Li
- Nuo Chen

---

*Signal2Action: from ambiguity to action, one agent at a time.*

---

## Local reqANA API

Run the backend:

```bash
uvicorn reqANA.api:app --reload --port 8001
```

Run the frontend:

```bash
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500/front_end.html
```

The requirement intake UI posts to:

```text
POST http://127.0.0.1:8001/requirements/from-mixed
```

Supported input fields:

- `text`
- `files`
- `audio_files`
- `google_access_token`
- `google_file_ids`
- `google_folder_ids`

## Google Drive Setup

To use Google Drive selection in the frontend:

1. Create a Google Cloud project.
2. Enable Google Drive API and Google Picker API.
3. Create an OAuth Client ID for a web app.
4. Create an API key.
5. Add `http://127.0.0.1:5500` to authorized JavaScript origins.

Set these in `.env`:

```bash
GOOGLE_CLIENT_ID=your_oauth_client_id.apps.googleusercontent.com
GOOGLE_API_KEY=your_google_api_key
GOOGLE_APP_ID=your_google_cloud_project_number
```

When you click Google Drive in the frontend, the page calls `/config/google`,
then opens Google auth and the Drive Picker directly.

The required values are:

- Google OAuth Client ID
- Google API Key
- Google Cloud Project Number / App ID
