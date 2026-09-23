# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class Meeting(Document):
    def validate(self):
        if not self.organizer:
            self.organizer = frappe.session.user