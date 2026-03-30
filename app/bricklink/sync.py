import json
import logging
from datetime import datetime, timezone

from app.database import db
from app.models import Order, OrderItem, SyncLog
from app.bricklink.client import BrickLinkClient, BrickLinkAPIError

logger = logging.getLogger(__name__)


def get_client(app):
    """Create a BrickLinkClient from app config."""
    return BrickLinkClient(
        consumer_key=app.config["BRICKLINK_CONSUMER_KEY"],
        consumer_secret=app.config["BRICKLINK_CONSUMER_SECRET"],
        token=app.config["BRICKLINK_TOKEN"],
        token_secret=app.config["BRICKLINK_TOKEN_SECRET"],
    )


def _parse_date(date_str):
    """Parse BrickLink date string to datetime."""
    if not date_str:
        return datetime.now(timezone.utc)
    # BrickLink uses format like "2024-01-15T10:30:00.000Z" or similar
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def _extract_cost(cost_dict, key):
    """Safely extract a float from a BrickLink cost dictionary."""
    if not cost_dict:
        return 0.0
    val = cost_dict.get(key, "0")
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def upsert_order(order_data):
    """Insert or update an order from API data."""
    order_id = order_data.get("order_id")
    order = db.session.get(Order, order_id)

    cost = order_data.get("cost", {})
    disp_cost = order_data.get("disp_cost", {})
    shipping = order_data.get("shipping", {})

    subtotal = _extract_cost(cost, "subtotal")
    grand_total = _extract_cost(cost, "grand_total")
    shipping_cost = _extract_cost(cost, "shipping")

    if order is None:
        order = Order(order_id=order_id)
        db.session.add(order)

    order.buyer_name = order_data.get("buyer_name", "")
    order.seller_name = order_data.get("seller_name", "")
    order.store_name = order_data.get("store_name", "")
    order.order_date = _parse_date(order_data.get("date_ordered"))
    order.status = order_data.get("status", "")
    order.total_count = order_data.get("total_count", 0)
    order.unique_count = order_data.get("unique_count", 0)
    order.subtotal = subtotal
    order.grand_total = grand_total
    order.shipping_cost = shipping_cost
    order.currency_code = disp_cost.get("currency_code", "EUR") if disp_cost else "EUR"
    order.payment_method = order_data.get("payment", {}).get("method", "") if order_data.get("payment") else ""
    order.remarks = order_data.get("remarks", "")
    order.raw_json = json.dumps(order_data)
    order.synced_at = datetime.now(timezone.utc)

    return order


def upsert_order_items(order_id, items_data):
    """Insert or update items for an order."""
    for item_data in items_data:
        inventory_id = item_data.get("inventory_id")
        item_info = item_data.get("item", {})

        existing = OrderItem.query.filter_by(
            order_id=order_id, inventory_id=inventory_id
        ).first()

        if existing is None:
            existing = OrderItem(order_id=order_id, inventory_id=inventory_id)
            db.session.add(existing)

        existing.item_no = item_info.get("no", "")
        existing.item_name = item_info.get("name", "")
        existing.item_type = item_info.get("type", "PART")
        existing.category_id = item_info.get("category_id")
        existing.color_id = item_data.get("color_id")
        existing.color_name = item_data.get("color_name", "")
        existing.quantity = item_data.get("quantity", 0)
        existing.unit_price = float(item_data.get("unit_price", 0))
        existing.condition = item_data.get("new_or_used", "N")
        existing.remarks = item_data.get("remarks", "")
        existing.description = item_data.get("description", "")
        existing.raw_json = json.dumps(item_data)


def sync_orders(app, full=False):
    """Sync orders from BrickLink API.

    If full=True, re-fetches items for all orders.
    Otherwise only fetches items for orders not yet in the DB.
    """
    client = get_client(app)
    log = SyncLog(
        sync_type="full" if full else "incremental",
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(log)
    api_calls = 0

    try:
        # Fetch all orders (buyer = direction out)
        orders_data = client.get_orders(direction="out")
        api_calls += 1

        new_orders = 0
        for od in orders_data:
            order_id = od.get("order_id")
            existing = db.session.get(Order, order_id)
            is_new = existing is None

            upsert_order(od)

            # Fetch items for new orders or during full sync
            if is_new or full:
                try:
                    items = client.get_order_items(order_id)
                    api_calls += 1
                    upsert_order_items(order_id, items)
                    if is_new:
                        new_orders += 1
                except BrickLinkAPIError as e:
                    logger.warning(f"Failed to fetch items for order {order_id}: {e}")

        db.session.commit()

        log.orders_synced = new_orders if not full else len(orders_data)
        log.api_calls_used = api_calls
        log.completed_at = datetime.now(timezone.utc)
        log.status = "success"
        db.session.commit()

        return {
            "orders_found": len(orders_data),
            "new_orders": new_orders,
            "api_calls": api_calls,
        }

    except BrickLinkAPIError as e:
        log.status = "error"
        log.error_message = str(e)
        log.api_calls_used = api_calls
        log.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        raise
    except Exception as e:
        log.status = "error"
        log.error_message = str(e)
        log.api_calls_used = api_calls
        log.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        raise
