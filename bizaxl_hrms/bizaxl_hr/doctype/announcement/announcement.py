# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.model.document import Document


class Announcement(Document):
    def validate(self):
        self.author = self.author or frappe.session.user

    def on_update(self):
        if self.flags.in_import or frappe.flags.in_install or frappe.flags.in_migrate:
            return
        if self.published and self.get_doc_before_save() is not None:
            if (self.get_doc_before_save().get("published") or False) != self.published:
                publish_announcement_notification(self.name, self.title, self.message)

    def on_trash(self):
        frappe.db.delete("Portal Notification", {"document_type": "Announcement", "document_name": self.name})


def publish_announcement_notification(announcement, title, message):
    """Push a Portal Notification to every active employee user when an announcement is published."""
    employees = frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "user_id", "employee_name"],
    )
    for emp in employees:
        if not emp.get("user_id"):
            continue
        notify_user(
            user=emp["user_id"],
            title=_("New Announcement: {0}").format(title or announcement),
            category="Announcements",
            message=self_safe_message(message),
            document_type="Announcement",
            document_name=announcement,
            link="/announcements",
        )
    frappe.db.commit()


def self_safe_message(text):
    """Strip HTML for notification bodies."""
    if not text:
        return ""
    import re

    return re.sub(r"<[^>]+>", "", text).strip()[:500]


def notify_user(user, title, category, message, document_type=None, document_name=None, link=None, commit=True):
    """Create a Portal Notification feed entry for a user."""
    if not user or user == "Administrator":
        return
    payload = {
        "doctype": "Portal Notification",
        "user": user,
        "title": title,
        "category": category,
        "message": message,
        "document_type": document_type if document_type else None,
        "document_name": document_name if document_name else None,
        "link": link,
        "read": 0,
    }
    doc = frappe.get_doc(payload)
    doc.insert(ignore_permissions=True, ignore_links=True)
    return doc.name