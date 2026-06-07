import os
import json
import uuid
import boto3
from boto3.dynamodb.conditions import Key
from datetime import date


TABLE_NAME = os.environ["TABLE_NAME"]
table = boto3.resource("dynamodb").Table(TABLE_NAME)


DEVICES = [
    {"deviceId": "router-1",   "name": "Router 1",   "category": "Routing",    "owners": ["Thomas", "Sarah"], "description": "Core Router Standort A"},
    {"deviceId": "router-2",   "name": "Router 2",   "category": "Routing",    "owners": ["Thomas"],          "description": "Core Router Standort B"},
    {"deviceId": "switch-1",   "name": "Switch 1",   "category": "Switching",  "owners": ["Lena", "Marco"],   "description": "Access Switch Floor 1"},
    {"deviceId": "switch-2",   "name": "Switch 2",   "category": "Switching",  "owners": ["Lena"],            "description": "Access Switch Floor 2"},
    {"deviceId": "dhcp-1",     "name": "DHCP 1",     "category": "Services",   "owners": ["Sarah"],           "description": "DHCP Server"},
    {"deviceId": "dwdm-1",     "name": "DWDM 1",     "category": "Transport",  "owners": ["Thomas", "Lena"], "description": "DWDM Multiplexer"},
    {"deviceId": "cluster-1",  "name": "Cluster 1",  "category": "Compute",    "owners": ["Marco", "Sarah"],  "description": "Kubernetes Cluster"},
    {"deviceId": "firewall-1", "name": "Firewall 1", "category": "Security",   "owners": ["Thomas", "Marco"], "description": "Perimeter Firewall"},
]


def respond(status, body):
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body),
    }

def get_identity(event):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    sub = claims.get("sub")
    email = claims.get("email", "")
    groups = claims.get("cognito:groups", "")   # z.B. "[admin]" oder ""
    return sub, email, groups


def is_admin(groups):
    return groups.strip("[]") == "admin"


def lambda_handler(event, context):
    print(json.dumps(event))
    method = event["requestContext"]["http"]["method"]
    path = event["rawPath"]

    print(method, path)

    if method == "OPTIONS":                                  return respond(200, {})
    if path == "/devices"  and method == "GET":              return get_devices()
    if path == "/bookings" and method == "GET":              return get_bookings(event)
    if path == "/bookings" and method == "POST":             return create_booking(event)
    if path.startswith("/bookings/") and method == "DELETE": return delete_booking(event, path)

    return respond(404, {"message": f"Route not found: {method} {path}"})


def get_devices():
    return respond(200, DEVICES)


def get_bookings(event):
    week = event["queryStringParameters"]["week"]
    result = table.query(KeyConditionExpression=Key("calendarWeek").eq(week))
    return respond(200, result.get("Items", []))


def create_booking(event):
    sub, email, groups = get_identity(event)
    body = json.loads(event["body"])
    booking = {
        "calendarWeek": get_calendar_week(body.get("startDate")),
        "bookingId": str(uuid.uuid4()),
        "ownerSub": sub,            # verifiziert, fuer die Eigentumspruefung
        "engineerName": email,      # Anzeige-Name aus dem Token, nicht vom Client
        "deviceIds": body.get("deviceIds", []),
        "startDate": body.get("startDate"),
        "startSlot": body.get("startSlot"),
        "endDate": body.get("endDate"),
        "endSlot": body.get("endSlot"),
        "desc": body.get("desc", ""),
        "details": body.get("details", ""),
        "status": "confirmed",
    }
    table.put_item(Item=booking)
    return respond(201, booking)


def delete_booking(event, path):
    sub, email, groups = get_identity(event)
    booking_id = path.split("/")[-1]
    week = event["queryStringParameters"]["week"]

    resp = table.get_item(Key={"calendarWeek": week, "bookingId": booking_id})
    item = resp.get("Item")

    # Eigentum ODER Admin
    if item.get("ownerSub") != sub and not is_admin(groups):
        return respond(403, {"message": "Nur der Ersteller oder ein Admin darf löschen."})

    table.delete_item(Key={"calendarWeek": week, "bookingId": booking_id})
    return respond(200, {"deleted": booking_id})


def get_calendar_week(date_str):
    # ============================================================
    # Berechnet die ISO-Kalenderwoche aus einem Datum-String.
    # ============================================================
    d = date.fromisoformat(date_str)
    year, week, day = d.isocalendar()
    return f"{year}-W{week:02d}"
    # Beispiel:
    # get_calendar_week('2026-05-12') -> '2026-W20'
    # get_calendar_week('2026-05-07') -> '2026-W19'
