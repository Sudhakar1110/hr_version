# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.model.document import Document


class PortalTask(Document):
    def autoname(self):
        pass  # autoname handled by frappe format

    def validate(self):
        if not self.assigned_by:
            self.assigned_by = frappe.session.user
        if self.status == "Done" and not self.completed_on:
            self.completed_on = frappe.utils.now()

    def on_update(self):
        new_assigned_to = self.assigned_to
        if not new_assigned_to:
            return
        user = frappe.get_value("Employee", new_assigned_to, "user_id")
        if user and user != frappe.session.user:
            # notify the assignee (only if status is Open-ish or assignment changed)
            link = "/tasks"
            if user:
                from bizaxl_hrms.bizaxl_hr.doctype.announcement.announcement import notify_user

                notify_user(
                    user=user,
                    title=_("Task assigned: {0}").format(self.subject),
                    category="Task",
                    message=_("You have been assigned a {0} priority task due {1}.").format(self.priority, self.due_date or _("no due date")),
                    document_type="Portal Task",
                    document_name=self.name,
                    link=link,
                )