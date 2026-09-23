# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document


class EmployeeOffboarding(Document):
    def validate(self):
        self.set_default_clearance_tasks()

    def set_default_clearance_tasks(self):
        defaults = [
            ("Return company laptop", "IT"),
            ("Return ID card & access cards", "IT"),
            ("IT account deactivation", "IT"),
            ("Handover documentation", "Manager"),
        ]
        if not self.get("clearance_tasks"):
            for name, role in defaults:
                self.append("clearance_tasks", {"task_name": name, "owner_role": role, "status": "Pending"})

    def progress(self):
        tasks = self.clearance_tasks or []
        if not tasks:
            return 0
        done = sum(1 for t in tasks if t.status == "Done")
        return round(done * 100 / len(tasks))