# RBSoftware Monorepo Foundation

## Structure
- `backend`: FastAPI + SQLModel + Alembic + pytest foundation
- `frontend`: Next.js + TypeScript + Tailwind + shadcn/ui foundation
- `infra`: nginx reverse proxy configs
- `compose.dev.yml`: local development stack
- `compose.prod.yml`: production-oriented stack

## Backend quick commands
- `make -C backend install`
- `make -C backend lint`
- `make -C backend test`
- `make -C backend run`

## Frontend quick commands
- `cd frontend && npm install`
- `cd frontend && npm run dev`
- `cd frontend && npm run lint`

## Run with Docker Compose
- Dev: `docker compose -f compose.dev.yml up --build`
- Prod: `docker compose -f compose.prod.yml up --build -d`
