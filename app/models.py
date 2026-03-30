from datetime import datetime, timezone
from app.database import db


class Order(db.Model):
    __tablename__ = "orders"

    order_id = db.Column(db.Integer, primary_key=True)  # BrickLink order ID
    buyer_name = db.Column(db.String, nullable=False, default="")
    seller_name = db.Column(db.String, nullable=False, default="")
    store_name = db.Column(db.String, default="")
    order_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String, nullable=False, default="")  # BrickLink status
    local_status = db.Column(db.String, nullable=True)  # NULL / received / checked
    total_count = db.Column(db.Integer, default=0)
    unique_count = db.Column(db.Integer, default=0)
    subtotal = db.Column(db.Float, default=0.0)
    grand_total = db.Column(db.Float, default=0.0)
    shipping_cost = db.Column(db.Float, default=0.0)
    currency_code = db.Column(db.String, default="EUR")
    payment_method = db.Column(db.String, default="")
    buyer_order_count = db.Column(db.Integer, default=0)
    remarks = db.Column(db.Text, default="")
    raw_json = db.Column(db.Text, default="")
    synced_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship("OrderItem", backref="order", lazy="dynamic")
    checklist_entries = db.relationship("ChecklistEntry", backref="order", lazy="dynamic")
    feedback_entries = db.relationship("Feedback", backref="order", lazy="dynamic")

    @property
    def avg_lot_price(self):
        if self.unique_count:
            return self.subtotal / self.unique_count
        return 0.0

    @property
    def avg_piece_price(self):
        if self.total_count:
            return self.subtotal / self.total_count
        return 0.0


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    inventory_id = db.Column(db.Integer, nullable=True)
    item_no = db.Column(db.String, nullable=False)
    item_name = db.Column(db.String, default="")
    item_type = db.Column(db.String, default="")  # PART, SET, MINIFIG, etc.
    category_id = db.Column(db.Integer, nullable=True)
    category_name = db.Column(db.String, default="")
    color_id = db.Column(db.Integer, nullable=True)
    color_name = db.Column(db.String, default="")
    quantity = db.Column(db.Integer, nullable=False, default=0)
    unit_price = db.Column(db.Float, nullable=False, default=0.0)
    condition = db.Column(db.String, default="N")  # N=new, U=used
    remarks = db.Column(db.Text, default="")
    description = db.Column(db.Text, default="")
    raw_json = db.Column(db.Text, default="")

    __table_args__ = (
        db.UniqueConstraint("order_id", "inventory_id", name="uq_order_inventory"),
    )

    @property
    def image_url(self):
        type_map = {
            "PART": "PN",
            "SET": "SN",
            "MINIFIG": "MN",
            "GEAR": "GN",
            "BOOK": "BN",
        }
        code = type_map.get(self.item_type, "PN")
        color = self.color_id if self.color_id else 0
        return f"https://img.bricklink.com/ItemImage/{code}/{color}/{self.item_no}.png"

    @property
    def total_price(self):
        return self.quantity * self.unit_price


class ChecklistEntry(db.Model):
    __tablename__ = "checklist_entries"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    order_item_id = db.Column(db.Integer, db.ForeignKey("order_items.id"), nullable=False)
    expected_qty = db.Column(db.Integer, nullable=False)
    received_qty = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String, default="pending")  # pending, ok, mismatch, missing
    notes = db.Column(db.Text, default="")
    checked_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    item = db.relationship("OrderItem", backref="checklist_entry")


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.order_id"), nullable=False)
    rating = db.Column(db.String, nullable=False)  # PRAISE, NEUTRAL, COMPLAINT
    comment = db.Column(db.Text, default="")
    sent_at = db.Column(db.DateTime, nullable=True)
    api_response = db.Column(db.Text, default="")


class SyncLog(db.Model):
    __tablename__ = "sync_log"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sync_type = db.Column(db.String, nullable=False)  # full, incremental, order_detail
    orders_synced = db.Column(db.Integer, default=0)
    api_calls_used = db.Column(db.Integer, default=0)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String, default="")  # success, error, rate_limited
    error_message = db.Column(db.Text, default="")
