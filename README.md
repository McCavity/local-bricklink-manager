# Local BrickLink Manager

A local web application for managing BrickLink orders. Syncs your order history via the BrickLink API and stores it locally so it persists after BrickLink purges old orders.

## Features

- **Order Sync** — Pull all your BrickLink orders and items into a local SQLite database
- **Order Checklist** — Go through received orders item-by-item to verify deliveries
- **Order Lifecycle** — Batch-mark orders as received, mark completed via BrickLink API, leave feedback
- **Statistics** — Average lot/piece prices, total spending, shipping costs, seller breakdown
- **Persistent Storage** — Orders are stored locally and never lost, even after BrickLink purges them

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

Open http://localhost:5000 in your browser.

## Usage

1. **Sync Orders** — Click "Sync Orders" to pull your latest orders from BrickLink
2. **Review Orders** — Browse your order list, filter by status
3. **Mark Received** — Select orders and batch-mark them as received when packages arrive
4. **Check Items** — Open an order's checklist to verify each item against what was delivered
5. **Complete & Feedback** — Mark orders as completed on BrickLink and leave feedback

## Tech Stack

- **Backend**: Python, Flask
- **Database**: SQLite via SQLAlchemy
- **API**: BrickLink REST API with OAuth 1.0
- **Frontend**: Server-side rendered HTML (Jinja2), vanilla JavaScript

## License

MIT
