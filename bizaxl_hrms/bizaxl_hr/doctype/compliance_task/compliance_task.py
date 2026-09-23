# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class ComplianceTask(Document):
    def validate(self):
        if self.due_date and self.status == "Pending" and self.due_date < frappe.utils.today():
            self.status = "Overdue"