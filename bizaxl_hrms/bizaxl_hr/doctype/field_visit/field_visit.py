# -*- coding: utf-8 -*-

import math

import frappe
from frappe.model.document import Document


class FieldVisit(Document):
    def validate(self):
        if self.visit_location:
            self.validate_geofence()

    def validate_geofence(self):
        loc = frappe.get_doc("Visit Location", self.visit_location)
        if self.check_in_lat and self.check_in_lng and loc.latitude and loc.longitude:
            distance = haversine(loc.latitude, loc.longitude, self.check_in_lat, self.check_in_lng)
            self.inside_geofence = 1 if distance <= (loc.radius_km or 0.5) else 0


def haversine(lat1, lng1, lat2, lng2):
    """Great-circle distance in kilometres."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))