# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class SalesCommissionLog(Document):
    def validate(self):
        if self.plan and self.achieved_amount:
            self.applicable_rate = self.get_applicable_rate()
            self.commission_amount = flt(self.achieved_amount) * flt(self.applicable_rate) / 100

    def get_applicable_rate(self):
        plan = frappe.get_doc("Sales Commission Plan", self.plan)
        for slab in plan.slabs:
            low = flt(slab.from_amount or 0)
            high = flt(slab.to_amount or 0) or float("inf")
            if low <= flt(self.achieved_amount) <= high:
                if slab.flat_amount:
                    self.commission_amount = slab.flat_amount
                    return 0
                return slab.rate or 0
        return 0