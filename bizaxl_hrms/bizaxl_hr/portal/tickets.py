# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import add_to_date, getdate, now_datetime

SLA_HOURS = {
    "Low": 72,
    "Medium": 24,
    "High": 4,
    "Urgent": 2,
}

STATUS_OPTIONS = ("Open", "In Progress", "Resolved", "Closed", "Rejected")


def resolve_category_sla(category, priority="Medium"):
    """SLA hours: prefer the Help Desk Category's configured SLA, else the priority map."""
    if category:
        cat_sla = frappe.db.get_value("Help Desk Category", category, "sla_hours")
        if cat_sla:
            return int(cat_sla)
    return SLA_HOURS.get(priority, 24)


def create_ticket(subject, description, category=None, priority="Medium", department=None):
    if not frappe.db.exists("DocType", "Help Desk Ticket"):
        frappe.throw(_("Help Desk is not configured yet"))
    doc = frappe.get_doc(
        {
            "doctype": "Help Desk Ticket",
            "subject": subject,
            "description": description,
            "category": category,
            "priority": priority,
            "department": department,
            "status": "Open",
            "sla_hours": resolve_category_sla(category, priority),
            "opening_date": now_datetime(),
            "raised_by": frappe.session.user,
            "employee": frappe.db.get_value("Employee", {"user_id": frappe.session.user}, "name"),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def get_tickets(raised_by=None, limit=100):
    """For the portal - surface a safe field projection."""
    filters = {}
    if raised_by:
        filters["raised_by"] = raised_by
    if not frappe.db.exists("DocType", "Help Desk Ticket"):
        return []
    return frappe.get_all(
        "Help Desk Ticket",
        filters=filters,
        fields=["name", "subject", "status", "category", "priority", "department", "assigned_to", "raised_by", "opening_date", "sla_hours"],
        order_by="opening_date desc",
        limit_page_length=limit,
    )


def get_ticket(name):
    if not frappe.db.exists("DocType", "Help Desk Ticket"):
        return None
    doc = frappe.get_doc("Help Desk Ticket", name)
    return {
        "name": doc.name,
        "subject": doc.subject,
        "description": doc.description,
        "status": doc.status,
        "category": doc.category,
        "priority": doc.priority,
        "department": doc.department,
        "assigned_to": doc.assigned_to,
        "raised_by": doc.raised_by,
        "opening_date": doc.opening_date,
        "response_date": doc.response_date,
        "resolution_date": doc.resolution_date,
        "resolution": doc.resolution,
        "feedback_rating": doc.feedback_rating,
        "feedback": doc.feedback,
        "sla_hours": doc.sla_hours,
    }


def update_ticket_status(name, status, remark=None, resolution=None, rating=None, feedback=None):
    if status not in STATUS_OPTIONS:
        frappe.throw(_("Invalid status: {0}").format(status))
    doc = frappe.get_doc("Help Desk Ticket", name)
    doc.status = status
    if status == "In Progress" and not doc.response_date:
        doc.response_date = now_datetime()
    if status in ("Resolved", "Closed") and not doc.resolution_date:
        doc.resolution_date = now_datetime()
    if resolution:
        doc.resolution = resolution
    if rating is not None:
        doc.feedback_rating = int(rating)
    if feedback:
        doc.feedback = feedback
    if remark:
        doc.add_comment("Comment", remark)
    doc.save(ignore_permissions=True)
    return doc.name


def sla_deadline(doc):
    """ISO deadline computed from opening_date + sla_hours."""
    if not doc.get("sla_hours"):
        return None
    opening = doc.get("opening_date") or now_datetime()
    return add_to_date(opening, hours=int(doc["sla_hours"]))


def sla_status(name):
    doc = frappe.get_doc("Help Desk Ticket", name)
    deadline = sla_deadline(doc)
    if not deadline:
        return "No SLA"
    breached = now_datetime() > deadline
    if doc.status in ("Resolved", "Closed", "Rejected"):
        return "Within SLA" if not breached else "Breached"
    return "Breached" if breached else "Pending"


def get_filtered_tickets(status=None, category=None, priority=None, limit=200):
    filters = {}
    for key, val in [("status", status), ("category", category), ("priority", priority)]:
        if val:
            filters[key] = val
    if not frappe.db.exists("DocType", "Help Desk Ticket"):
        return []
    return frappe.get_all(
        "Help Desk Ticket",
        filters=filters,
        fields=["name", "subject", "status", "category", "priority", "assigned_to", "raised_by", "opening_date", "sla_hours"],
        order_by="opening_date desc",
        limit_page_length=limit,
    )


def sla_breaches_recent(limit=50):
    """Open/In-Progress tickets that have already crossed their SLA deadline."""
    return frappe.db.sql(
        """
        SELECT name, subject, priority, category, assigned_to, opening_date, sla_hours, status
        FROM `tabHelp Desk Ticket`
        WHERE status IN ('Open', 'In Progress')
          AND sla_hours > 0
          AND opening_date < NOW() - INTERVAL sla_hours HOUR
        ORDER BY opening_date ASC
        LIMIT %s
        """,
        limit,
        as_dict=1,
    )


def unassigned_ticket_count():
    return frappe.db.count(
        "Help Desk Ticket",
        filters={"status": ("in", ("Open", "In Progress")), "assigned_to": ("is", "not set")},
    )