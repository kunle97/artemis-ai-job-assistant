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

## Status

Early setup / MVP in progress.