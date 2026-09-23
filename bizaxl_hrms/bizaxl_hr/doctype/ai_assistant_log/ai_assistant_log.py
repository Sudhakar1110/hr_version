# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class AIAssistantLog(Document):
    def validate(self):
        if not self.user:
            self.user = frappe.session.user