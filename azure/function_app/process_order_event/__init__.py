import json
import logging
import os
import sys
import ssl
import certifi

sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

import azure.functions as func
import sendgrid
from sendgrid.helpers.mail import Mail
from core.order_event import validate_event, is_critical_event, should_retry

def send_critical_alert(event: dict):
    """Send email alert for critical order events via SendGrid."""
    try:
        # Set SSL cert path at environment level before SendGrid call
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

        sg = sendgrid.SendGridAPIClient(
            api_key=os.getenv("SENDGRID_API_KEY")
        )

        message = Mail(
            from_email=os.getenv("ALERT_EMAIL_FROM"),
            to_emails=os.getenv("ALERT_EMAIL_TO"),
            subject=f"🚨 Critical Order Alert — {event['status'].upper()}",
            html_content=f"""
                <h2>Critical Order Event Detected</h2>
                <table>
                    <tr><td><strong>Order ID:</strong></td><td>{event['orderId']}</td></tr>
                    <tr><td><strong>Customer:</strong></td><td>{event['customerId']}</td></tr>
                    <tr><td><strong>Status:</strong></td><td>{event['status'].upper()}</td></tr>
                    <tr><td><strong>Amount:</strong></td><td>${event['amount']} {event['currency']}</td></tr>
                    <tr><td><strong>Time:</strong></td><td>{event['timestamp']}</td></tr>
                    <tr><td><strong>Retry Count:</strong></td><td>{event['retryCount']}</td></tr>
                </table>
                <p>Please review this order immediately.</p>
            """
        )
        sg.send(message)
        logging.info(
            f"Critical alert email sent for order {event['orderId'][:8]}..."
        )
    except Exception as e:
        logging.error(f"Failed to send alert email: {e}")
        raise
    
def main(msg: func.ServiceBusMessage):
    """Process incoming order events from Service Bus queue."""
    try:
        body = msg.get_body().decode("utf-8")
        event: dict = json.loads(body)
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
            send_critical_alert(event)
        else:
            logging.info(
                f"Standard event processed — "
                f"Order {event['orderId'][:8]}... "
                f"Status: {event['status']}"
            )

        if not should_retry(event):
            raise Exception(
                "Max retries exceeded — dead lettering message"
            )

        logging.info(
            f"Order {event['orderId'][:8]}... processed successfully."
        )

    except Exception as e:
        logging.error(f"Failed to process message: {e}")
        raise