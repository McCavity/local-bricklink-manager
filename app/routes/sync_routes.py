from flask import Blueprint, redirect, url_for, flash, current_app, jsonify
from app.bricklink.sync import sync_orders, get_client
from app.bricklink.client import BrickLinkAPIError

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")


@sync_bp.route("/full", methods=["POST"])
def full_sync():
    if not current_app.config.get("BRICKLINK_CONSUMER_KEY"):
        flash("BrickLink API credentials not configured. Check your .env file.", "error")
        return redirect(url_for("orders.order_list"))

    try:
        result = sync_orders(current_app._get_current_object(), full=True)
        parts = [
            f"Full sync complete: {result['orders_found']} orders found",
            f"{result['new_orders']} new",
        ]
        if result.get("purged"):
            parts.append(f"{result['purged']} purged (no item data available)")
        if result.get("items_fetched"):
            parts.append(f"items fetched for {result['items_fetched']} orders")
        parts.append(f"{result['api_calls']} API calls used")
        flash(", ".join(parts) + ".", "success")
    except BrickLinkAPIError as e:
        flash(f"Sync failed: {e}", "error")
    except Exception as e:
        flash(f"Sync failed: {e}", "error")

    return redirect(url_for("orders.order_list"))


@sync_bp.route("/incremental", methods=["POST"])
def incremental_sync():
    if not current_app.config.get("BRICKLINK_CONSUMER_KEY"):
        flash("BrickLink API credentials not configured. Check your .env file.", "error")
        return redirect(url_for("orders.order_list"))

    try:
        result = sync_orders(current_app._get_current_object(), full=False)
        parts = [
            f"Sync complete: {result['orders_found']} orders found",
            f"{result['new_orders']} new",
        ]
        if result.get("purged"):
            parts.append(f"{result['purged']} purged")
        parts.append(f"{result['api_calls']} API calls used")
        flash(", ".join(parts) + ".", "success")
    except BrickLinkAPIError as e:
        flash(f"Sync failed: {e}", "error")
    except Exception as e:
        flash(f"Sync failed: {e}", "error")

    return redirect(url_for("orders.order_list"))


@sync_bp.route("/debug")
def debug_api():
    """Diagnostic endpoint: tries both directions and shows raw API results."""
    if not current_app.config.get("BRICKLINK_CONSUMER_KEY"):
        return jsonify({"error": "API credentials not configured"})

    client = get_client(current_app)
    results = {}

    for direction in ("out", "in"):
        for filed in (False, True):
            key = f"direction={direction}, filed={filed}"
            try:
                orders = client.get_orders(direction=direction, filed=filed)

                # Status breakdown
                status_counts = {}
                for o in orders:
                    s = o.get("status", "unknown")
                    status_counts[s] = status_counts.get(s, 0) + 1

                # Date range
                dates = [o.get("date_ordered", "") for o in orders if o.get("date_ordered")]
                dates.sort()

                results[key] = {
                    "count": len(orders),
                    "status_breakdown": status_counts,
                    "date_range": {
                        "earliest": dates[0] if dates else None,
                        "latest": dates[-1] if dates else None,
                    },
                    "first_5": [
                        {
                            "order_id": o.get("order_id"),
                            "status": o.get("status"),
                            "date_ordered": o.get("date_ordered"),
                            "seller_name": o.get("seller_name"),
                        }
                        for o in orders[:5]
                    ],
                    "last_5": [
                        {
                            "order_id": o.get("order_id"),
                            "status": o.get("status"),
                            "date_ordered": o.get("date_ordered"),
                            "seller_name": o.get("seller_name"),
                        }
                        for o in orders[-5:]
                    ],
                }
            except BrickLinkAPIError as e:
                results[key] = {"error": str(e)}

    return jsonify(results)
