import json
import logging
from datetime import datetime, timezone

from app.database import db
from app.models import Order, OrderItem, SyncLog
from app.bricklink.client import BrickLinkClient, BrickLinkAPIError
from app.bricklink.currency import convert_to_eur

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
    """Insert or update an order from API data.

    BrickLink returns two cost blocks:
    - cost: amounts in the store's currency (e.g. CZK for a Czech shop)
    - disp_cost: amounts in the buyer's display currency (e.g. EUR)
    We use disp_cost as the primary values since we're a buyer.
    When the store currency differs, we store the originals in the _eur fields
    (which in this case become the "buyer currency" values — always EUR for us).
    """
    order_id = order_data.get("order_id")
    order = db.session.get(Order, order_id)
    is_new = order is None

    cost = order_data.get("cost", {})
    disp_cost = order_data.get("disp_cost", {})

    store_currency = cost.get("currency_code", "EUR") if cost else "EUR"
    buyer_currency = disp_cost.get("currency_code", "EUR") if disp_cost else "EUR"

    if store_currency != buyer_currency and disp_cost:
        # Foreign currency order: store values are in store currency,
        # disp values are in buyer currency (EUR).
        # Primary fields get the buyer (EUR) values for consistent display/stats.
        subtotal = _extract_cost(disp_cost, "subtotal")
        grand_total = _extract_cost(disp_cost, "grand_total")
        shipping_cost = _extract_cost(disp_cost, "shipping")
        currency_code = buyer_currency

        # Store original shop currency values in the _eur fields
        # (repurposed: these hold the "other" currency for reference)
        orig_subtotal = _extract_cost(cost, "subtotal")
        orig_grand_total = _extract_cost(cost, "grand_total")
        orig_shipping = _extract_cost(cost, "shipping")
    else:
        # Same currency: use cost block directly
        subtotal = _extract_cost(cost, "subtotal")
        grand_total = _extract_cost(cost, "grand_total")
        shipping_cost = _extract_cost(cost, "shipping")
        currency_code = store_currency
        orig_subtotal = None
        orig_grand_total = None
        orig_shipping = None

    if is_new:
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
    order.currency_code = currency_code
    order.payment_method = order_data.get("payment", {}).get("method", "") if order_data.get("payment") else ""
    order.remarks = order_data.get("remarks", "")
    order.raw_json = json.dumps(order_data)
    order.synced_at = datetime.now(timezone.utc)

    # For foreign currency orders, store originals and exchange rate
    if store_currency != buyer_currency and orig_grand_total:
        order.subtotal_eur = orig_subtotal       # original store currency subtotal
        order.grand_total_eur = orig_grand_total  # original store currency total
        order.shipping_cost_eur = orig_shipping   # original store currency shipping
        # Compute exchange rate: 1 buyer_currency = X store_currency
        if grand_total and grand_total > 0:
            order.exchange_rate = orig_grand_total / grand_total
            logger.info(
                f"Order {order_id}: foreign currency {store_currency}, "
                f"display {buyer_currency}: {orig_grand_total} {store_currency} "
                f"= {grand_total} {buyer_currency}"
            )

    # Auto-mark COMPLETED/PURGED/CANCELLED as "checked" locally on first import
    if is_new and order.status in ("COMPLETED", "PURGED", "CANCELLED"):
        order.local_status = "checked"

    # For PURGED orders, assume feedback was already given
    if is_new and order.status == "PURGED":
        order.has_buyer_feedback = True

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

    If full=True, fetches orders in ALL statuses (including Completed)
    and re-fetches items for all orders.
    Otherwise only fetches active (non-completed) orders and items for
    orders not yet in the DB.
    """
    client = get_client(app)
    log = SyncLog(
        sync_type="full" if full else "incremental",
        started_at=datetime.now(timezone.utc),
    )
    db.session.add(log)
    api_calls = 0

    try:
        orders_data = []

        if full:
            # Full sync: fetch both non-filed and filed orders.
            # Non-filed = active orders; filed = completed/archived orders.
            # The API excludes filed orders by default.
            for filed in (False, True):
                try:
                    batch = client.get_orders(direction="out", filed=filed)
                    api_calls += 1
                    orders_data.extend(batch)
                except BrickLinkAPIError as e:
                    api_calls += 1
                    logger.warning(f"Failed to fetch orders (filed={filed}): {e}")
        else:
            # Incremental: fetch active (non-filed) orders + filed orders
            # to catch newly completed/purged ones too.
            for filed in (False, True):
                try:
                    batch = client.get_orders(direction="out", filed=filed)
                    api_calls += 1
                    orders_data.extend(batch)
                except BrickLinkAPIError as e:
                    api_calls += 1
                    logger.warning(f"Failed to fetch orders (filed={filed}): {e}")

        # Deduplicate in case an order appears in both filed and non-filed
        seen_ids = set()
        unique_orders = []
        for od in orders_data:
            oid = od.get("order_id")
            if oid not in seen_ids:
                seen_ids.add(oid)
                unique_orders.append(od)
        orders_data = unique_orders

        new_orders = 0
        items_fetched = 0
        items_failed = 0
        for od in orders_data:
            order_id = od.get("order_id")
            order_status = od.get("status", "")
            existing = db.session.get(Order, order_id)
            is_new = existing is None

            order = upsert_order(od)

            # Fetch items for new orders or during full sync.
            # Skip PURGED orders — BrickLink no longer has their item data.
            if (is_new or full) and order_status != "PURGED":
                try:
                    items = client.get_order_items(order_id)
                    api_calls += 1
                    upsert_order_items(order_id, items)
                    items_fetched += 1
                except BrickLinkAPIError as e:
                    api_calls += 1
                    items_failed += 1
                    logger.warning(f"Failed to fetch items for order {order_id} ({order_status}): {e}")

            # Check feedback status for non-purged orders on first import
            if is_new and order_status != "PURGED":
                try:
                    feedback_list = client.get_order_feedback(order_id)
                    api_calls += 1
                    # Check if the buyer (us) already left feedback
                    for fb in feedback_list:
                        if fb.get("from", {}).get("name", "").lower() == order.buyer_name.lower():
                            order.has_buyer_feedback = True
                            break
                except BrickLinkAPIError:
                    api_calls += 1
                    # Non-critical, just skip

            if is_new:
                new_orders += 1

        db.session.commit()

        log.orders_synced = new_orders if not full else len(orders_data)
        log.api_calls_used = api_calls
        log.completed_at = datetime.now(timezone.utc)
        log.status = "success"
        db.session.commit()

        purged_count = sum(1 for o in orders_data if o.get("status") == "PURGED")
        return {
            "orders_found": len(orders_data),
            "new_orders": new_orders,
            "purged": purged_count,
            "items_fetched": items_fetched,
            "items_failed": items_failed,
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
