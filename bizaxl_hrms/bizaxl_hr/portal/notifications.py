# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import time_diff_in_seconds, now_datetime

CATEGORIES = ("Leave", "Payroll", "Attendance", "Task", "Announcements", "Ticket", "Training", "Recognition", "Wellness", "Performance", "System")


def create_notification(user, title, category, message, document_type=None, document_name=None, link=None, commit=False):
    if not user or user == "Guest" or user == "Administrator":
        return None
    if not is_category_enabled(user, category):
        return None
    doc = frappe.get_doc(
        {
            "doctype": "Portal Notification",
            "user": user,
            "title": title,
            "category": category,
            "message": message,
            "document_type": document_type,
            "document_name": document_name,
            "link": link,
            "read": 0,
        }
    )
    doc.insert(ignore_permissions=True)
    if commit:
        frappe.db.commit()
    return doc.name


def is_category_enabled(user, category):
    prefs = frappe.get_all(
        "Notification Preference",
        filters={"user": user, "category": category},
        fields=["enabled", "name"],
    )
    if not prefs:
        return True  # default: enabled
    return bool(prefs[-1].enabled)


def get_feed(user, limit=50, only_unread=False):
    filters = {"user": user}
    if only_unread:
        filters["read"] = 0
    rows = frappe.get_all(
        "Portal Notification",
        filters=filters,
        fields=["name", "title", "category", "message", "read", "link", "created_at"],
        order_by="created_at desc",
        limit_page_length=limit,
    )
    return rows


def unread_count(user):
    return frappe.db.count("Portal Notification", filters={"user": user, "read": 0})


def mark_all_read(user):
    frappe.db.sql("UPDATE `tabPortal Notification` SET `read`=1 WHERE `user`=%s AND `read`=0", user)
    frappe.db.commit()
    return {"updated": True}


def relative_time(dt, reference=None):
    if not dt:
        return ""
    reference = reference or now_datetime()
    if hasattr(dt, "strftime") is False:
        dt = frappe.utils.data.to_datetime(str(dt))
    diff = time_diff_in_seconds(reference, dt)
    mins = int(diff // 60)
    if mins < 1:
        return _("just now")
    if mins < 60:
        return _("{0} minutes ago").format(mins)
    hrs = int(mins // 60)
    if hrs < 24:
        return _("{0} hours ago").format(hrs)
    days = int(hrs // 24)
    if days < 7:
        return _("{0} days ago").format(days)
    return _("{0} weeks ago").format(int(days // 7))