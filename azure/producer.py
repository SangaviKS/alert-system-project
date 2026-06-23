import json
import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from azure.servicebus import ServiceBusClient, ServiceBusMessage
from core.order_event import generate_order_event, is_critical_event

load_dotenv()

CONNECTION_STRING = os.getenv("AZURE_SERVICE_BUS_CONNECTION_STRING")
QUEUE_NAME = os.getenv("AZURE_SERVICE_BUS_QUEUE_NAME")

def send_order_event(client, event):
    """Send a single order event to the Service Bus queue."""
    with client.get_queue_sender(queue_name=QUEUE_NAME) as sender:
        message = ServiceBusMessage(
            body=json.dumps(event),
            content_type="application/json",
            subject=f"order-{event['status']}"
        )
        sender.send_messages(message)
        priority = "🚨 CRITICAL" if is_critical_event(event) else "✅ normal"
        print(f"Sent [{priority}] Order {event['orderId'][:8]}... "
              f"Status: {event['status']} | Amount: ${event['amount']}")

def main():
    print("Starting Order Event Producer...")
    print(f"Sending to queue: {QUEUE_NAME}\n")

    with ServiceBusClient.from_connection_string(CONNECTION_STRING) as client:
        try:
            while True:
                event = generate_order_event()
                send_order_event(client, event)
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nProducer stopped.")

if __name__ == "__main__":
    main()