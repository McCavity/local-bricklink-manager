from flask import Blueprint, render_template
from sqlalchemy import func
from app.database import db
from app.models import Order

stats_bp = Blueprint("stats", __name__, url_prefix="/stats")


@stats_bp.route("/")
def dashboard():
    total_orders = db.session.query(func.count(Order.order_id)).scalar() or 0

    if total_orders == 0:
        return render_template("stats/dashboard.html", total_orders=0)

    # Compute EUR-normalized totals by iterating orders
    # (needed because SQLite can't do the conditional EUR conversion in SQL)
    orders = Order.query.all()

    total_spending = 0.0
    total_subtotal = 0.0
    total_shipping = 0.0
    total_items = 0
    total_lots = 0

    for o in orders:
        total_spending += o.grand_total_in_eur
        total_subtotal += o.subtotal_in_eur
        total_shipping += o.shipping_cost_in_eur
        total_items += o.total_count or 0
        total_lots += o.unique_count or 0

    avg_order_value = total_spending / total_orders if total_orders else 0.0
    avg_lot_price = total_subtotal / total_lots if total_lots else 0.0
    avg_piece_price = total_subtotal / total_items if total_items else 0.0

    # Seller breakdown (EUR-normalized)
    seller_map = {}
    for o in orders:
        name = o.seller_name or "Unknown"
        if name not in seller_map:
            seller_map[name] = {"count": 0, "total": 0.0}
        seller_map[name]["count"] += 1
        seller_map[name]["total"] += o.grand_total_in_eur

    seller_stats = [
        (name, data["count"], data["total"], data["total"] / data["count"])
        for name, data in seller_map.items()
    ]
    seller_stats.sort(key=lambda x: x[2], reverse=True)

    # Status breakdown
    status_stats = (
        db.session.query(
            Order.status,
            func.count(Order.order_id).label("count"),
        )
        .group_by(Order.status)
        .all()
    )

    # Foreign currency orders count
    foreign_count = sum(1 for o in orders if o.has_foreign_currency_info)

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
        foreign_count=foreign_count,
        currency="EUR",
    )
