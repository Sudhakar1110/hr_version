# -*- coding: utf-8 -*-

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class VendorPayout(Document):
    def validate(self):
        if self.paid_amount and self.status == "Pending":
            self.status = "Processing"