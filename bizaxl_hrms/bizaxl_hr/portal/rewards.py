# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import flt, today

POINT_VALUES = {
    "Appreciation": 1,
    "Badge": 2,
    "Milestone": 3,
    "Award": 5,
    "Employee of the Month": 10,
    "Anniversary": 1,
}

PUBLISHED_STATES = ("Published",)


def give_recognition(recipient, title, rec_type="Appreciation", points=None, message=None, giver=None):
    """Award recognition. `recipient` = Employee name; `giver` = User name."""
    giver = giver or frappe.session.user
    doc = frappe.get_doc(
        {
            "doctype": "Recognition",
            "recognized_employee": recipient,
            "recognized_by": giver,
            "recognition_type": rec_type,
            "badge_name": title,
            "energy_points": points if points is not None else POINT_VALUES.get(rec_type, 1),
            "posting_date": today(),
            "appreciation_wall": 1,
            "status": "Published",
            "message": message,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name


def leaderboard(limit=20):
    """Top employees ranked by earned energy points."""
    if not frappe.db.exists("DocType", "Recognition"):
        return []
    return frappe.db.sql(
        """
        SELECT rec.recognized_employee AS employee, emp.employee_name AS employee_name,
               SUM(rec.energy_points) AS points, COUNT(rec.name) AS recognitions
        FROM `tabRecognition` rec
        INNER JOIN `tabEmployee` emp ON emp.name = rec.recognized_employee
        WHERE rec.docstatus < 2 AND rec.status = 'Published'
        GROUP BY rec.recognized_employee, emp.employee_name
        ORDER BY points DESC
        LIMIT %s
        """,
        limit,
        as_dict=1,
    )


def recognition_feed(limit=50):
    """Published recognitions surfaced on the appreciation wall."""
    if not frappe.db.exists("DocType", "Recognition"):
        return []
    return frappe.get_all(
        "Recognition",
        filters={"status": "Published", "appreciation_wall": 1},
        fields=[
            "name", "badge_name", "recognition_type", "message", "recognized_employee",
            "recognized_by", "energy_points", "posting_date",
        ],
        order_by="posting_date desc",
        limit_page_length=limit,
    )


def my_points(employee):
    """Points earned by the user as recipient, and points they have given."""
    if not employee:
        return {"points": 0, "count": 0, "given": 0}
    rows = frappe.get_all(
        "Recognition",
        filters={"recognized_employee": employee},
        fields=["energy_points"],
        limit_page_length=0,
    )
    given_rows = frappe.get_all(
        "Recognition",
        filters={"recognized_by": frappe.session.user},
        fields=["energy_points"],
        limit_page_length=0,
    )
    total = sum(flt(r["energy_points"] or 0) for r in rows)
    given = sum(flt(r["energy_points"] or 0) for r in given_rows)
    return {"points": total, "count": len(rows), "given": given}


def my_last_reward(employee):
    if not employee:
        return None
    rows = frappe.get_all(
        "Recognition",
        filters={"recognized_employee": employee},
        fields=["name", "badge_name", "recognition_type", "energy_points", "posting_date", "message"],
        order_by="posting_date desc",
        limit=1,
    )
    return rows[0] if rows else None