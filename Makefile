# Convenience targets for local dev.
# Run these on YOUR machine (the build sandbox has no internet access).
#
# Load DATABASE_URL from backend/.env for db targets.
-include backend/.env
export

.PHONY: help backend-setup backend-run db-migrate frontend-setup frontend-run

help:
	@echo "Targets:"
	@echo "  backend-setup   create venv + install backend deps + seed .env"
	@echo "  backend-run     run FastAPI (uvicorn) on :8000"
	@echo "  db-migrate      apply infra/db/init/*.sql to \$$DATABASE_URL"
	@echo "  frontend-setup  npm install (after the Next.js step)"
	@echo "  frontend-run    run Next.js dev server on :3000"

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

# --- Database ------------------------------------------------------------
# Applies the numbered SQL migrations in order. Requires a running Postgres
# with pgvector and DATABASE_URL set in backend/.env. (Docker Compose to
# stand one up locally arrives in Step 6.)
db-migrate:
	@for f in infra/db/init/*.sql; do \
		echo "applying $$f"; \
		psql "$(DATABASE_URL)" -f "$$f" || exit 1; \
	done
	@echo "Migrations applied."

# --- Frontend (available after the Next.js step) -------------------------
frontend-setup:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev
