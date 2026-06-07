import json
import os
import uuid
from datetime import datetime

import boto3
from boto3.dynamodb.conditions import Key

TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)


def calendar_week(start_date):
    """'2026-05-12' -> '2026-W20' (ISO-Kalenderwoche)."""
    d = datetime.strptime(start_date, "%Y-%m-%d").date()
    year, week, _ = d.isocalendar()
    return f"{year}-W{week:02d}"


def claims(event):
    return event["requestContext"]["authorizer"]["jwt"]["claims"]


def is_admin(c):
    return "admin" in c.get("cognito:groups", "")


def reply(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization,Content-Type",
            "Access-Control-Allow-Methods": "GET,POST,DELETE,OPTIONS",
        },
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    method = event["requestContext"]["http"]["method"]
    path = event["requestContext"]["http"]["path"]

    if method == "OPTIONS":
        return reply(200, {})
    if method == "POST" and path == "/bookings":
        return create_booking(event)
    if method == "GET" and path == "/bookings":
        return list_bookings(event)
    if method == "DELETE" and path.startswith("/bookings/"):
        return delete_booking(event, path.rsplit("/", 1)[-1])

    # 404: genau diesen Text aendert ihr in Aufgabe 10.
    return reply(404, {"message": "Route nicht gefunden"})


def create_booking(event):
    c = claims(event)
    data = json.loads(event.get("body") or "{}")
    item = {
        "calendarWeek": calendar_week(data["startDate"]),
        "bookingId": str(uuid.uuid4()),
        "startDate": data["startDate"],
        "startSlot": data["startSlot"],
        "endDate": data["endDate"],
        "endSlot": data["endSlot"],
        "deviceIds": data["deviceIds"],
        "desc": data.get("desc", ""),
        "ownerSub": c["sub"],
        "ownerEmail": c.get("email", ""),
    }
    table.put_item(Item=item)
    return reply(201, item)


def list_bookings(event):
    params = event.get("queryStringParameters") or {}
    week = params.get("week")
    if not week:
        return reply(400, {"message": "Query-Parameter week fehlt"})
    result = table.query(KeyConditionExpression=Key("calendarWeek").eq(week))
    return reply(200, result.get("Items", []))


def delete_booking(event, booking_id):
    c = claims(event)
    params = event.get("queryStringParameters") or {}
    week = params.get("week")
    if not week:
        return reply(400, {"message": "Query-Parameter week fehlt (Teil des Keys)"})
    existing = table.get_item(
        Key={"calendarWeek": week, "bookingId": booking_id}
    ).get("Item")
    if not existing:
        return reply(404, {"message": "Buchung nicht gefunden"})
    # Nur der Eigentuemer (sub) ODER ein Admin (Maria) darf loeschen, Thomas nicht.
    if existing["ownerSub"] != c["sub"] and not is_admin(c):
        return reply(403, {"message": "Nur Eigentuemer oder Admin"})
    table.delete_item(Key={"calendarWeek": week, "bookingId": booking_id})
    return reply(200, {"deleted": booking_id})
