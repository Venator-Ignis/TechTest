# Package Sync Monorepo

Monorepo structure:

- `locker/` - Python service (Peewee + SQLite) to queue and sync packages
- `server/` - Go API (Gin + GORM) to receive package sync events
- `docker-compose.yml` - Postgres database for the Go server

## 1) Start Postgres

From repo root:

```bash
docker compose up -d
```

## 2) Run server (Go)

```bash
cd server
go mod tidy
go run .
```

Server listens on `http://localhost:8080` and exposes `POST /sync`.

## 3) Run locker (Python)

```bash
cd locker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.dropoff PKG-1001
python -m app.sync_worker
```

The worker polls unsynced packages from SQLite and sends them to `POST /sync`.
