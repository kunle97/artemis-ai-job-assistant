# Artemis

Artemis is an AI-assisted job search and application copilot.

It helps users:
- upload and parse resumes
- define job search preferences
- find relevant jobs from supported ATS sources
- score job fit
- draft application answers
- assist with repetitive application workflows
- auto fills application forms to the best of its ability witht he least amount of user intervention

## Planned Stack

- Next.js
- FastAPI
- Postgres
- Redis
- Playwright
- OpenAI-compatible LLM provider

## Project Structure

- `apps/web` - frontend
- `apps/api` - backend API
- `apps/worker` - background jobs
- `docs/` - architecture and product docs

## Getting Started

### Backend API

```bash
cd services/api

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

### Worker Services

Run the periodic feed scan worker and Celery beat scheduler with Docker Compose.

```bash
docker compose up -d --build postgres redis worker beat
```

The scan cadence is controlled by `JOB_SCAN_INTERVAL_HOURS` and defaults to `24`.
Set it before starting Compose if you want a different interval.

### Running Tests

```bash
cd services/api
source venv/bin/activate

# Run all tests
python -m pytest tests/

# Run unit tests only
python -m pytest tests/unit/

# Run API tests only
python -m pytest tests/api/

# Run with verbose output
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing
```

## Dev Scripts

All scripts live in `services/api/scripts/` and must be run from `services/api/` with the virtualenv active.

### Feed Scanner

Scan ATS job boards and log all matching jobs in detail.

```bash
cd services/api
source venv/bin/activate

# Scan all 72 configured boards
python scripts/run_feed_scan.py

# Scope to a single ATS
python scripts/run_feed_scan.py --source ashby

# Filter to specific companies
python scripts/run_feed_scan.py --companies stripe,linear,ramp

# Filter by job title keywords (OR logic)
python scripts/run_feed_scan.py --keywords "engineer,backend,python"

# Summary table only — skip per-job detail
python scripts/run_feed_scan.py --summary-only

# Persist new jobs to DB for a user
python scripts/run_feed_scan.py --persist --user-id <uuid>
```

### Pipeline Fill Runner

Authenticate against a running API instance, create applications, and run the automation pipeline end-to-end.
Configure the target URLs in `scripts/constants.py` before running.

```bash
cd services/api
source venv/bin/activate

# Run with local resume
python scripts/test_fill_runner.py

# Run with the latest S3-backed resume
python scripts/test_fill_runner.py --storage s3

# Clear screenshots before running
python scripts/test_fill_runner.py --clear-screenshots

# Enable auto-submit after a successful fill
python scripts/test_fill_runner.py --enable-submit

# Combine flags
python scripts/test_fill_runner.py --clear-screenshots --storage s3 --enable-submit
```

Results are saved per-run under `scripts/test_results/<TIMESTAMP>/`.

### API Checks Suite

Run the full API validation suite (auth, storage preflight, resume upload, async dispatch,
submission guardrails, feed checks, and migrations) from one command.

```bash
cd services/api
source venv/bin/activate

python3 scripts/run_api_checks.py --continue-on-error --storage-args=--storage-backend\ local --feed-args=--skip-scan
```

## Status

Early setup / MVP in progress.