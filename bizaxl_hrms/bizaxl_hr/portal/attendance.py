# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, getdate, now, today


def get_today_checkins(employee, on_date=None):
    """Employee Checkin rows for the given date."""
    dt = getdate(on_date or today())
    filters = {
        "employee": employee,
        "time": ("between", [str(dt) + " 00:00:00", str(dt) + " 23:59:59"]),
    }
    return frappe.get_all(
        "Employee Checkin",
        filters=filters,
        fields=["name", "log_type", "time", "shift", "actual_time", "device_id"],
        order_by="time asc",
    )


def get_today_attendance(employee, on_date=None):
    dt = getdate(on_date or today())
    return frappe.db.get_value(
        "Attendance",
        {"employee": employee, "attendance_date": dt},
        ["status", "check_in", "check_out", "name", "late_entry", "early_exit", "attendance_date"],
        as_dict=1,
    )


def checkin_overview(employee, on_date=None):
    """Public summary used by the Attendance widget."""
    checkins = get_today_checkins(employee, on_date)
    status = "No check-in yet"
    first_in = None
    last_out = None
    for c in checkins:
        if c.log_type == "IN" and first_in is None:
            first_in = c
        if c.log_type == "OUT":
            last_out = c
    if first_in:
        status = "Checked in at " + str(first_in.time)[11:16]
    elif checkins:
        status = "Logged"
    def _hm(value):
        return str(value)[11:16] if value else None
    return {
        "status": status,
        "first_in": _hm(first_in.time) if first_in else None,
        "last_out": _hm(last_out.time) if last_out else None,
        "shift": frappe.get_value("Employee", employee, "shift") or "General 9-6",
    }


def last_30_days_summary(employee, on_date=None):
    """Present / Absent / Leave / Holiday counts over the last 30 working days."""
    end = getdate(on_date or today())
    start = add_days(end, -29)
    statuses = frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ("between", [start, end]),
        },
        fields=["status", "attendance_date"],
    )
    summary = {"Present": 0, "Absent": 0, "On Leave": 0, "Half Day": 0, "Holiday": 0, "Work From Home": 0}
    for s in statuses:
        summary[s.status] = summary.get(s.status, 0) + 1
    total_days = len(statuses)
    pct = round(summary.get("Present", 0) * 100 / max(total_days, 1))
    return {
        "summary": summary,
        "present": summary.get("Present", 0),
        "absent": summary.get("Absent", 0),
        "leave": summary.get("On Leave", 0),
        "total": total_days,
        "percentage": pct,
    }


def attendance_calendar(employee, month):
    """Calendar data for one month (YYYY-MM)."""
    from frappe.utils.data import month_start, month_end

    start = month_start(month)
    end = month_end(month)
    rows = frappe.get_all(
        "Attendance",
        filters={"employee": employee, "attendance_date": ("between", [start, end])},
        fields=["attendance_date", "status", "check_in", "check_out"],
        order_by="attendance_date asc",
    )
    return rows


def attendance_requests(employee, limit=20):
    """Attendance Request (regularisation) rows."""
    return frappe.get_all(
        "Attendance Request",
        filters={"employee": employee},
        fields=["name", "reason", "from_date", "to_date", "status", "attendance_request_type"],
        order_by="from_date desc",
        limit_page_length=limit,
    )


def overtime_summary(employee, from_date, to_date):
    """Approximate overtime hours from attendance check-out vs shift end (sample)."""
    return {
        "from_date": from_date,
        "to_date": to_date,
        "overtime_hours": 0,
        "late_entries": 0,
        "early_exits": 0,
    }


def mark_checkin(employee, log_type="IN", time=None, skip_errors=False):
    doc = frappe.get_doc(
        {
            "doctype": "Employee Checkin",
            "employee": employee,
            "log_type": log_type,
            "time": time or now(),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc.name