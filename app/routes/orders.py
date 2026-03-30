from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from app.database import db
from app.models import Order, OrderItem
from app.bricklink.sync import get_client
from app.bricklink.client import BrickLinkAPIError

orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("/")
def order_list():
    status_filter = request.args.get("status", "")
    local_filter = request.args.get("local_status", "")
    sort = request.args.get("sort", "date_desc")

    query = Order.query

    if status_filter:
        query = query.filter(Order.status == status_filter)
    if local_filter:
        if local_filter == "none":
            query = query.filter(Order.local_status.is_(None))
        else:
            query = query.filter(Order.local_status == local_filter)

    if sort == "date_asc":
        query = query.order_by(Order.order_date.asc())
    elif sort == "total_desc":
        query = query.order_by(Order.grand_total.desc())
    elif sort == "total_asc":
        query = query.order_by(Order.grand_total.asc())
    else:
        query = query.order_by(Order.order_date.desc())

    orders = query.all()

    # Get distinct statuses for filter dropdown
    statuses = db.session.query(Order.status).distinct().all()
    statuses = sorted(set(s[0] for s in statuses if s[0]))

    return render_template(
        "orders/list.html",
        orders=orders,
        statuses=statuses,
        current_status=status_filter,
        current_local=local_filter,
        current_sort=sort,
    )


@orders_bp.route("/<int:order_id>")
def order_detail(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash(f"Order {order_id} not found.", "error")
        return redirect(url_for("orders.order_list"))

    items = OrderItem.query.filter_by(order_id=order_id).all()
    return render_template("orders/detail.html", order=order, items=items)


@orders_bp.route("/batch-received", methods=["POST"])
def batch_mark_received():
    order_ids = request.form.getlist("order_ids")
    if not order_ids:
        flash("No orders selected.", "warning")
        return redirect(url_for("orders.order_list"))

    count = 0
    for oid in order_ids:
        order = db.session.get(Order, int(oid))
        if order and order.local_status is None:
            order.local_status = "received"
            count += 1

    db.session.commit()
    flash(f"Marked {count} order(s) as received.", "success")
    return redirect(url_for("orders.order_list"))


@orders_bp.route("/<int:order_id>/complete", methods=["POST"])
def mark_completed(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash(f"Order {order_id} not found.", "error")
        return redirect(url_for("orders.order_list"))

    try:
        client = get_client(current_app)
        client.update_order_status(order_id, "Completed")
        order.status = "COMPLETED"
        db.session.commit()
        flash(f"Order {order_id} marked as Completed on BrickLink.", "success")
    except BrickLinkAPIError as e:
        flash(f"Failed to update order on BrickLink: {e}", "error")

    return redirect(url_for("orders.order_detail", order_id=order_id))


@orders_bp.route("/<int:order_id>/feedback", methods=["POST"])
def submit_feedback(order_id):
    from app.bricklink.feedback import submit_feedback as _submit

    rating = request.form.get("rating", "PRAISE")
    comment = request.form.get("comment", "")

    success, message = _submit(current_app, order_id, rating, comment or None)
    if success:
        flash(message, "success")
    else:
        flash(message, "error")

    return redirect(url_for("orders.order_detail", order_id=order_id))
