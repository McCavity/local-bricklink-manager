from flask import Blueprint, render_template
from sqlalchemy import func
from app.database import db
from app.models import Order

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.route("/")
def dashboard():
    # Overall stats
    total_orders = db.session.query(func.count(Order.order_id)).scalar() or 0
    total_spending = db.session.query(func.sum(Order.grand_total)).scalar() or 0.0
    total_subtotal = db.session.query(func.sum(Order.subtotal)).scalar() or 0.0
    total_shipping = db.session.query(func.sum(Order.shipping_cost)).scalar() or 0.0
    avg_order_value = db.session.query(func.avg(Order.grand_total)).scalar() or 0.0
    total_items = db.session.query(func.sum(Order.total_count)).scalar() or 0
    total_lots = db.session.query(func.sum(Order.unique_count)).scalar() or 0

    avg_lot_price = total_subtotal / total_lots if total_lots else 0.0
    avg_piece_price = total_subtotal / total_items if total_items else 0.0

    # Seller breakdown
    seller_stats = (
        db.session.query(
            Order.seller_name,
            func.count(Order.order_id).label("order_count"),
            func.sum(Order.grand_total).label("total_spent"),
            func.avg(Order.grand_total).label("avg_order"),
        )
        .group_by(Order.seller_name)
        .order_by(func.sum(Order.grand_total).desc())
        .all()
    )

    # Status breakdown
    status_stats = (
        db.session.query(
            Order.status,
            func.count(Order.order_id).label("count"),
        )
        .group_by(Order.status)
        .all()
    )

    # Currency (use most common)
    currency = (
        db.session.query(Order.currency_code)
        .group_by(Order.currency_code)
        .order_by(func.count(Order.order_id).desc())
        .first()
    )
    currency = currency[0] if currency else "EUR"

    return render_template(
        "stats/dashboard.html",
        total_orders=total_orders,
        total_spending=total_spending,
        total_subtotal=total_subtotal,
        total_shipping=total_shipping,
        avg_order_value=avg_order_value,
        total_items=total_items,
        total_lots=total_lots,
        avg_lot_price=avg_lot_price,
        avg_piece_price=avg_piece_price,
        seller_stats=seller_stats,
        status_stats=status_stats,
        currency=currency,
    )
