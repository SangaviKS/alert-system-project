import json
import logging
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

import azure.functions as func
from core.order_event import validate_event, is_critical_event, should_retry

def main(msg: func.ServiceBusMessage):
    """Process incoming order events from Service Bus queue."""
    try:
        body = msg.get_body().decode("utf-8")
        event = json.loads(body)
        logging.info(f"Processing order: {event['orderId']}")

        is_valid, validation_message = validate_event(event)
        if not is_valid:
            logging.error(f"Invalid event: {validation_message}")
            raise ValueError(f"Validation failed: {validation_message}")

        if is_critical_event(event):
            logging.warning(
                f"CRITICAL EVENT — Order {event['orderId'][:8]}... "
                f"Status: {event['status']} | "
                f"Customer: {event['customerId']} | "
                f"Amount: ${event['amount']}"
            )
        else:
            logging.info(
                f"Standard event processed — Order {event['orderId'][:8]}... "
                f"Status: {event['status']}"
            )

        if not should_retry(event):
            raise Exception("Max retries exceeded — dead lettering message")

        logging.info(f"Order {event['orderId'][:8]}... processed successfully.")

    except Exception as e:
        logging.error(f"Failed to process message: {e}")
        raise