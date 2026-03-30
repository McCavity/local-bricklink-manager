import json
import logging
from datetime import datetime, timezone

from app.database import db
from app.models import Feedback
from app.bricklink.sync import get_client
from app.bricklink.client import BrickLinkAPIError

logger = logging.getLogger(__name__)

DEFAULT_FEEDBACK_TEXT = "Thank you for a smooth transaction! Everything was well packed and as described."


def submit_feedback(app, order_id, rating, comment=None):
    """Submit feedback for an order via the BrickLink API.

    rating: 'PRAISE', 'NEUTRAL', or 'COMPLAINT'
    """
    if comment is None:
        comment = DEFAULT_FEEDBACK_TEXT

    client = get_client(app)

    feedback = Feedback(
        order_id=order_id,
        rating=rating.upper(),
        comment=comment,
    )
    db.session.add(feedback)

    try:
        result = client.post_feedback(order_id, rating.upper(), comment)
        feedback.sent_at = datetime.now(timezone.utc)
        feedback.api_response = json.dumps(result) if result else ""
        db.session.commit()
        return True, "Feedback submitted successfully."
    except BrickLinkAPIError as e:
        feedback.api_response = str(e)
        db.session.commit()
        return False, str(e)
