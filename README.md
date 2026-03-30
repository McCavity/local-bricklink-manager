# Local BrickLink Manager

A local web application for managing BrickLink orders. Syncs your order history via the BrickLink API and stores it locally so it persists after BrickLink purges old orders.

## Features

- **Order Sync** — Pull all your BrickLink orders (including filed/completed/purged) into a local SQLite database
- **Order Checklist** — Go through received orders item-by-item to verify deliveries, with mismatch/missing tracking
- **Order Lifecycle** — Batch-mark orders as received, mark completed via BrickLink API, leave feedback (with duplicate protection)
- **Statistics** — Average lot/piece prices, total spending, shipping costs, seller breakdown — all normalized to EUR
- **Foreign Currency Support** — Orders placed in non-EUR stores are automatically converted using BrickLink's own exchange rates
- **Persistent Storage** — Orders are stored locally and never lost, even after BrickLink purges them
- **Sortable Tables** — Click any column header to sort; sticky headers stay visible when scrolling

## Setup

### 1. Prerequisites

- Python 3.10+

### 2. Get BrickLink API Credentials

1. Go to [BrickLink API Registration](https://www.bricklink.com/v2/api/register_consumer.page)
2. Register a new consumer
3. For IP Address, enter `0.0.0.0` if you have a dynamic IP (this allows access from any IP — keep your credentials secure!)
4. Note your Consumer Key, Consumer Secret, Token Value, and Token Secret

### 3. Install

```bash
# Clone the repository
git clone https://github.com/McCavity/local-bricklink-manager.git
cd local-bricklink-manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env with your BrickLink API credentials
```

### 4. Run

```bash
python run.py
```

Open http://localhost:5001 in your browser.

> **Note:** Port 5000 is used by AirPlay Receiver on macOS. This app uses port 5001 by default.

## Usage

1. **Sync Orders** — Click "Sync Orders" in the navbar (incremental) or "Full Sync" on the orders page to pull orders from BrickLink. Both modes fetch filed (archived) orders as well.
2. **Review Orders** — Browse your order list, filter by BrickLink status or local status, sort by clicking column headers.
3. **Mark Received** — Select orders via checkboxes and batch-mark them as received when packages arrive.
4. **Check Items** — Open an order's checklist to verify each item. Use "OK" for correct items, enter a different quantity for mismatches. View a summary of correct/missing/mismatched items.
5. **Complete & Feedback** — Mark orders as completed on BrickLink and leave feedback (Praise/Neutral/Complaint). The feedback form is hidden once feedback has been submitted.

## How Sync Works

- **Incremental Sync** (navbar button): Fetches both active and filed orders from BrickLink. Only fetches item details for orders not yet in the local database.
- **Full Sync**: Same as incremental, but also re-fetches item details for all non-purged orders.
- Orders with status `COMPLETED`, `PURGED`, or `CANCELLED` are automatically marked as "checked" locally on first import.
- Item details are not available for `PURGED` orders (BrickLink has removed them).
- Feedback status is checked via API for non-purged orders on first import.

## Tech Stack

- **Backend**: Python, Flask, Flask-SQLAlchemy
- **Database**: SQLite (auto-created, auto-migrated)
- **API**: BrickLink REST API with OAuth 1.0 (via requests-oauthlib)
- **Frontend**: Server-side rendered HTML (Jinja2), vanilla JavaScript

## License

MIT
