# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class EmployeeGrievance(Document):
    def validate(self):
        if not self.raised_by:
            self.raised_by = frappe.session.user