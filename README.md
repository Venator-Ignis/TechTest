# Package Sync Monorepo - Operation Ghost Hunter

A distributed package tracking system for 2,000 solar-powered smart lockers that sync package drop-off data from edge devices (SQLite) to a central server (Postgres).

## Architecture

**Locker (Edge):** Python service using Peewee ORM + SQLite for local package storage  
**Server (Central):** Go API using Gin + GORM + Postgres for centralized package tracking  
**Sync Protocol:** Polling-based with retry logic, idempotency, and two-phase commit

## Key Features

- **UUID-based tracking IDs** - Collision-resistant across 2,000+ distributed lockers
- **Idempotent sync** - Duplicate requests handled gracefully via upsert (ON CONFLICT)
- **Retry logic** - Up to 5 attempts with tracking to prevent infinite loops
- **Two-phase commit** - Server ACK verification before marking packages as synced
- **Audit trail** - Full chain of custody with locker_id, drop_off_timestamp, sync_attempt_timestamp, server_received_at
- **Network resilience** - Handles timeouts, crashes, and offline periods
- **Battery optimization** - 30-second sync interval for solar-powered devices

## Setup & Installation

### 1) Start Postgres

From repo root:

```bash
docker compose up -d
```

### 2) Run Server (Go)

```bash
cd server
go mod tidy
go run .
```

Server listens on `http://localhost:8080` and exposes `POST /sync`.

### 3) Run Locker (Python)

```bash
cd locker
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

### Drop off a package (creates local record)

```bash
cd locker
.venv/bin/python -m app.dropoff PKG-1001
```

Output: `Package queued: id=1, tracking_id=PKG-1001, locker=LOCKER-001`

### Run sync worker (syncs to central server)

```bash
cd locker
.venv/bin/python -m app.sync_worker
```

The worker polls unsynced packages from SQLite every 30 seconds and sends them to `POST /sync`.

## Testing

### Test 1: Basic Sync

```bash
# Terminal 1: Start server
cd server && go run .

# Terminal 2: Drop package and sync
cd locker
.venv/bin/python -m app.dropoff TEST-001
.venv/bin/python -c "from app.sync_worker import sync_once; sync_once()"
```

Expected output: `✓ Synced TEST-001`

### Test 2: Idempotency

```bash
# Send the same package twice
curl -X POST http://localhost:8080/sync \
  -H "Content-Type: application/json" \
  -d '{"tracking_id":"DUP-001","locker_id":"LOCKER-001","status":"pending","drop_off_timestamp":"2026-02-20T18:00:00Z","sync_attempt_timestamp":"2026-02-20T18:00:00Z","last_sync_attempt":0}'

curl -X POST http://localhost:8080/sync \
  -H "Content-Type: application/json" \
  -d '{"tracking_id":"DUP-001","locker_id":"LOCKER-001","status":"pending","drop_off_timestamp":"2026-02-20T18:00:00Z","sync_attempt_timestamp":"2026-02-20T18:01:00Z","last_sync_attempt":1}'

# Verify only one record exists
docker exec package-postgres psql -U postgres -d packages \
  -c "SELECT COUNT(*) FROM packages WHERE tracking_id='DUP-001';"
```

Expected: `count = 1`

### Test 3: Retry Logic

```bash
# Drop package
cd locker
.venv/bin/python -m app.dropoff RETRY-001

# Stop server (simulate network failure)
# Run sync - will fail and increment retry counter
.venv/bin/python -c "from app.sync_worker import sync_once; sync_once()"

# Check retry count increased
.venv/bin/python -c "from app.models import Package, init_db; init_db(); p = Package.get(Package.tracking_id=='RETRY-001'); print(f'Attempts: {p.sync_attempt_count}, Status: {p.status}')"

# Restart server and sync again - should succeed
.venv/bin/python -c "from app.sync_worker import sync_once; sync_once()"
```

Expected: Status changes from `pending` to `synced` after server restart.

### Test 4: Verify in Postgres

```bash
docker exec package-postgres psql -U postgres -d packages \
  -c "SELECT tracking_id, locker_id, status, last_sync_attempt, server_received_at FROM packages ORDER BY server_received_at DESC LIMIT 5;"
```

## Configuration

### Locker (.env)

```env
SQLITE_PATH=./locker.db
SERVER_SYNC_URL=http://localhost:8080/sync
SYNC_INTERVAL_SECONDS=30
LOCKER_ID=LOCKER-001
```

### Server (.env)

```env
PORT=8080
DATABASE_URL=postgres://postgres:postgres@localhost:5432/packages?sslmode=disable
```

## Database Schemas

### SQLite (Locker)

```
Package:
  - id (AutoField)
  - tracking_id (TextField, unique, UUID4)
  - locker_id (TextField)
  - status (TextField: "pending" | "synced")
  - drop_off_timestamp (DateTimeField)
  - sync_attempt_count (IntegerField)
  - last_sync_attempt (DateTimeField, nullable)
```

### Postgres (Server)

```
packages:
  - id (bigint, primary key)
  - tracking_id (text, unique index)
  - locker_id (text, index)
  - status (text)
  - drop_off_timestamp (timestamptz)
  - sync_attempt_timestamp (timestamptz)
  - server_received_at (timestamptz, auto)
  - last_sync_attempt (bigint)
```

## API Endpoints

### POST /sync

Receives package sync requests from lockers.

**Request:**
```json
{
  "tracking_id": "PKG-1001",
  "locker_id": "LOCKER-001",
  "status": "pending",
  "drop_off_timestamp": "2026-02-20T18:00:00Z",
  "sync_attempt_timestamp": "2026-02-20T18:05:00Z",
  "last_sync_attempt": 0
}
```

**Response (201):**
```json
{
  "ack": true,
  "tracking_id": "PKG-1001",
  "server_received_at": "2026-02-20T18:05:01.123Z"
}
```

## Troubleshooting

**Packages not syncing:**
- Check server is running: `curl http://localhost:8080/sync`
- Check Postgres is running: `docker compose ps`
- Check locker logs for network errors

**Schema mismatch errors:**
- Recreate SQLite: `rm locker/locker.db && python -c "from app.models import init_db; init_db()"`
- Recreate Postgres: `docker exec package-postgres psql -U postgres -d packages -c "DROP TABLE packages CASCADE;"`

**Port 8080 already in use:**
- Find process: `lsof -i :8080`
- Kill it: `kill <PID>`
