from flask import Flask
from config import Config
from app.database import db, init_db


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    # Initialize database
    db.init_app(app)
    with app.app_context():
        init_db()

    # Register blueprints
    from app.routes.orders import orders_bp
    from app.routes.checklist import checklist_bp
    from app.routes.stats import stats_bp
    from app.routes.sync_routes import sync_bp

    app.register_blueprint(orders_bp)
    app.register_blueprint(checklist_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(sync_bp)

    # Root redirect
    @app.route("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("orders.order_list"))

    return app
