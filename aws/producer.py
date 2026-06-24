import json
import os
import sys
import time
import boto3
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
from core.order_event import generate_order_event, is_critical_event

load_dotenv()

QUEUE_URL = os.getenv("AWS_SQS_QUEUE_URL")

def send_order_event(sqs_client, event):
    """Send a single order event to the SQS queue."""
    response = sqs_client.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(event),
        MessageAttributes={
            "status": {
                "StringValue": event["status"],
                "DataType": "String"
            }
        }
    )
    priority = "🚨 CRITICAL" if is_critical_event(event) else "✅ normal"
    print(
        f"Sent [{priority}] Order {event['orderId'][:8]}... "
        f"Status: {event['status']} | "
        f"Amount: ${event['amount']} | "
        f"MessageId: {response['MessageId'][:8]}..."
    )
    return response

def main():
    print("Starting AWS Order Event Producer...")
    print(f"Sending to SQS queue: {QUEUE_URL}\n")

    sqs = boto3.client(
        "sqs",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    )

    try:
        while True:
            event = generate_order_event()
            send_order_event(sqs, event)
            time.sleep(10)
    except KeyboardInterrupt:
        print("\nProducer stopped.")

if __name__ == "__main__":
    main()