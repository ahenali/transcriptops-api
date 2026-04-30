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

## Deployment to Render.com (free tier)

1. Push to GitHub
2. Go to render.com → New → Web Service → connect your repo
3. Render auto-detects `render.yaml` — click Deploy
4. Add env vars in the Render dashboard (OPENAI_API_KEY, VALID_API_KEYS)
5. Your live URL: `https://transcriptops-api.onrender.com`

Health check: `GET https://your-app.onrender.com/health`

---

## Example requests

### Extract action items

```bash
curl -X POST https://your-app.onrender.com/transcript/extract \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key_here" \
  -d '{
    "transcript": "John: We need the Q3 report by Friday. Sarah will handle the analysis. Also, John will schedule a follow-up call with the client next week.",
    "language": "en"
  }'
```

Response:
```json
{
  "action_items": [
    {"task": "Complete Q3 report", "owner": "Sarah", "due": "Friday"},
    {"task": "Schedule follow-up call with client", "owner": "John", "due": "next week"}
  ],
  "summary": "The team discussed Q3 deliverables with Sarah owning the analysis and John handling client outreach.",
  "sentiment": "neutral",
  "key_topics": ["Q3 report", "client follow-up", "deadlines"],
  "word_count": 42,
  "model_used": "gpt-4o-mini"
}
```

### Summarize a transcript

```bash
curl -X POST https://your-app.onrender.com/transcript/summarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key_here" \
  -d '{
    "transcript": "...",
    "bullet_count": 5
  }'
```

### Extract deal signals

```bash
curl -X POST https://your-app.onrender.com/deal/signals \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_key_here" \
  -d '{
    "transcript": "Prospect: Our budget is around $50K but we need board approval by end of Q3. The price feels a bit high compared to what we have now..."
  }'
```

Response:
```json
{
  "budget_mentioned": "$50,000",
  "timeline": "end of Q3",
  "decision_maker": "board",
  "deal_stage": "evaluation",
  "objections": ["Price is high compared to current solution", "Requires board approval"],
  "next_steps": [],
  "deal_score": 48,
  "model_used": "gpt-4o-mini"
}
```

---

## Generating API keys for customers

```python
import secrets
print(secrets.token_urlsafe(32))
# e.g. "k_ZtX9mQ2vL8eRpYjN4wB7cF1sK3oA6hD"
```

Add new keys to your VALID_API_KEYS env var (comma-separated) and redeploy.

For scale: replace the env var approach with a Supabase table + key lookup.

---

## RapidAPI listing checklist

- [ ] API live on Render with /health returning 200
- [ ] Add RAPIDAPI_PROXY_SECRET from your RapidAPI provider dashboard to env vars
- [ ] Set base URL in RapidAPI to your Render URL
- [ ] Add all 3 endpoints with descriptions and example payloads
- [ ] Set pricing tiers (Free: 50/mo, Basic: $15/500, Pro: $39/2000)
- [ ] Add code examples in Python, JS, cURL for each endpoint
- [ ] Publish and post in Make + n8n communities

---

## Cost estimate

| Monthly calls | OpenAI cost (gpt-4o-mini) | Your revenue at $15/user | Margin |
|---------------|---------------------------|--------------------------|--------|
| 1,000         | ~$0.15                    | $15 (1 user)             | 99%    |
| 10,000        | ~$1.50                    | $75 (5 users)            | 98%    |
| 100,000       | ~$15                      | $390 (26 users)          | 96%    |

gpt-4o-mini costs ~$0.15 per 1M input tokens. A 1,000-word transcript ≈ 1,300 tokens.

---

## File structure

```
transcriptops/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app, routes, middleware
│   ├── auth.py        # API key authentication
│   ├── models.py      # Pydantic request/response schemas
│   ├── ai.py          # OpenAI service layer
│   └── prompts.py     # All prompt templates
├── tests/
│   └── test_endpoints.py
├── requirements.txt
├── render.yaml
├── .env.example
└── README.md
```
