# This function is deployed and executed in AWS Lambda.
# It is triggered by SQS queue: order-events
# This file is kept here for reference and version control purposes.

import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ORDER_STATUSES = ["placed", "failed", "cancelled", "processing"]

def validate_event(event):
    """Validates that an order event has all required fields."""
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

def is_critical_event(event):
    """Returns True if the event requires immediate alerting."""
    return event["status"] in ["failed", "cancelled"]

def should_retry(event, max_retries=3):
    """Returns True if the event should be retried."""
    return event["retryCount"] < max_retries

def lambda_handler(event, context):
    """Process incoming order events from SQS queue."""
    processed = 0
    failed = 0
    batch_item_failures = []

    for record in event["Records"]:
        message_id = record["messageId"]
        try:
            body = json.loads(record["body"])
            logger.info(f"Processing order: {body['orderId']}")

            is_valid, validation_message = validate_event(body)
            if not is_valid:
                logger.error(f"Invalid event: {validation_message}")
                raise ValueError(f"Validation failed: {validation_message}")

            if is_critical_event(body):
                logger.warning(
                    f"CRITICAL EVENT — Order {body['orderId'][:8]}... "
                    f"Status: {body['status']} | "
                    f"Customer: {body['customerId']} | "
                    f"Amount: ${body['amount']}"
                )
            else:
                logger.info(
                    f"Standard event — Order {body['orderId'][:8]}... "
                    f"Status: {body['status']}"
                )

            if not should_retry(body):
                raise Exception(
                    f"Order {body['orderId'][:8]}... exceeded max retries"
                )

            logger.info(
                f"Order {body['orderId'][:8]}... processed successfully."
            )
            processed += 1

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}")
            batch_item_failures.append(
                {"itemIdentifier": message_id}
            )
            failed += 1

    logger.info(f"Batch complete — Processed: {processed}, Failed: {failed}")

    if batch_item_failures:
        return {"batchItemFailures": batch_item_failures}

    return {"statusCode": 200, "body": f"Processed {processed} records"}