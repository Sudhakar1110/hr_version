# -*- coding: utf-8 -*-

import math

import frappe
from frappe import _
from frappe.utils import now, today

FIELD_STATUSES = ("Scheduled", "Checked In", "Checked Out", "Completed", "Cancelled")


def list_visit_locations():
    if not frappe.db.exists("DocType", "Visit Location"):
        return []
    return frappe.get_all(
        "Visit Location",
        fields=["name", "location_name", "client", "address", "latitude", "longitude", "radius_km"],
        order_by="location_name asc",
        limit_page_length=200,
    )


def schedule_visit(employee, client=None, purpose=None, visit_location=None):
    """Create a Field Visit record (Scheduled)."""
    if not frappe.db.exists("DocType", "Field Visit"):
        frappe.throw(_("Field Visit doctype not available"))
    doc = frappe.get_doc(
        {
            "doctype": "Field Visit",
            "employee": employee,
            "visit_date": today(),
            "client": client,
            "purpose": purpose,
            "visit_location": visit_location,
            "status": "Scheduled",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def get_my_field_visits(employee, limit=50):
    if not frappe.db.exists("DocType", "Field Visit"):
        return []
    return frappe.get_all(
        "Field Visit",
        filters={"employee": employee},
        fields=[
            "name", "visit_date", "client", "purpose", "visit_location", "status",
            "check_in_time", "check_out_time", "inside_geofence", "notes",
        ],
        order_by="visit_date desc",
        limit_page_length=limit,
    )


def active_field_visits(limit=100):
    if not frappe.db.exists("DocType", "Field Visit"):
        return []
    return frappe.get_all(
        "Field Visit",
        filters={"status": ("in", ("Scheduled", "Checked In"))},
        fields=["name", "employee", "employee_name", "visit_date", "client", "purpose", "status"],
        order_by="visit_date desc",
        limit_page_length=limit,
    )


def _doc(name):
    if not frappe.db.exists("DocType", "Field Visit"):
        frappe.throw(_("Field Visit doctype not available"))
    return frappe.get_doc("Field Visit", name)


def _haversine(lat1, lng1, lat2, lng2):
    """Distance in km between two coords."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _inside_geofence(visit, lat, lng):
    """True if the check-in coords fall within the linked location's radius."""
    if not visit.get("visit_location"):
        return None
    loc = frappe.get_value(
        "Visit Location",
        visit.get("visit_location"),
        ["latitude", "longitude", "radius_km"],
        as_dict=1,
    )
    if not loc or not loc.get("latitude") or not loc.get("longitude"):
        return None
    dist = _haversine(float(lat), float(lng), float(loc["latitude"]), float(loc["longitude"]))
    radius = loc.get("radius_km") or 0.5
    return dist <= radius


def check_in_visit(name, lat, lng, visit_location=None):
    """Verify geo-fence and stamp check-in coordinates/time."""
    doc = _doc(name)
    doc.check_in_lat = float(lat)
    doc.check_in_lng = float(lng)
    doc.check_in_time = now()
    if visit_location:
        doc.visit_location = visit_location
    doc.inside_geofence = _inside_geofence(doc, lat, lng)
    if doc.status == "Scheduled":
        doc.status = "Checked In"
    doc.save(ignore_permissions=True)
    return {
        "name": doc.name,
        "inside_geofence": doc.inside_geofence,
        "check_in_time": str(doc.check_in_time),
    }


def check_out_visit(name, lat, lng, notes=None):
    doc = _doc(name)
    doc.check_out_lat = float(lat)
    doc.check_out_lng = float(lng)
    doc.check_out_time = now()
    if notes:
        doc.notes = notes
    doc.status = "Checked Out" if doc.status != "Completed" else doc.status
    doc.save(ignore_permissions=True)
    return {"name": doc.name, "check_out_time": str(doc.check_out_time)}


def complete_visit(name, notes=None):
    doc = _doc(name)
    if notes:
        doc.notes = notes
    doc.status = "Completed"
    doc.save(ignore_permissions=True)
    return {"name": doc.name}


def route_coverage(field_visit):
    doc = _doc(field_visit)
    loc = None
    if doc.visit_location:
        loc = frappe.get_value(
            "Visit Location",
            doc.visit_location,
            ["location_name", "address", "latitude", "longitude", "radius_km"],
            as_dict=1,
        )
    return {
        "visit": {
            "name": doc.name,
            "visit_date": doc.visit_date,
            "client": doc.client,
            "purpose": doc.purpose,
            "status": doc.status,
            "inside_geofence": doc.inside_geofence,
            "check_in_time": str(doc.check_in_time) if doc.check_in_time else None,
            "check_in_lat": doc.check_in_lat,
            "check_in_lng": doc.check_in_lng,
            "check_out_time": str(doc.check_out_time) if doc.check_out_time else None,
            "check_out_lat": doc.check_out_lat,
            "check_out_lng": doc.check_out_lng,
            "notes": doc.notes,
        },
        "location": loc,
    }