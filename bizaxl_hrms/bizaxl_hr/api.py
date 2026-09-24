# -*- coding: utf-8 -*-
# Whitelisted API handlers used by the Bizaxl HR Portal frontend.
# Every endpoint validates the session before touching data.

import frappe
from frappe import _
from frappe.utils import getdate, today

from bizaxl_hrms.bizaxl_hr.portal.utils import (
    require_login,
    get_session_employee,
    get_sidebar_context,
    is_hr,
    is_payroll,
    get_direct_reports,
)

# ---------------------------------------------------------------------------
# Session / navigation
# ---------------------------------------------------------------------------


@frappe.whitelist()
def sidebar():
    ctx = frappe._dict()
    return get_sidebar_context(ctx).sidebar


@frappe.whitelist()
def current_user():
    require_login()
    employee = get_session_employee()
    return {
        "user": frappe.session.user,
        "employee": employee.name if employee else None,
        "employee_name": employee.employee_name if employee else None,
        "roles": sorted(frappe.get_roles()),
    }


@frappe.whitelist()
def upcoming_holidays(limit=5):
    from frappe.utils import today as _today

    require_login()
    if not frappe.db.exists("DocType", "Holiday"):
        return []
    return frappe.get_all(
        "Holiday",
        filters={"holiday_date": (">=", _today())},
        fields=["holiday_date", "description", "weekly_off"],
        order_by="holiday_date asc",
        limit_page_length=int(limit),
    )


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------


@frappe.whitelist()
def attendance_today():
    from bizaxl_hrms.bizaxl_hr.portal.attendance import checkin_overview, get_today_attendance

    require_login()
    emp = get_session_employee(force=True)
    return {
        "overview": checkin_overview(emp.name),
        "attendance": get_today_attendance(emp.name),
    }


@frappe.whitelist()
def attendance_summary(days=30):
    from bizaxl_hrms.bizaxl_hr.portal.attendance import last_30_days_summary

    require_login()
    emp = get_session_employee(force=True)
    return last_30_days_summary(emp.name)


@frappe.whitelist()
def attendance_calendar(month=None):
    from bizaxl_hrms.bizaxl_hr.portal.attendance import attendance_calendar

    require_login()
    emp = get_session_employee(force=True)
    return attendance_calendar(emp.name, month or today()[:7])


@frappe.whitelist()
def get_attendance_requests():
    from bizaxl_hrms.bizaxl_hr.portal.attendance import attendance_requests

    require_login()
    emp = get_session_employee(force=True)
    return attendance_requests(emp.name)


@frappe.whitelist()
def submit_attendance_request(from_date, to_date, reason, type="Regularization"):
    require_login()
    emp = get_session_employee(force=True)
    doc = frappe.get_doc(
        {
            "doctype": "Attendance Request",
            "employee": emp.name,
            "from_date": from_date,
            "to_date": to_date,
            "reason": reason,
            "attendance_request_type": type,
        }
    )
    doc.insert(ignore_permissions=True)
    return {"name": doc.name, "status": "Submitted"}


@frappe.whitelist()
def mark_checkin(log_type="IN"):
    from bizaxl_hrms.bizaxl_hr.portal.attendance import mark_checkin

    require_login()
    emp = get_session_employee(force=True)
    name = mark_checkin(emp.name, log_type=log_type)
    return {"name": name, "log_type": log_type}


# ---------------------------------------------------------------------------
# Leave
# ---------------------------------------------------------------------------


@frappe.whitelist()
def leave_summary():
    from bizaxl_hrms.bizaxl_hr.portal.leave import get_leave_summary

    require_login()
    emp = get_session_employee(force=True)
    return get_leave_summary(emp.name)


@frappe.whitelist()
def leave_applications(limit=20):
    from bizaxl_hrms.bizaxl_hr.portal.leave import get_leave_applications

    require_login()
    emp = get_session_employee(force=True)
    return get_leave_applications(emp.name, limit=int(limit))


@frappe.whitelist()
def apply_leave(leave_type, from_date, to_date, reason=None, half_day=0, half_day_date=None):
    """
    Apply for leave. Balance and workflow are validated before submission.
    """
    from frappe.utils import date_diff as _date_diff

    from bizaxl_hrms.bizaxl_hr.portal.leave import get_leave_balance

    require_login()
    emp = get_session_employee(force=True)
    if not frappe.db.exists("Leave Type", leave_type):
        frappe.throw(_("Invalid leave type: {0}").format(leave_type))
    if not from_date or not to_date:
        frappe.throw(_("Leave dates are required"))
    if from_date > to_date:
        frappe.throw(_("From date cannot be after To date"))

    requested_days = _date_diff(to_date, from_date) + 1
    half_day = int(half_day or 0)
    if half_day:
        requested_days = 0.5
        half_day_date = half_day_date or from_date

    balance = get_leave_balance(emp.name, leave_type, from_date)
    allocation = frappe.get_all(
        "Leave Allocation",
        filters={
            "employee": emp.name,
            "leave_type": leave_type,
            "docstatus": 1,
            "from_date": ("<=", from_date),
            "to_date": (">=", to_date),
        },
        fields=["name", "total_leaves_allocated", "leaves_taken"],
        limit=1,
    )
    if allocation and balance < requested_days:
        frappe.throw(
            _("Insufficient {0} balance. Available: {1} day(s), requested: {2} day(s).").format(
                leave_type, balance, requested_days
            )
        )

    doc = frappe.get_doc(
        {
            "doctype": "Leave Application",
            "employee": emp.name,
            "leave_type": leave_type,
            "from_date": from_date,
            "to_date": to_date,
            "reason": reason,
            "half_day": 1 if half_day else 0,
            "half_day_date": half_day_date,
        }
    )
    doc.insert(ignore_permissions=True)
    doc.submit()
    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def team_leave_calendar():
    from bizaxl_hrms.bizaxl_hr.portal.leave import team_leave_calendar

    require_login()
    emp = get_session_employee(force=True)
    return team_leave_calendar(emp.name)


# ---------------------------------------------------------------------------
# Payroll
# ---------------------------------------------------------------------------


@frappe.whitelist()
def payslips(limit=12):
    from bizaxl_hrms.bizaxl_hr.portal.payroll import get_payslip_history

    require_login()
    emp = get_session_employee(force=True)
    return get_payslip_history(emp.name, limit=int(limit))


@frappe.whitelist()
def payslip_year_totals_data():
    from bizaxl_hrms.bizaxl_hr.portal.payroll import payslip_year_totals

    require_login()
    emp = get_session_employee(force=True)
    return payslip_year_totals(emp.name)


@frappe.whitelist()
def statutory_illustration():
    """Illustrative PF/ESI/TDS figures used by the Payslips page calculator."""
    from bizaxl_hrms.bizaxl_hr.portal.payroll import compute_statutories

    require_login()
    args = frappe.form_dict
    gross = float(args.get("gross") or 0)
    basic = float(args.get("basic") or 0)
    return compute_statutories(gross, basic)


@frappe.whitelist()
def payroll_preflight_check():
    from bizaxl_hrms.bizaxl_hr.portal.payroll import pre_payroll_validation

    require_login()
    if not is_payroll():
        frappe.throw(_("Not allowed"), frappe.PermissionError)
    return pre_payroll_validation()


# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------


@frappe.whitelist()
def performance_data():
    from bizaxl_hrms.bizaxl_hr.portal.performance import (
        get_appraisals,
        get_feedback,
        skill_gap_analysis,
        okr_summary,
    )

    require_login()
    emp = get_session_employee(force=True)
    return {
        "appraisals": get_appraisals(emp.name),
        "feedback": get_feedback(emp.name),
        "skill_gaps": skill_gap_analysis(emp.name),
        "okr": okr_summary(emp.name),
    }


# ---------------------------------------------------------------------------
# Recruitment
# ---------------------------------------------------------------------------


@frappe.whitelist()
def job_openings():
    from bizaxl_hrms.bizaxl_hr.portal.recruitment import get_job_openings

    require_login()
    return get_job_openings()


@frappe.whitelist()
def active_job_applicants():
    from bizaxl_hrms.bizaxl_hr.portal.recruitment import get_active_job_applicants

    require_login()
    if not is_hr():
        frappe.throw(_("Not allowed"), frappe.PermissionError)
    return get_active_job_applicants()


@frappe.whitelist()
def hiring_pipeline():
    from bizaxl_hrms.bizaxl_hr.portal.recruitment import hiring_pipeline_summary

    require_login()
    if not is_hr():
        frappe.throw(_("Not allowed"), frappe.PermissionError)
    return hiring_pipeline_summary()


@frappe.whitelist()
def upcoming_interviews(days=14):
    from bizaxl_hrms.bizaxl_hr.portal.recruitment import get_upcoming_interviews

    require_login()
    return get_upcoming_interviews(days_ahead=int(days))


# ---------------------------------------------------------------------------
# Help Desk & tickets
# ---------------------------------------------------------------------------


@frappe.whitelist()
def ticket_categories():
    cats = frappe.get_all("Help Desk Category", fields=["name", "category_name"], order_by="name")
    return cats


@frappe.whitelist()
def create_ticket(subject, description, category=None, priority="Medium"):
    from bizaxl_hrms.bizaxl_hr.portal.tickets import create_ticket as _create

    require_login()
    name = _create(subject, description, category, priority)
    return {"name": name}


@frappe.whitelist()
def my_tickets():
    from bizaxl_hrms.bizaxl_hr.portal.tickets import get_tickets

    require_login()
    return get_tickets(raised_by=frappe.session.user)


@frappe.whitelist()
def ticket_detail(name):
    from bizaxl_hrms.bizaxl_hr.portal.tickets import get_ticket, sla_status

    require_login()
    t = get_ticket(name)
    if not t:
        frappe.throw(_("Ticket not found"))
    return {"ticket": t, "sla": sla_status(name)}


@frappe.whitelist()
def update_ticket_status(name, status, remark=None):
    from bizaxl_hrms.bizaxl_hr.portal.tickets import update_ticket_status as _update

    require_login()
    return _update(name, status, remark)


# ---------------------------------------------------------------------------
# Rewards
# ---------------------------------------------------------------------------


@frappe.whitelist()
def rewards_leaderboard(limit=20):
    from bizaxl_hrms.bizaxl_hr.portal.rewards import leaderboard

    require_login()
    return leaderboard(int(limit))


@frappe.whitelist()
def rewards_feed(limit=50):
    from bizaxl_hrms.bizaxl_hr.portal.rewards import recognition_feed

    require_login()
    return recognition_feed(int(limit))


@frappe.whitelist()
def my_rewards():
    from bizaxl_hrms.bizaxl_hr.portal.rewards import my_points

    require_login()
    emp = get_session_employee(force=True)
    return my_points(emp.name)


@frappe.whitelist()
def give_recognition(recipient, title, rec_type="Appreciation", points=None, message=None):
    from bizaxl_hrms.bizaxl_hr.portal.rewards import give_recognition as _give

    require_login()
    name = _give(recipient, title, rec_type, points=points, message=message)
    return {"name": name}


# ---------------------------------------------------------------------------
# Wellness
# ---------------------------------------------------------------------------


@frappe.whitelist()
def wellness_programs():
    from bizaxl_hrms.bizaxl_hr.portal.wellness import get_active_programs

    require_login()
    return get_active_programs()


@frappe.whitelist()
def register_wellness(program):
    from bizaxl_hrms.bizaxl_hr.portal.wellness import register_for_program

    require_login()
    emp = get_session_employee(force=True)
    return {"name": register_for_program(program, employee=emp.name)}


@frappe.whitelist()
def submit_counselling(reason, category="General"):
    from bizaxl_hrms.bizaxl_hr.portal.wellness import submit_counselling_request

    require_login()
    emp = get_session_employee(force=True)
    return {"name": submit_counselling_request(reason, category=category, employee=emp.name)}


@frappe.whitelist()
def my_wellness():
    from bizaxl_hrms.bizaxl_hr.portal.wellness import my_participations

    require_login()
    emp = get_session_employee(force=True)
    return my_participations(emp.name)


# ---------------------------------------------------------------------------
# Field operations
# ---------------------------------------------------------------------------


@frappe.whitelist()
def my_field_visits():
    from bizaxl_hrms.bizaxl_hr.portal.field import get_my_field_visits

    require_login()
    emp = get_session_employee(force=True)
    return get_my_field_visits(emp.name)


@frappe.whitelist()
def field_visit_locations():
    from bizaxl_hrms.bizaxl_hr.portal.field import list_visit_locations

    require_login()
    return list_visit_locations()


@frappe.whitelist()
def schedule_field_visit(client=None, purpose=None, visit_location=None):
    from bizaxl_hrms.bizaxl_hr.portal.field import schedule_visit

    require_login()
    emp = get_session_employee(force=True)
    return {"name": schedule_visit(emp.name, client=client, purpose=purpose, visit_location=visit_location)}


@frappe.whitelist()
def field_check_in(name, lat, lng):
    from bizaxl_hrms.bizaxl_hr.portal.field import check_in_visit

    require_login()
    return check_in_visit(name, lat, lng)


@frappe.whitelist()
def field_check_out(name, lat, lng, notes=None):
    from bizaxl_hrms.bizaxl_hr.portal.field import check_out_visit

    require_login()
    return check_out_visit(name, lat, lng, notes)


@frappe.whitelist()
def field_complete(name, notes=None):
    from bizaxl_hrms.bizaxl_hr.portal.field import complete_visit

    require_login()
    return complete_visit(name, notes)


@frappe.whitelist()
def visit_route(name):
    from bizaxl_hrms.bizaxl_hr.portal.field import route_coverage

    require_login()
    return route_coverage(name)


# ---------------------------------------------------------------------------
# AI assistant
# ---------------------------------------------------------------------------


@frappe.whitelist()
def ai_chat(message):
    from bizaxl_hrms.bizaxl_hr.portal.ai import chat

    require_login()
    return chat(message)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------


@frappe.whitelist()
def notification_feed(limit=40, only_unread=0):
    from bizaxl_hrms.bizaxl_hr.portal.notifications import get_feed

    require_login()
    return get_feed(frappe.session.user, limit=int(limit), only_unread=int(only_unread))


@frappe.whitelist()
def notification_unread_count():
    from bizaxl_hrms.bizaxl_hr.portal.notifications import unread_count

    require_login()
    return {"count": unread_count(frappe.session.user)}


@frappe.whitelist()
def mark_notifications_read():
    from bizaxl_hrms.bizaxl_hr.portal.notifications import mark_all_read

    require_login()
    return mark_all_read(frappe.session.user)


# ---------------------------------------------------------------------------
# Onboarding / Offboarding
# ---------------------------------------------------------------------------


@frappe.whitelist()
def my_onboarding():
    require_login()
    emp = get_session_employee()
    if not emp:
        return {"onboarding": []}
    rows = frappe.get_all(
        "Employee Onboarding",
        filters={"employee": emp.name},
        fields=["name", "start_date", "status", "employee_name", "template", "progress"],
        order_by="start_date desc",
    )
    return {"onboarding": rows}


@frappe.whitelist()
def my_offboarding():
    require_login()
    emp = get_session_employee()
    if not emp:
        return {"offboarding": []}
    rows = frappe.get_all(
        "Employee Offboarding",
        filters={"employee": emp.name},
        fields=["name", "status", "employee_name", "resignation_date", "last_working_day", "exit_interview_date"],
        order_by="resignation_date desc",
    )
    return {"offboarding": rows}


@frappe.whitelist()
def my_ffs_status():
    require_login()
    emp = get_session_employee()
    if not emp:
        return {"ffs": []}
    rows = frappe.get_all(
        "Full and Final Settlement",
        filters={"employee": emp.name},
        fields=["name", "status", "net_payable", "date_of_joining", "last_working_day"],
        order_by="creation desc",
    )
    return {"ffs": rows}


@frappe.whitelist()
def my_team():
    require_login()
    emp = get_session_employee(force=True)
    return get_direct_reports(emp.name)


@frappe.whitelist()
def announcements(limit=10):
    require_login()
    if not frappe.db.exists("DocType", "Announcement"):
        return []
    return frappe.get_all(
        "Announcement",
        filters={"published": 1},
        fields=["name", "title", "announcement_type", "message", "announcement_date", "author", "pinned", "department"],
        order_by="pinned desc, announcement_date desc",
        limit_page_length=int(limit),
    )


@frappe.whitelist()
def employee_profile():
    require_login()
    emp = get_session_employee(force=True)
    fields = [
        "name", "employee_name", "date_of_joining", "department", "designation", "reports_to",
        "company", "employment_type", "email", "company_email", "personal_email", "mobile_number",
        "current_address", "qualification", "marital_status", "blood_group", "status",
    ]
    data = {f: emp.get(f) for f in fields}
    reports_to_name = data.get("reports_to")
    if reports_to_name:
        data["reports_to_name"] = frappe.get_value("Employee", reports_to_name, "employee_name")
    return data


# ---------------------------------------------------------------------------
# Directory
# ---------------------------------------------------------------------------

DIRECTORY_SENSITIVE = ("bank_name", "bank_acct_no", "salary_", "date_of_birth", "passport_number", "pan_number", "aadhar_number")


@frappe.whitelist()
def directory(query=None, department=None, designation=None):
    require_login()
    filters = {"status": "Active"}
    if query:
        filters["employee_name"] = ("like", "%" + query + "%")
    if department:
        filters["department"] = department
    if designation:
        filters["designation"] = designation
    return frappe.get_all(
        "Employee",
        filters=filters,
        fields=["name", "employee_name", "department", "designation", "mobile_number", "personal_email", "company_email", "reports_to", "date_of_joining"],
        order_by="employee_name asc",
        limit_page_length=100,
    )