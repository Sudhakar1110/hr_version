# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class PortalNotification(Document):
    def validate(self):
        self.created_at = self.created_at or frappe.utils.now()

    def before_save(self):
        # Employees may only touch their own notifications.
        if not frappe.session.user:
            return
        if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles():
            return
        if "HR Portal - HR Manager" not in frappe.get_roles():
            self.user = frappe.session.user

    def on_update(self):
        if self.link:
            self.link = self.link


def mark_read(docname):
    doc = frappe.get_doc("Portal Notification", docname)
    if doc.user != frappe.session.user and not doc.has_permission("write"):
        frappe.throw(frappe._("Permission denied"))
    if not doc.read:
        doc.db_set("read", 1)
    return {"message": "ok", "name": doc.name}