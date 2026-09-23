# -*- coding: utf-8 -*-
#  -- default frequencies: daily / monthly / quarterly (customizable in Bizaxl Portal Settings)

import frappe
from frappe import _
from frappe.utils import add_days, add_months, getdate, today

from bizaxl_hrms.bizaxl_hr.portal.leave import get_leave_balances
from bizaxl_hrms.bizaxl_hr.portal.notifications import create_notification


def daily():
    """Run once per day - compiles digest, chases pending approvals + expiring contracts."""
    _digest_for_all()
    _contract_expiry_alerts()
    _pending_leave_watch()
    frappe.db.commit()


# ---------------------------------------------------------------------------
# Entry points referenced from hooks.py scheduler_events
# ---------------------------------------------------------------------------


def daily_digest():
    """hooks.py: daily() -> managed digest of balance / approvals for each user."""
    _digest_for_all()
    _pending_leave_watch()
    frappe.db.commit()


def sla_escalations():
    """hooks.py: daily() -> remind agents about breached and soon-to-breach tickets."""
    from bizaxl_hrms.bizaxl_hr.portal.tickets import sla_breaches_recent

    breached = sla_breaches_recent(limit=50)
    for t in breached:
        if not t.get("assigned_to"):
            continue
        create_notification(
            t["assigned_to"],
            _("SLA breached: {0}").format(t["subject"]),
            "Ticket",
            _("Ticket {0} crossed its response SLA on {1}.").format(t["name"], t["opening_date"]),
            document_type="Help Desk Ticket",
            document_name=t["name"],
            link="/help-and-grievance",
        )
    frappe.db.commit()


def compliance_reminders():
    """hooks.py: hourly() -> proactively create overdue Compliance Task items."""
    _compliance_checklist()
    frappe.db.commit()


def weekly():
    pass


def monthly():
    _leave_balance_summary()
    frappe.db.commit()


def quarterly():
    competitive_landscape = _compliance_checklist()
    frappe.db.commit()


def _digest_for_all():
    """Notify every active employee with an unread digest. The feed filters
    silently by preference; we only fire when the category is enabled."""
    users = frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
    if not frappe.db.exists("DocType", "Portal Notification"):
        return
    for user in users:
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            continue
        balances = get_leave_balances(employee)
        if balances:
            line = ", ".join("{} ({}d)".format(b["leave_type"], b["balance"]) for b in balances[:3])
        else:
            line = "No leave allocations currently."
        create_notification(
            user,
            _("Your daily digest"),
            "Announcements",
            _("Leave balance: {0}").format(line),
            link="/dashboard",
        )


def _contract_expiry_alerts(days=60):
    """Alert when an employment contract is nearing expiry."""
    from frappe.utils import data

    today_dt = getdate(today())
    end = add_days(today_dt, days)
    if not frappe.db.exists("DocType", "Employee") or not frappe.db.exists("DocType", "Employment Type"):
        return
    emps = frappe.get_all(
        "Employee",
        filters={"status": "Active", "date_of_retirement": ("between", [today_dt, end])},
        fields=["name", "employee_name", "user_id", "date_of_retirement"],
    )
    for e in emps:
        if e.get("user_id"):
            create_notification(
                e["user_id"],
                _("Contract/retirement date approaching"),
                "System",
                _("Your scheduled last working day ({0}) is within {1} days.").format(e["date_of_retirement"], days),
                link="/profile",
            )


def _pending_leave_watch():
    """Notify HR managers of leave applications pending approval for > 2 days."""
    two_days_back = add_days(today(), -2)
    pending = frappe.get_all(
        "Leave Application",
        filters={"docstatus": 1, "status": "Open", "posting_date": ("<=", two_days_back)},
        fields=["name", "employee", "from_date", "to_date"],
        limit_page_length=50,
    )
    if not pending:
        return
    approvers = [
        u
        for u in frappe.get_all("User", filters={"enabled": 1, "user_type": "System User"}, pluck="name")
        if "HR Manager" in frappe.get_roles(u)
    ]
    for approver in approvers:
        create_notification(
            approver,
            _("{0} leave request(s) awaiting approval"),
            "Leave",
            _("There are {0} leave applications older than 2 days pending approval. Action required.").format(len(pending)),
            link="/leave-and-attendance",
        )


def _leave_balance_summary():
    """Monthly silent-keep: currently a no-op placeholder for future reporting."""
    return True


def _compliance_checklist():
    """Quarterly statutory compliance job - generates Compliance Task records as needed."""
    if not frappe.db.exists("DocType", "Compliance Task"):
        return
    tasks = [
        ("File PF returns (Form 3A)", "Statutory"),
        ("File ESI monthly returns", "Statutory"),
        ("Verify professional tax remittances", "Statutory"),
        ("Reconcile income-tax (TDS) challans", "Statutory"),
        ("Renew labour welfare fund declarations", "Statutory"),
        ("Audit of full & final settlements", "Employee Records"),
    ]
    created = 0
    for description, category in tasks:
        exists = frappe.get_all(
            "Compliance Task",
            filters={"description": description, "month": today()[:7]},
            fields=["name"],
            limit=1,
        )
        if not exists:
            doc = frappe.get_doc(
                {
                    "doctype": "Compliance Task",
                    "description": description,
                    "category": category,
                    "month": today()[:7],
                    "status": "Open",
                }
            )
            doc.insert(ignore_permissions=True)
            created += 1
    return {"tasks_created": created, "month": today()[:7]}