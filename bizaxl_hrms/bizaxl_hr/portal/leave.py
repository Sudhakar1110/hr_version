# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate, today


def get_leave_types():
    return frappe.get_all("Leave Type", pluck="name", order_by="name")


def get_leave_balance(employee, leave_type, on_date=None):
    """Balance available for a leave type using Leave Allocation records."""
    on_date = on_date or today()
    allocations = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": employee,
            "leave_type": leave_type,
            "docstatus": 1,
            "from_date": ("<=", on_date),
            "to_date": (">=", on_date),
        },
        fields=["total_leaves_allocated", "leaves_taken"],
    )
    balance = 0.0
    for a in allocations:
        balance += flt(a.total_leaves_allocated) - flt(a.leaves_taken)
    return max(balance, 0.0)


def get_leave_balances(employee, on_date=None):
    on_date = on_date or today()
    balances = []
    for lt in get_leave_types():
        balance = get_leave_balance(employee, lt, on_date)
        if balance > 0:
            balances.append({"leave_type": lt, "balance": balance})
    return balances


def get_leave_summary(employee):
    """Used by the dashboard Leave Balance widget."""
    balances = get_leave_balances(employee)
    total = sum(b["balance"] for b in balances)
    in_use = get_leaves_in_use(employee)
    return {
        "balances": balances,
        "total_available": round(total, 1),
        "in_use": in_use,
    }


def get_leaves_in_use(employee):
    filters = {
        "employee": employee,
        "docstatus": 1,
        "status": ("in", ("Open", "Approved")),
    }
    rows = frappe.get_all(
        "Leave Application",
        fields=["leave_type", "from_date", "to_date", "total_leave_days", "status"],
        filters=filters,
    )
    days = 0
    for r in rows:
        days += flt(r.total_leave_days or 0)
    return days


def get_leave_applications(employee, limit=20):
    return frappe.get_all(
        "Leave Application",
        filters={"employee": employee},
        fields=["name", "leave_type", "from_date", "to_date", "total_leave_days", "status", "posting_date"],
        order_by="posting_date desc",
        limit_page_length=limit,
    )


def team_leave_calendar(employee):
    """Aggregate of leave applications for the manager's direct reports."""
    from bizaxl_hrms.bizaxl_hr.portal.utils import get_direct_reports

    team = get_direct_reports(employee)
    names = [t["name"] for t in team]
    if not names:
        return []
    rows = frappe.get_all(
        "Leave Application",
        filters={"employee": ("in", names), "docstatus": 1, "status": "Approved"},
        fields=["name", "employee", "leave_type", "from_date", "to_date", "total_leave_days"],
        order_by="from_date asc",
        limit_page_length=100,
    )
    names_map = {t["name"]: t["employee_name"] for t in team}
    for r in rows:
        r["employee_name"] = names_map.get(r["employee"], r["employee"])
    return rows


def leave_policy_for_employee(employee):
    """Fetch the leave policy assignment for an employee."""
    assignment = frappe.get_all(
        "Leave Policy Assignment",
        filters={"employee": employee, "docstatus": 1},
        fields=["leave_policy", "effective_from", "effective_to", "leave_period"],
        order_by="effective_from desc",
        limit=1,
    )
    return assignment[0] if assignment else None


def get_encashment_rule(employee, leave_type):
    """Return encashable cash value/day for a leave type if applicable."""
    encas = frappe.get_all(
        "Leave Encashment",
        filters={"employee": employee, "leave_type": leave_type, "docstatus": 1},
        fields=["encashment_amount", "total_encashable_days", "status"],
        limit=1,
    )
    return encas[0] if encas else None