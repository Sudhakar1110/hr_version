# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import today

from bizaxl_hrms.bizaxl_hr.portal.attendance import checkin_overview, last_30_days_summary
from bizaxl_hrms.bizaxl_hr.portal.leave import get_leave_balances
from bizaxl_hrms.bizaxl_hr.portal.payroll import get_payslip_history
from bizaxl_hrms.bizaxl_hr.portal.utils import get_session_employee


def chat(message):
    """Rule-based HR assistant. Returns (answer_text, intent)."""
    message = (message or "").strip().lower()
    intent = guess_intent(message)

    employee = get_session_employee(force=False)
    handlers = {
        "leave_balance": lambda: leave_balance_answer(employee),
        "attendance": lambda: attendance_answer(employee),
        "payslip": lambda: payslip_answer(employee),
        "holiday": lambda: holiday_answer(),
        "policy": lambda: policy_answer(message),
        "greeting": lambda: "Hello! I am the HR assistant. Ask me about leave balance, attendance, payslips, holidays or policies.",
        "grievance": lambda: "You can raise a grievance on the Help & Grievance page. It is kept confidential and assigned to an HR manager.",
        "help": lambda: "I can help with: leave balance, attendance summary, last payslip, upcoming holidays, and common policies.",
        "faq": lambda: faq_answer(message),
    }
    handler = handlers.get(intent, lambda: fallback_answer(message))
    try:
        answer = handler()
    except Exception:
        answer = "Sorry, I could not fetch that right now. Try again in a moment."
    log(message, answer, intent)
    return {"answer": answer, "intent": intent}


def guess_intent(message):
    if any(w in message for w in ["hi", "hello", "hey", "good morning", "good afternoon"]):
        return "greeting"
    if any(w in message for w in ["balance", "leave left", "leave available", "how many leaves"]):
        return "leave_balance"
    if any(w in message for w in ["attendance", "check in", "check-in", "absent", "present today", "punch"]):
        return "attendance"
    if any(w in message for w in ["payslip", "salary slip", "pay", "salary breakdown", "net pay"]):
        return "payslip"
    if any(w in message for w in ["holiday", "holidays", "festival", "off day"]):
        return "holiday"
    if any(w in message for w in ["policy", "policies", "code of conduct", "hr policy"]):
        return "policy"
    if any(w in message for w in ["grievance", "complaint", "harassment", "report someone"]):
        return "grievance"
    if any(w in message for w in ["help", "what can you", "commands", "options"]):
        return "help"
    return "faq"


def leave_balance_answer(employee):
    if not employee:
        return "Please log in with an employee-linked account to see your leave balance."
    rows = get_leave_balances(employee.name)
    if not rows:
        return "You currently have no leave allocations."
    return "Leave balance: " + ", ".join("{} ({} days)".format(r["leave_type"], r["balance"]) for r in rows)


def attendance_answer(employee):
    if not employee:
        return "Please log in with an employee-linked account to see your attendance."
    ov = checkin_overview(employee.name)
    summary = last_30_days_summary(employee.name)
    return "Today: {}. Last 30 days: {:.0f}% attendance ({} present, {} absent, {} on leave).".format(
        ov["status"], summary["percentage"], summary["present"], summary["absent"], summary["leave"]
    )


def payslip_answer(employee):
    if not employee:
        return "Please log in with an employee-linked account to see your payslips."
    rows = get_payslip_history(employee.name, limit=1)
    if not rows:
        return "No payslips found yet. Check back after the payroll cycle."
    r = rows[0]
    return "Your latest payslip {} ({} to {}) shows gross {} and net {}.".format(
        r["name"], r["start_date"], r["end_date"], r["gross_pay"], r["net_pay"]
    )


def holiday_answer():
    import frappe.utils.data as d

    today_dt = d.today()
    if not frappe.db.exists("DocType", "Holiday List") or not frappe.db.exists("DocType", "Holiday"):
        return "No holiday list is configured yet."
    hd = frappe.get_all(
        "Holiday",
        filters={"holiday_date": (">=", today_dt)},
        fields=["holiday_date", "description"],
        order_by="holiday_date asc",
        limit_page_length=3,
    )
    if not hd:
        return "No upcoming holidays found in the default holiday list."
    return "Upcoming holidays: " + "; ".join("{} ({})".format(h["holiday_date"], h["description"]) for h in hd)


def policy_answer(message):
    for keyword, summary in policy_bank().items():
        if keyword in message:
            return summary
    return "Let me connect you with HR for that policy question."


def faq_answer(message):
    if not frappe.db.exists("DocType", "FAQ"):
        return "I could not find an answer. Resources are available on the Help & Grievance page."
    matches = frappe.get_all(
        "FAQ",
        filters={},
        fields=["name", "question", "answer"],
        limit_page_length=200,
    )
    best = None
    best_score = 0
    words = set(_words(message))
    for m in matches:
        q = _words(m["question"].lower())
        score = len(set(q) & words)
        if score > best_score:
            best_score = score
            best = m
    if best and best_score > 0:
        return "{} (from '{}')".format(best["answer"], best["question"])
    return "I could not find an exact match. Please search the Knowledge Base or raise a ticket on Help & Grievance."


def policy_bank():
    return {
        "leave": "Paid leave is governed by approved leave policies. Use Leave & Attendance to apply; manager approval is required.",
        "work from home": "Work-from-home requests are routed through your manager. Choose the option in Leave Application.",
        "attendance": "Mark your check-in/out from the Attendance widget. Late entries are tracked and reported.",
        "hr policy": "All HR policies are available in the Knowledge Base / Policy manual under Help.",
    }


def fallback_answer(message):
    return "I understood your message but I am still learning. Try asking about leave, attendance, payslip, holidays or a specific policy."


def _words(text):
    return [w for w in text.replace(",", " ").replace(".", " ").split() if len(w) > 1]


def log(message, answer, intent):
    if frappe.session.user == "Guest":
        return
    if not frappe.db.exists("DocType", "AI Assistant Log"):
        return
    doc = frappe.get_doc(
        {
            "doctype": "AI Assistant Log",
            "user": frappe.session.user,
            "query": message,
            "response": answer,
            "intent": intent,
        }
    )
    doc.insert(ignore_permissions=True)
    frappe.db.commit()