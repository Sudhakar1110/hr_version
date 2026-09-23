# -*- coding: utf-8 -*-

import frappe
from frappe import _

PORTAL_ROLES = [
    ("HR Portal - Founder", "Company-wide summary access for Founder / CEO."),
    ("HR Portal - HR Manager", "Runs HR operations end-to-end: hiring, org-wide approvals, payroll oversight, training, policies."),
    ("HR Portal - Team Leader", "Manages one team: approves leave/attendance, assigns tasks, reviews performance."),
    ("HR Portal - Employee", "Everyday self-service: check in/out, apply leave, view payslip, own tasks and training."),
    ("HR Portal - Recruiter", "Owns the hiring pipeline: job postings, screening, interviews, offers."),
    ("HR Portal - Interviewer", "Temporary role for panellists: sees assigned interviews and gives feedback."),
    ("HR Portal - Payroll Officer", "Processes monthly salaries, payslips, tax/PF/ESI, bonuses and deductions."),
    ("HR Portal - Trainer", "Runs training programs, assigns courses, builds quizzes, issues certificates."),
    ("HR Portal - IT Support", "Handles employee support tickets, asset allocation, and software requests."),
]

DEFAULT_TICKET_CATEGORIES = [
    ("HR Support", "Questions and requests for the HR team."),
    ("IT Support", "Laptop, email, software and access issues."),
    ("Finance", "Payslips, reimbursements and payment queries."),
    ("Facilities", "Workstations, offices and campus requests."),
    ("Payroll", "Salary, PF/ESI/TDS and statutory queries."),
]

DEFAULT_WELLNESS_PROGRAMS = [
    ("Annual Health Checkup", "Health Program", "Free preventive health checkup camp for all employees."),
    ("10K Steps Challenge", "Fitness Challenge", "Monthly step challenge with team rankings."),
    ("Confidential Counselling", "Mental Wellness", "Private counselling support - HR does not see details."),
]


def create_roles():
    """Create the 9 Bizaxl HR portal roles (idempotent)."""
    for role, description in PORTAL_ROLES:
        if not frappe.db.exists("Role", role):
            frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 0}).insert(ignore_permissions=True, ignore_if_duplicate=True)


def create_ticket_categories():
    if not frappe.db.exists("Help Desk Category", "IT Support"):
        for name, desc in DEFAULT_TICKET_CATEGORIES:
            if not frappe.db.exists("Help Desk Category", name):
                frappe.get_doc({"doctype": "Help Desk Category", "category_name": name, "description": desc}).insert(ignore_permissions=True)


def create_wellness_programs():
    if frappe.db.count("Wellness Program") == 0:
        for name, ptype, desc in DEFAULT_WELLNESS_PROGRAMS:
            frappe.get_doc({
                "doctype": "Wellness Program",
                "program_name": name,
                "program_type": ptype,
                "description": desc,
                "is_active": 1,
            }).insert(ignore_permissions=True)


def ensure_portal_settings():
    if not frappe.db.exists("Portal Settings", "Portal Settings"):
        settings = frappe.get_doc({
            "doctype": "Portal Settings",
            "portal_enabled": 1,
            "ai_assistant_enabled": 1,
            "default_sla_hours": 8,
        })
        # Single doctype auto-names as the doctype name
        settings.flags.ignore_mandatory = True
        settings.insert(ignore_permissions=True)


def before_install():
    pass  # nothing required before installation


def after_install():
    create_roles()
    create_ticket_categories()
    create_wellness_programs()
    ensure_portal_settings()
    frappe.db.commit()