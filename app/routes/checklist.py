from datetime import datetime, timezone
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.database import db
from app.models import Order, OrderItem, ChecklistEntry

checklist_bp = Blueprint("checklist", __name__, url_prefix="/checklist")


def _ensure_checklist(order_id):
    """Create checklist entries for all items if they don't exist yet."""
    items = OrderItem.query.filter_by(order_id=order_id).all()
    existing_item_ids = {
        e.order_item_id
        for e in ChecklistEntry.query.filter_by(order_id=order_id).all()
    }

    for item in items:
        if item.id not in existing_item_ids:
            entry = ChecklistEntry(
                order_id=order_id,
                order_item_id=item.id,
                expected_qty=item.quantity,
                received_qty=0,
                status="pending",
            )
            db.session.add(entry)

    db.session.commit()


@checklist_bp.route("/<int:order_id>")
def check_order(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash(f"Order {order_id} not found.", "error")
        return redirect(url_for("orders.order_list"))

    _ensure_checklist(order_id)

    entries = (
        db.session.query(ChecklistEntry, OrderItem)
        .join(OrderItem, ChecklistEntry.order_item_id == OrderItem.id)
        .filter(ChecklistEntry.order_id == order_id)
        .all()
    )

    total = len(entries)
    checked = sum(1 for e, _ in entries if e.status != "pending")
    progress = int(checked / total * 100) if total else 0

    return render_template(
        "checklist/check.html",
        order=order,
        entries=entries,
        progress=progress,
        total=total,
        checked=checked,
    )


@checklist_bp.route("/<int:order_id>/item/<int:entry_id>", methods=["POST"])
def update_item(order_id, entry_id):
    """AJAX endpoint to update a checklist entry."""
    entry = db.session.get(ChecklistEntry, entry_id)
    if not entry or entry.order_id != order_id:
        return jsonify({"error": "Entry not found"}), 404

    data = request.get_json() if request.is_json else request.form

    received_qty = int(data.get("received_qty", 0))
    notes = data.get("notes", "")

    entry.received_qty = received_qty
    entry.notes = notes
    entry.checked_at = datetime.now(timezone.utc)

    if received_qty == entry.expected_qty:
        entry.status = "ok"
    elif received_qty == 0:
        entry.status = "missing"
    else:
        entry.status = "mismatch"

    db.session.commit()

    return jsonify({
        "status": entry.status,
        "received_qty": entry.received_qty,
        "expected_qty": entry.expected_qty,
    })


@checklist_bp.route("/<int:order_id>/mark-all-ok", methods=["POST"])
def mark_all_ok(order_id):
    """Mark all pending items as OK (received_qty = expected_qty)."""
    entries = ChecklistEntry.query.filter_by(
        order_id=order_id, status="pending"
    ).all()

    now = datetime.now(timezone.utc)
    for entry in entries:
        entry.received_qty = entry.expected_qty
        entry.status = "ok"
        entry.checked_at = now

    db.session.commit()
    flash(f"Marked {len(entries)} item(s) as OK.", "success")
    return redirect(url_for("checklist.check_order", order_id=order_id))


@checklist_bp.route("/<int:order_id>/complete", methods=["POST"])
def complete_checklist(order_id):
    """Finalize the checklist and update local_status."""
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("orders.order_list"))

    order.local_status = "checked"
    db.session.commit()

    return redirect(url_for("checklist.summary", order_id=order_id))


@checklist_bp.route("/<int:order_id>/summary")
def summary(order_id):
    order = db.session.get(Order, order_id)
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for("orders.order_list"))

    entries = (
        db.session.query(ChecklistEntry, OrderItem)
        .join(OrderItem, ChecklistEntry.order_item_id == OrderItem.id)
        .filter(ChecklistEntry.order_id == order_id)
        .all()
    )

    ok_items = [(e, i) for e, i in entries if e.status == "ok"]
    mismatch_items = [(e, i) for e, i in entries if e.status == "mismatch"]
    missing_items = [(e, i) for e, i in entries if e.status == "missing"]
    pending_items = [(e, i) for e, i in entries if e.status == "pending"]

    return render_template(
        "checklist/summary.html",
        order=order,
        ok_items=ok_items,
        mismatch_items=mismatch_items,
        missing_items=missing_items,
        pending_items=pending_items,
    )
