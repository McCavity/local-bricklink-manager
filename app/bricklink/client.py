import json
import logging
from requests_oauthlib import OAuth1Session

logger = logging.getLogger(__name__)

BASE_URL = "https://api.bricklink.com/api/store/v1"


class BrickLinkAPIError(Exception):
    def __init__(self, status_code, message, meta=None):
        self.status_code = status_code
        self.message = message
        self.meta = meta or {}
        super().__init__(f"BrickLink API error {status_code}: {message}")


class BrickLinkClient:
    def __init__(self, consumer_key, consumer_secret, token, token_secret):
        self.session = OAuth1Session(
            consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=token_secret,
        )

    def _request(self, method, path, params=None, json_body=None):
        url = f"{BASE_URL}{path}"
        logger.info(f"API {method} {url} params={params}")
        resp = self.session.request(
            method, url, params=params, json=json_body,
            headers={"Accept": "application/json"},
        )
        logger.info(f"API response: HTTP {resp.status_code}, body length={len(resp.text)}")
        logger.debug(f"API response body: {resp.text[:500]}")

        if resp.status_code != 200:
            try:
                body = resp.json()
                msg = body.get("meta", {}).get("description", resp.text)
            except Exception:
                msg = resp.text
            raise BrickLinkAPIError(resp.status_code, msg)

        body = resp.json()
        meta = body.get("meta", {})
        if meta.get("code") not in (200, 204):
            raise BrickLinkAPIError(
                meta.get("code", 0),
                meta.get("description", "Unknown error"),
                meta,
            )
        data = body.get("data")
        if isinstance(data, list):
            logger.info(f"API returned {len(data)} items")
        return data

    def get_orders(self, direction="out", status=None, filed=False):
        """Get list of orders. direction='out' = orders the user placed (buyer)."""
        params = {"direction": direction}
        if status:
            params["status"] = status
        if filed:
            params["filed"] = "true"
        return self._request("GET", "/orders", params=params) or []

    def get_order(self, order_id):
        """Get details for a single order."""
        return self._request("GET", f"/orders/{order_id}")

    def get_order_items(self, order_id):
        """Get items in an order. Returns list of batch lists."""
        data = self._request("GET", f"/orders/{order_id}/items")
        # API returns list of lists (batches); flatten
        items = []
        if data:
            for batch in data:
                if isinstance(batch, list):
                    items.extend(batch)
                else:
                    items.append(batch)
        return items

    def update_order_status(self, order_id, status):
        """Update the BrickLink status of an order."""
        return self._request("PUT", f"/orders/{order_id}/status", json_body={
            "field": "status",
            "value": status,
        })

    def post_feedback(self, order_id, rating, comment=""):
        """Post feedback for an order. rating: PRAISE, NEUTRAL, COMPLAINT."""
        return self._request("POST", "/feedback", json_body={
            "order_id": order_id,
            "rating_of_bs": rating,  # rating of buyer/seller
            "comment": comment,
        })

    def get_order_messages(self, order_id):
        """Get messages/drive thru for an order."""
        return self._request("GET", f"/orders/{order_id}/messages") or []

    def get_order_feedback(self, order_id):
        """Get feedback for an order."""
        return self._request("GET", f"/orders/{order_id}/feedback") or []
