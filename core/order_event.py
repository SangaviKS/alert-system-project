import uuid
import random
from datetime import datetime, timezone

ORDER_STATUSES = ["placed", "failed", "cancelled", "processing"]

def generate_order_event(status=None, customer_id=None):
    """Generate a realistic order event."""
    return {
        "orderId": str(uuid.uuid4()),
        "customerId": customer_id or f"CUST-{random.randint(1000, 9999)}",
        "status": status or random.choice(ORDER_STATUSES),
        "amount": round(random.uniform(10.0, 500.0), 2),
        "currency": "CAD",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "retryCount": 0
    }

def is_critical_event(event):
    """Returns True if the event requires immediate alerting."""
    return event["status"] in ["failed", "cancelled"]

def validate_event(event):
    """Validates that an order event has all required fields with correct types."""
    required_fields = {
        "orderId": str,
        "customerId": str,
        "status": str,
        "amount": (int, float),
        "currency": str,
        "timestamp": str,
        "retryCount": int
    }
    for field, expected_type in required_fields.items():
        if field not in event:
            return False, f"Missing field: {field}"
        if not isinstance(event[field], expected_type):
            return False, f"Invalid type for {field}"
    if event["status"] not in ORDER_STATUSES:
        return False, f"Invalid status: {event['status']}"
    if event["amount"] <= 0:
        return False, "Amount must be greater than 0"
    return True, "Valid"

def should_retry(event, max_retries=3):
    """Returns True if the event should be retried."""
    return event["retryCount"] < max_retries

def increment_retry(event):
    """Returns a new event dict with incremented retry count."""
    updated = event.copy()
    updated["retryCount"] += 1
    return updated