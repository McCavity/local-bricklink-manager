# CLAUDE.md

## Project Overview

Local BrickLink Manager — a Flask web app for tracking BrickLink orders locally. The user is a BrickLink buyer.

## Tech Stack

- Python 3.10+ / Flask / Flask-SQLAlchemy / SQLite
- BrickLink API with OAuth 1.0 via requests-oauthlib
- Jinja2 templates, vanilla JS, BrickLink-inspired CSS

## Key Conventions

- API credentials are in `.env` (never committed)
- BrickLink API: `direction=out` for buyer orders, `filed=True` to include archived orders
- BrickLink returns statuses in UPPERCASE: `COMPLETED`, `PURGED`, `CANCELLED`, `SHIPPED`, etc.
- `local_status` on orders is a local overlay (NULL / received / checked), never sent to BrickLink
- COMPLETED/PURGED/CANCELLED orders are auto-marked `local_status='checked'` on import
- Foreign currency: BrickLink provides `cost` (store currency) and `disp_cost` (buyer currency); we use `disp_cost` as primary values
- Images are loaded via BrickLink CDN URLs, not stored locally
- Rate limit: 5000 API calls/day
- Schema migrations are handled via `_migrate()` in `database.py` (adds columns to existing tables)

## Running

```bash
python run.py  # starts Flask on localhost:5001
```

## Project Structure

- `app/` — Flask application
  - `models.py` — SQLAlchemy models (orders, order_items, checklist_entries, feedback, sync_log)
  - `database.py` — DB init, auto-migration for new columns
  - `bricklink/` — API client, sync logic, feedback, currency conversion
  - `routes/` — Flask blueprints (orders, checklist, stats, sync)
  - `templates/` — Jinja2 templates
  - `static/` — CSS and JS (including sortable.js for client-side table sorting)
- `config.py` — loads .env configuration
- `run.py` — entry point
