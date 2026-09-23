# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class HelpDeskCategory(Document):
    def validate(self):
        self.sla_hours = self.sla_hours or 8