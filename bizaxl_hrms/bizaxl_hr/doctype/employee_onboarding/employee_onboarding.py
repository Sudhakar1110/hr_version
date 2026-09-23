# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.model.document import Document


class EmployeeOnboarding(Document):
    def validate(self):
        self.update_progress()

    def update_progress(self):
        tasks = self.get("onboarding_tasks") or []
        if not tasks:
            self.progress = 0
            return
        done = sum(1 for t in tasks if t.status == "Done")
        self.progress = round(done * 100 / len(tasks))