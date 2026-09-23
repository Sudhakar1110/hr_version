# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import getdate, now_datetime, today


class PortalAccessError(frappe.ValidationError):
    pass


SIDEBAR = [
    ("Dashboard", "/dashboard", "octicon-home"),
    ("My Profile", "/profile", "octicon-person"),
    ("Leave & Attendance", "/leave-and-attendance", "octicon-calendar"),
    ("My Work", "/my-work", "octicon-checklist"),
    ("Expenses & Travel", "/expenses-and-travel", "octicon-credit-card"),
    ("Performance", "/performance", "octicon-graph"),
    ("Learning", "/learning", "octicon-book"),
    ("Help & Grievance", "/help-and-grievance", "octicon-question"),
    ("Tasks", "/tasks", "octicon-tasklist"),
    ("Meetings", "/meetings", "octicon-people"),
    ("Recognition", "/recognition", "octicon-star"),
    ("Wellness", "/wellness", "octicon-heart"),
    ("Holiday Calendar", "/holiday-calendar", "octicon-note"),
    ("Onboarding", "/onboarding", "octicon-rocket"),
    ("Offboarding", "/offboarding", "octicon-x-circle"),
    ("Documents", "/documents", "octicon-file-directory"),
    ("Payslips", "/payslips", "octicon-credit-card"),
    ("Directory", "/directory", "octicon-search"),
    ("Announcements", "/announcements", "octicon-megaphone"),
    ("Notifications", "/notifications", "octicon-bell"),
    ("My Requests", "/requests", "octicon-inbox"),
    ("Reports & Analytics", "/reports", "octicon-repo"),
    ("My Team", "/my-team", "octicon-organization"),
    ("Recruitment", "/recruitment", "octicon-briefcase"),
    ("Interviews", "/interviews", "octicon-video"),
    ("AI Assistant", "/ai-assistant", "octicon-bot"),
    ("Settings", "/settings", "octicon-tools"),
]

MANAGER_ROLES = ("HR Portal - Team Leader", "HR Portal - HR Manager")
HR_ROLES = ("HR Manager", "HR User", "HR Portal - HR Manager")
PAYROLL_ROLES = ("HR Portal - Payroll Officer", "HR Manager", "Accounts Manager", "Accounts User")


def require_login():
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect


def get_session_employee(force=False):
    """Return the Employee doc linked to the logged-in user (or None)."""
    user = frappe.session.user
    if user == "Guest":
        if force:
            require_login()
        return None
    name = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not name:
        if force:
            frappe.throw(_("No Employee record is linked to your user account. Please contact HR."), PortalAccessError)
        return None
    return frappe.get_doc("Employee", name)


def get_employee_user(employee):
    return frappe.db.get_value("Employee", employee, "user_id")


def get_roles():
    return set(frappe.get_roles())


def has_any_role(*roles):
    return bool(get_roles().intersection(set(roles)))


def is_hr():
    return has_any_role(*HR_ROLES)


def is_manager():
    return has_any_role(*MANAGER_ROLES)


def is_payroll():
    return has_any_role(*PAYROLL_ROLES)


def get_direct_reports(employee):
    """Direct report employees reporting to `employee`."""
    if not employee:
        return []
    return frappe.get_all(
        "Employee",
        filters={"reports_to": employee, "status": "Active"},
        fields=["name", "employee_name", "department", "designation", "user_id", "reports_to"],
        order_by="employee_name asc",
    )


def get_sidebar_context(context):
    context.sidebar = [
        {"label": label, "url": url, "icon": icon}
        for label, url, icon in SIDEBAR
    ]
    return context


def portal_enabled():
    try:
        return frappe.db.get_single_value("Portal Settings", "portal_enabled", cache=True) or False
    except Exception:
        return True


def format_currency(amount, currency=None):
    from frappe.utils import fmt_money

    try:
        return fmt_money(amount, currency=currency)
    except Exception:
        return "{:,.2f}".format(amount or 0)


def today_str():
    return today()


def now():
    return now_datetime()