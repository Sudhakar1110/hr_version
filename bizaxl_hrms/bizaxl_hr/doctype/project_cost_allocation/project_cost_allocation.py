# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate

from bizaxl_hrms.bizaxl_hr.doctype.field_visit.field_visit import haversine  # noqa: F401  (shared geo helper)


class ProjectCostAllocation(Document):
    def validate(self):
        self.compute_total_cost()

    def compute_total_cost(self):
        if self.allocation_type == "Hourly" and self.start_date and self.end_date:
            days = (getdate(self.end_date) - getdate(self.start_date)).days + 1
            if days < 0:
                days = 0
            self.total_cost = flt(self.rate) * flt(self.hours_per_day or 8) * days
        elif self.allocation_type == "Daily" and self.start_date and self.end_date:
            days = (getdate(self.end_date) - getdate(self.start_date)).days + 1
            self.total_cost = flt(self.rate) * max(days, 0)
        elif self.allocation_type == "Fixed":
            self.total_cost = flt(self.rate)
        else:
            self.total_cost = self.total_cost or 0