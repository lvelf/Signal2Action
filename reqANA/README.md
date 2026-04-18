# reqANA

`reqANA` is the requirement analysis module.

It owns:

- Requirement document generation
- Text/file/audio intake APIs
- VoiceRun handler
- Veris simulation entrypoint

## Files

```text
reqANA/
  agent.py              AI requirement analysis logic
  api.py                FastAPI endpoints
  file_loader.py        Requirement file reader
  models.py             Input/output data models
  transcription.py      Audio upload transcription
  voicerun_handler.py   VoiceRun function handler
  integrations/
    veris/
      veris.yaml.example
      Dockerfile.sandbox.example
```

## Local Run

From the project root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env
```

Set your Baseten key in `.env`:

```bash
MODEL_PROVIDER=baseten
BASETEN_API_KEY=your_baseten_key
BASETEN_BASE_URL=https://inference.baseten.co/v1
BASETEN_MODEL=deepseek-ai/DeepSeek-V3.1
```

If you want to use `/requirements/from-voice` for local audio file upload, also set
`OPENAI_API_KEY` because the current local transcription module uses OpenAI
transcription. VoiceRun live calls do not need this local transcription path.

Start the API:

```bash
uvicorn reqANA.api:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Useful Endpoints

- `GET /health`
- `POST /requirements/from-text`
- `POST /requirements/from-file`
- `POST /requirements/from-voice`
- `POST /requirements/from-mixed`
- `POST /veris/requirement-agent`
