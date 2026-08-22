# Backend — FastAPI

Custom agent loop + MCP client layer + learner-state services live here.

## Run locally

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then fill in values
uvicorn app.main:app --reload --port 8000
```

Check it: `curl http://localhost:8000/health`

## Layout (grows each step)

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py       # FastAPI app + health check
│   └── config.py     # settings from env / .env
├── requirements.txt
└── .env.example
```
