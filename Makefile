# Convenience targets for local dev.
# Run these on YOUR machine (the build sandbox has no internet access).

.PHONY: backend-setup backend-run frontend-setup frontend-run

# --- Backend -------------------------------------------------------------
backend-setup:
	cd backend && python3 -m venv .venv && \
	. .venv/bin/activate && \
	pip install --upgrade pip && \
	pip install -r requirements.txt && \
	cp -n .env.example .env || true
	@echo "Backend ready. Edit backend/.env, then: make backend-run"

backend-run:
	cd backend && . .venv/bin/activate && \
	uvicorn app.main:app --reload --port 8000

# --- Frontend (available after the Next.js step) -------------------------
frontend-setup:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev
