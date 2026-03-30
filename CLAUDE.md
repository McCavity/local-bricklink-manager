# CLAUDE.md

## Project Overview

Local BrickLink Manager — a Flask web app for tracking BrickLink orders locally. The user is a BrickLink buyer.

## Tech Stack

- Python 3.10+ / Flask / SQLAlchemy / SQLite
- BrickLink API with OAuth 1.0 via requests-oauthlib
- Jinja2 templates, vanilla JS, BrickLink-inspired CSS

## Key Conventions

- API credentials are in `.env` (never committed)
- BrickLink API: `direction=out` for buyer orders
- `local_status` on orders is a local overlay (NULL / received / checked), never sent to BrickLink
- Images are loaded via BrickLink CDN URLs, not stored locally
- Rate limit: 5000 API calls/day

## Running

```bash
python run.py  # starts Flask on localhost:5000
```

## Project Structure

- `app/` — Flask application
  - `models.py` — SQLAlchemy models (orders, order_items, checklist_entries, feedback, sync_log)
  - `bricklink/` — API client, sync logic, feedback
  - `routes/` — Flask blueprints (orders, checklist, stats, sync)
  - `templates/` — Jinja2 templates
  - `static/` — CSS and JS
- `config.py` — loads .env configuration
- `run.py` — entry point
