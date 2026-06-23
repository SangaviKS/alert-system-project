import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.order_event import (
    generate_order_event,
    is_critical_event,
    validate_event,
    should_retry,
    increment_retry,
    ORDER_STATUSES
)

# --- generate_order_event tests ---

def test_generate_order_event_returns_dict():
    event = generate_order_event()
    assert isinstance(event, dict)

def test_generate_order_event_has_required_fields():
    event = generate_order_event()
    expected = {"orderId", "customerId", "status", "amount",
                "currency", "timestamp", "retryCount"}
    assert expected.issubset(event.keys())

def test_generate_order_event_default_currency():
    event = generate_order_event()
    assert event["currency"] == "CAD"

def test_generate_order_event_retry_count_starts_at_zero():
    event = generate_order_event()
    assert event["retryCount"] == 0

def test_generate_order_event_custom_status():
    event = generate_order_event(status="placed")
    assert event["status"] == "placed"

def test_generate_order_event_custom_customer_id():
    event = generate_order_event(customer_id="CUST-TEST-001")
    assert event["customerId"] == "CUST-TEST-001"

def test_generate_order_event_amount_in_range():
    event = generate_order_event()
    assert 10.0 <= event["amount"] <= 500.0

def test_generate_order_event_status_is_valid():
    event = generate_order_event()
    assert event["status"] in ORDER_STATUSES

# --- is_critical_event tests ---

def test_is_critical_event_failed_order():
    event = generate_order_event(status="failed")
    assert is_critical_event(event) == True

def test_is_critical_event_cancelled_order():
    event = generate_order_event(status="cancelled")
    assert is_critical_event(event) == True

def test_is_critical_event_placed_order():
    event = generate_order_event(status="placed")
    assert is_critical_event(event) == False

def test_is_critical_event_processing_order():
    event = generate_order_event(status="processing")
    assert is_critical_event(event) == False

# --- validate_event tests ---

def test_validate_event_accepts_valid_event():
    event = generate_order_event()
    is_valid, message = validate_event(event)
    assert is_valid == True

def test_validate_event_rejects_missing_field():
    event = {"orderId": "123", "status": "placed"}
    is_valid, message = validate_event(event)
    assert is_valid == False
    assert "Missing field" in message

def test_validate_event_rejects_invalid_status():
    event = generate_order_event()
    event["status"] = "unknown"
    is_valid, message = validate_event(event)
    assert is_valid == False
    assert "Invalid status" in message

def test_validate_event_rejects_zero_amount():
    event = generate_order_event()
    event["amount"] = 0
    is_valid, message = validate_event(event)
    assert is_valid == False
    assert "Amount" in message

def test_validate_event_rejects_wrong_type():
    event = generate_order_event()
    event["amount"] = "not-a-number"
    is_valid, message = validate_event(event)
    assert is_valid == False

# --- should_retry tests ---

def test_should_retry_below_max():
    event = generate_order_event()
    event["retryCount"] = 1
    assert should_retry(event) == True

def test_should_retry_at_max():
    event = generate_order_event()
    event["retryCount"] = 3
    assert should_retry(event) == False

def test_should_retry_custom_max():
    event = generate_order_event()
    event["retryCount"] = 2
    assert should_retry(event, max_retries=5) == True

# --- increment_retry tests ---

def test_increment_retry_increases_count():
    event = generate_order_event()
    updated = increment_retry(event)
    assert updated["retryCount"] == 1

def test_increment_retry_does_not_mutate_original():
    event = generate_order_event()
    updated = increment_retry(event)
    assert event["retryCount"] == 0
    assert updated["retryCount"] == 1

# --- additional validate_event tests ---

def test_validate_event_rejects_negative_amount():
    event = generate_order_event()
    event["amount"] = -50.0
    is_valid, message = validate_event(event)
    assert is_valid == False
    assert "Amount" in message

# --- additional increment_retry test ---

def test_increment_retry_multiple_times():
    event = generate_order_event()
    event = increment_retry(event)
    event = increment_retry(event)
    assert event["retryCount"] == 2