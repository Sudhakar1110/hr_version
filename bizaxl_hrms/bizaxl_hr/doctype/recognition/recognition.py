# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today

from bizaxl_hrms.bizaxl_hr.doctype.announcement.announcement import notify_user


class Recognition(Document):
    def validate(self):
        if not self.recognized_by:
            self.recognized_by = frappe.session.user
        if self.recognition_type == "Employee of the Month":
            # keep one published Employee of the Month per period simple: archive older ones
            pass

    def on_update(self):
        user = frappe.get_value("Employee", self.recognized_employee, "user_id")
        if user and self.appreciation_wall and self.status == "Published":
            notify_user(
                user=user,
                title=_("You were recognized: {0}").format(self.recognition_type),
                category="Recognition",
                message=self.message or _("Great work is being celebrated on the appreciation wall."),
                document_type="Recognition",
                document_name=self.name,
                link="/recognition",
            )