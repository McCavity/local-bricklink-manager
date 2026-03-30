from flask import Blueprint, redirect, url_for, flash, current_app
from app.bricklink.sync import sync_orders
from app.bricklink.client import BrickLinkAPIError

sync_bp = Blueprint("sync", __name__, url_prefix="/sync")


@sync_bp.route("/full", methods=["POST"])
def full_sync():
    if not current_app.config.get("BRICKLINK_CONSUMER_KEY"):
        flash("BrickLink API credentials not configured. Check your .env file.", "error")
        return redirect(url_for("orders.order_list"))

    try:
        result = sync_orders(current_app._get_current_object(), full=True)
        flash(
            f"Full sync complete: {result['orders_found']} orders found, "
            f"{result['new_orders']} new, {result['api_calls']} API calls used.",
            "success",
        )
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
        flash(
            f"Sync complete: {result['orders_found']} orders found, "
            f"{result['new_orders']} new, {result['api_calls']} API calls used.",
            "success",
        )
    except BrickLinkAPIError as e:
        flash(f"Sync failed: {e}", "error")
    except Exception as e:
        flash(f"Sync failed: {e}", "error")

    return redirect(url_for("orders.order_list"))
