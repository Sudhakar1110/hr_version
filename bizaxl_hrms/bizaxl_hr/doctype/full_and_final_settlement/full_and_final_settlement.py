# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FullandFinalSettlement(Document):
    def validate(self):
        if not self.get("ffs_tasks"):
            for name in ["Clearance confirmed", "Manager sign-off", "IT asset recovery", "Finance settlement"]:
                self.append("ffs_tasks", {"task_name": name, "status": "Pending"})
        self.compute_net_payable()

    def compute_net_payable(self):
        positive = flt(self.gross_earned) + flt(self.notice_pay_instead) + flt(self.gratuity)
        negative = (
            flt(self.unpaid_leave_deduction)
            + flt(self.pending_advance)
            + flt(self.other_recoveries)
            + flt(self.employee_pf)
            + flt(self.employee_esi)
            + flt(self.tds)
            + flt(self.professional_tax)
        )
        self.net_payable = positive - negative