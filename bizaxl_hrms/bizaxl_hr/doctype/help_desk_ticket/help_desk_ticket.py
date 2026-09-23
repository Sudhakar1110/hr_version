# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now

from bizaxl_hrms.bizaxl_hr.doctype.announcement.announcement import notify_user


class HelpDeskTicket(Document):
    def validate(self):
        if not self.raised_by:
            self.raised_by = frappe.session.user
        if not self.opening_date:
            self.opening_date = now()
        if not self.sla_hours and self.category:
            self.sla_hours = frappe.get_value("Help Desk Category", self.category, "sla_hours") or 8
        if not self.department and self.category:
            self.department = frappe.get_value("Help Desk Category", self.category, "department")

    def on_update(self):
        self._notify_status_change()

    def _notify_status_change(self):
        prev = self.get_doc_before_save()
        if prev and prev.get("status") != self.status:
            message = _("Your ticket {0} is now {1}.").format(self.name, self.status)
            if self.raised_by and self.raised_by != frappe.session.user:
                notify_user(
                    user=self.raised_by,
                    title=_("Ticket {0} {1}").format(self.name, self.status),
                    category="Ticket",
                    message=message,
                    document_type="Help Desk Ticket",
                    document_name=self.name,
                    link="/help-and-grievance",
                )

    def set_resolved(self):
        self.status = "Resolved"
        self.resolution_date = now()
        self.save(ignore_permissions=True)
        return self.name