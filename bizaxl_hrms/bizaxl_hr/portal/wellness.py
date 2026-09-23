# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import getdate, today


def get_programs(limit=50):
    if not frappe.db.exists("DocType", "Wellness Program"):
        return []
    return frappe.get_all(
        "Wellness Program",
        fields=["name", "program_name", "program_type", "description", "target", "start_date", "end_date", "vendor", "is_active"],
        order_by="start_date desc",
        limit_page_length=limit,
    )


def get_active_programs():
    if not frappe.db.exists("DocType", "Wellness Program"):
        return []
    today_dt = getdate(today())
    return frappe.get_all(
        "Wellness Program",
        filters={"is_active": 1, "end_date": (">=", today_dt)},
        fields=["name", "program_name", "program_type", "description", "target", "start_date", "end_date", "vendor"],
        order_by="start_date asc",
        limit_page_length=50,
    )


def _program_doc(name):
    if not frappe.db.exists("DocType", "Wellness Program"):
        frappe.throw(_("Wellness Program doctype not available"))
    return frappe.get_doc("Wellness Program", name)


def register_for_program(program, employee, user=None):
    doc = _program_doc(program)
    for row in doc.participants:
        if row.employee == employee:
            return {"name": doc.name, "already_registered": True}
    doc.append(
        "participants",
        {"employee": employee, "status": "Enrolled", "joined_date": today()},
    )
    doc.save(ignore_permissions=True)
    return {"name": doc.name, "already_registered": False}


def my_participations(employee, limit=50):
    """Scan active programs' participant child rows for this employee."""
    if not frappe.db.exists("DocType", "Wellness Program"):
        return []
    results = []
    programs = frappe.get_all("Wellness Program", fields=["name", "program_name"], limit_page_length=500)
    for p in programs:
        doc = frappe.get_doc("Wellness Program", p["name"])
        for row in doc.participants:
            if row.employee == employee and len(results) < limit:
                results.append(
                    {
                        "program": doc.name,
                        "program_name": doc.program_name,
                        "program_type": doc.program_type,
                        "status": row.status,
                        "joined_date": row.joined_date,
                    }
                )
                break
    results.sort(key=lambda r: (r.get("joined_date") or ""), reverse=True)
    return results[:limit]


def submit_counselling_request(reason, category="General", employee=None):
    if not frappe.db.exists("DocType", "Counselling Request"):
        frappe.throw(_("Counselling module is not configured yet"))
    doc = frappe.get_doc(
        {
            "doctype": "Counselling Request",
            "employee": employee,
            "requested_by": frappe.session.user,
            "reason": reason,
            "category": category,
            "status": "Open",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name