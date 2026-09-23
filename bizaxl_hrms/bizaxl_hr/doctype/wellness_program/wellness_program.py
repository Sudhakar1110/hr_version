# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class WellnessProgram(Document):
    def enroll(self, employee):
        """Enroll an employee in this program (idempotent)."""
        for row in self.participants:
            if row.employee == employee:
                return row
        row = self.append("participants", {
            "employee": employee,
            "status": "Enrolled",
            "joined_date": frappe.utils.today(),
        })
        self.save(ignore_permissions=True)
        return row