# TranscriptOps API

Extract action items, deal signals, and executive summaries from any meeting or
call transcript. One API call replaces 30 minutes of manual note-taking.

Built for Make, n8n, Zapier, and direct CRM integrations.

---

## Endpoints

| Method | Path                    | What it does                                          |
|--------|-------------------------|-------------------------------------------------------|
| GET    | `/health`               | Status check (required by RapidAPI)                   |
| POST   | `/transcript/extract`   | Action items + sentiment + key topics                 |
| POST   | `/transcript/summarize` | N-bullet executive summary + one-liner TL;DR          |
| POST   | `/deal/signals`         | Budget, timeline, objections, deal score (0–100)      |

---

## Local setup (5 minutes)

```bash
git clone https://github.com/ahenali/transcriptops-api
cd transcriptops-api

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env — add your OPENAI_API_KEY and at least one VALID_API_KEYS value

uvicorn app.main:app --reload
```

Interactive docs: http://localhost:8000/docs

---

## Running tests

```bash
pytest tests/ -v
```

Tests mock OpenAI — no tokens consumed. All tests should pass before deploy.

---
