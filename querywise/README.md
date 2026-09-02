# QueryWise — Intelligent Database Query Optimizer & Index Advisor

QueryWise helps small dev teams (without a dedicated DBA) find slow SQL
queries, understand *why* they're slow, and get safe, explainable index
recommendations — without ever touching their real data or schema.

It connects to a **real 12-table PostgreSQL database** and, for any
read-only `SELECT` you paste in, runs `EXPLAIN` / `EXPLAIN ANALYZE` and turns
the raw execution plan into:

- A **0–100 Query Health Score**
- A plain-English breakdown of expensive operations (sequential scans, sorts, joins…)
- **Index recommendations** based on your `WHERE` / `JOIN` / `ORDER BY` / `GROUP BY` columns — checked against indexes that already exist, so duplicates are never suggested
- A **What-If Simulator** that estimates the improvement of a proposed index — without ever creating it
- A **Database Explorer** showing the real tables, columns, keys, and indexes QueryWise is connected to
- A **dashboard** with trends, most-frequently-analyzed tables, and history across all analyzed queries

---

## Tech Stack

| Layer     | Tech |
|-----------|------|
| Frontend  | React + Vite + Tailwind CSS + Axios + Recharts |
| Backend   | Python + FastAPI + SQLAlchemy + psycopg2 |
| Database  | PostgreSQL |
| Optional  | Docker + Docker Compose |

```
React Frontend  →  FastAPI Backend  →  PostgreSQL Database
```

---

## The Demo Database (12 tables)

`database/schema.sql` creates a realistic e-commerce / company-management
schema:

```
departments → employees
customers → addresses
categories → products ← suppliers
customers → orders → order_items ← products
orders → payments
orders → shipments
customers + products → reviews
```

| Table | Approx. rows |
|---|---|
| departments | 10 |
| employees | 800 |
| customers | 1,500 |
| addresses | 1,800 |
| categories | 25 |
| suppliers | 80 |
| products | 800 |
| orders | 8,000 |
| order_items | 24,000 |
| payments | 8,000 |
| shipments | 6,000 |
| reviews | 5,000 |

**Some foreign keys are indexed** (`orders.customer_id`, `order_items.order_id`,
`order_items.product_id`, `products.category_id`, `products.supplier_id`,
`payments.order_id`, `shipments.order_id`, `addresses.customer_id`,
`reviews.customer_id`, `reviews.product_id`) so those queries show fast Index
Scans.

**Some commonly-filtered columns are deliberately left unindexed** —
`employees.department_id`, `employees.salary`, `customers.city`,
`customers.created_at`, `products.price`, `orders.status`, `orders.order_date`
— so the Index Advisor has real Sequential Scans to detect and fix.

---

## Project Structure

```
querywise/
├── database/
│   ├── schema.sql       # The 12-table demo schema (target database)
│   ├── seed.sql         # Realistic sample data (idempotent — safe to re-run)
│   └── app_schema.sql   # QueryWise's own history/recommendation tables (optional; auto-created by the backend too)
│
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entrypoint
│   │   ├── database.py             # App DB (SQLAlchemy) + Target DB (psycopg2, read-only)
│   │   ├── scheduler.py            # Background slow-query scan (APScheduler)
│   │   ├── api/                    # analyze.py, history.py, dashboard.py, recommendations.py, explorer.py
│   │   ├── services/               # validator, explain parser, health score, index advisor, simulator, db_explorer
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   └── schemas/                # Pydantic request/response schemas
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── pages/                  # Dashboard, QueryAnalyzer, QueryHistory, IndexRecommendations, QueryDetails, DatabaseExplorer
│   │   ├── components/             # Sidebar, Card, PlanTree, HealthScoreBadge, Feedback states
│   │   ├── services/api.js         # Axios client
│   │   ├── App.jsx / main.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── .env.example
│   └── Dockerfile
│
├── docker-compose.yml
└── README.md
```

---

## Option A: Run with Docker Compose (easiest)

Requires Docker + Docker Compose installed.

```bash
cd querywise
docker compose up --build
```

This starts:
- **PostgreSQL** on `localhost:5432` — automatically initialized with `database/schema.sql`, then `database/seed.sql`, then `database/app_schema.sql` on first boot
- **FastAPI backend** on `http://localhost:8000` (docs at `http://localhost:8000/docs`)
- **React frontend** on `http://localhost:5173`

Open `http://localhost:5173` — the database is already fully seeded, so you
can analyze real queries immediately.

To stop: `Ctrl+C`, then `docker compose down` (add `-v` to also wipe the
database volume and reseed fresh next time).

---

## Option B: Run locally without Docker (step by step)

### 1. Install PostgreSQL

- **Windows**: download the installer from postgresql.org/download/windows, run it, and remember the password you set for the `postgres` user.
- **macOS**: `brew install postgresql@16` then `brew services start postgresql@16`
- **Linux (Debian/Ubuntu)**: `sudo apt install postgresql postgresql-contrib`

Verify it's running:
```bash
psql --version
```

### 2. Create the database and load the schema + data

```bash
# Create the database
createdb querywise_demo
# (Windows, if createdb isn't on PATH: use pgAdmin, or run
#  psql -U postgres -c "CREATE DATABASE querywise_demo;")

# From the querywise/ project root:
psql -U postgres -d querywise_demo -f database/schema.sql
psql -U postgres -d querywise_demo -f database/seed.sql

# Optional — only needed if you want the app's history tables to exist
# before the backend's first run (the backend also creates them automatically):
psql -U postgres -d querywise_demo -f database/app_schema.sql
```

You should see `CREATE TABLE` / `CREATE INDEX` output from `schema.sql`, and
`INSERT 0 <count>` lines from `seed.sql` (e.g. `INSERT 0 8000` for orders).

**Re-running is safe**: `schema.sql` drops and recreates every table, and
`seed.sql` starts with `TRUNCATE ... RESTART IDENTITY CASCADE`, so running
either script again never creates duplicates.

### 3. Configure and start the backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # Windows: copy .env.example .env
```

Open `backend/.env` and confirm the values match your PostgreSQL setup
(the defaults assume user `postgres`, password `postgres`, database
`querywise_demo`, host `localhost`, port `5432` — edit if yours differ):

```
TARGET_DB_HOST=localhost
TARGET_DB_PORT=5432
TARGET_DB_NAME=querywise_demo
TARGET_DB_USER=postgres
TARGET_DB_PASSWORD=postgres

APP_DB_HOST=localhost
APP_DB_PORT=5432
APP_DB_NAME=querywise_demo
APP_DB_USER=postgres
APP_DB_PASSWORD=postgres

SLOW_QUERY_THRESHOLD_MS=500
FRONTEND_ORIGIN=http://localhost:5173
```

Then start the server (always run this from inside the `backend/` folder):

```bash
uvicorn app.main:app --reload --port 8000
```

Confirm it worked by opening **http://localhost:8000/docs** in a browser —
you should see the interactive API docs.

> **Note on CORS:** the backend accepts requests from *any* `http://localhost:<port>`
> or `http://127.0.0.1:<port>` origin automatically, so it doesn't matter if
> Vite happens to start your frontend on 5173, 5174, or another port.

### 4. Start the frontend (React + Vite)

In a **new terminal**:

```bash
cd frontend
npm install
cp .env.example .env            # Windows: copy .env.example .env
npm run dev
```

Open the URL Vite prints (usually **http://localhost:5173**).

### 5. Test it with the Example Queries

On the **Query Analyzer** page, click **Example Queries** to expand a list of
15 pre-written queries covering every feature: sequential scans, `WHERE`
filters, single and multi-table `JOIN`s, `LEFT JOIN`, `ORDER BY`, `GROUP BY`,
aggregates (`COUNT`, `SUM`, `AVG`), date ranges, and multi-condition filters.
Click one to load it into the editor, then click **Analyze Query**.

Try, for example:

```sql
-- Triggers a sequential scan (department_id is intentionally unindexed)
SELECT * FROM employees WHERE department_id = 3;
```

```sql
-- Multi-table JOIN across 4 tables
SELECT o.id, c.first_name, p.name, oi.quantity
FROM orders o
JOIN customers c ON o.customer_id = c.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;
```

Then visit **Database Explorer** to see the real, live table list, row
counts, columns, primary/foreign keys, and existing indexes — proof
QueryWise is reading an actual PostgreSQL database, not fixtures.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/analyze` | Validate + analyze a SQL query, save to history |
| POST | `/api/simulate-index` | Run a safe what-if simulation for a proposed index |
| GET  | `/api/history` | List past analyses (supports `search`, `slow_only`, `limit`) |
| GET  | `/api/history/{id}` | Full detail for one analysis |
| GET  | `/api/dashboard` | Summary stats (incl. total tables, most-analyzed tables) + trend data |
| GET  | `/api/recommendations` | All index recommendations across all queries |
| GET  | `/api/explorer/tables` | Every table in the target database + live row counts |
| GET  | `/api/explorer/tables/{table_name}` | Columns, primary key, foreign keys, indexes for one table |
| GET  | `/api/health` | Simple health check |

Full interactive docs (Swagger UI) are available at `http://localhost:8000/docs`
once the backend is running.

---

## Safety Guarantees

QueryWise is built to be safe to run against a real database:

- ✅ Only `SELECT` statements are ever accepted (validated with `sqlparse` + a keyword blocklist covering `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `TRUNCATE`, `GRANT`, `REVOKE`, `EXECUTE`, `CALL`, `COPY`, `VACUUM`, `REINDEX`, `MERGE`, `REPLACE`)
- ✅ Stacked / multi-statement queries (e.g. `SELECT 1; DROP TABLE x;`) are rejected outright
- ✅ The connection used to run `EXPLAIN` is set to PostgreSQL `READ ONLY` at the session level as defense-in-depth
- ✅ Index recommendations are **only ever shown as SQL text** — QueryWise never runs `CREATE INDEX` automatically
- ✅ The What-If Simulator uses either PostgreSQL's `hypopg` extension (session-local hypothetical indexes, never persisted) or a clearly-labeled heuristic estimate — it never modifies real tables or indexes
- ✅ The Database Explorer only ever runs read-only `SELECT` / `information_schema` / `pg_catalog` lookups, with table names validated against the real table list and safely quoted before use
- ✅ Raw Python/SQLAlchemy/psycopg2 tracebacks are never sent to the frontend — a global exception handler converts everything into a friendly message

---

## Notes on the Query Health Score

The score starts at 100 and simple, explainable deductions are applied for:
sequential scans, high planner cost, large estimated row counts, expensive
sorts, costly nested loops, and joins. See
`backend/app/services/health_score.py` for the exact rules — they're
intentionally simple heuristics rather than a black box, so you can read and
tweak them.

```
90–100 → Excellent
70–89  → Good
40–69  → Needs Improvement
0–39   → Poor
```

---

## Troubleshooting

- **"Could not reach the QueryWise server"** — make sure the backend is
  running, and check the browser console for the exact error. A CORS error
  mentioning a specific origin means the frontend and backend are running
  but the browser blocked the request — this should no longer happen since
  the backend allows any `localhost` port automatically; if you still see
  it, double-check you're running the updated `backend/app/main.py`.
- **"One or more tables in your query do not exist"** — make sure you ran
  both `database/schema.sql` and `database/seed.sql` against the database
  your backend's `.env` points to.
- **Connection refused to PostgreSQL** — verify `TARGET_DB_HOST` /
  `TARGET_DB_PORT` in `backend/.env` match how PostgreSQL is actually
  running (`localhost` for a local install, `db` for Docker Compose).
- **`.env` changes don't seem to take effect** — always run `uvicorn` from
  inside the `backend/` folder (`cd backend` first), and restart it after
  editing `.env` — environment variables are only read once, at startup.
- **Dashboard shows "Total Tables: 0" or Explorer is empty** — this means
  the backend can't reach the target database; check `TARGET_DB_*` values
  in `backend/.env` and confirm PostgreSQL is running.
