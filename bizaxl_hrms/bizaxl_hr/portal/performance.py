# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import flt, today


def get_appraisals(employee, limit=10):
    """Appraisal records for an employee (standard HR doctype)."""
    filters = {"employee": employee}
    if not frappe.db.exists("DocType", "Appraisal"):
        return []
    return frappe.get_all(
        "Appraisal",
        filters=filters,
        fields=["name", "appraisal_cycle", "start_date", "end_date", "total_score", "status", "due_date"],
        order_by="start_date desc",
        limit_page_length=limit,
    )


def get_feedback(employee, limit=20):
    """Performance feedback about the employee."""
    if not frappe.db.exists("DocType", "Employee Performance Feedback"):
        return []
    return frappe.get_all(
        "Employee Performance Feedback",
        filters={"employee": employee},
        fields=["name", "employee", "remarks", "reviewer", "performance", "date"],
        order_by="date desc",
        limit_page_length=limit,
    )


def get_goals(employee, limit=20):
    """Goals linked to the employee (Frappe core Goal doctype, if available)."""
    if not frappe.db.exists("DocType", "Goal"):
        return []
    return frappe.get_all(
        "Goal",
        filters={"owner_employee": employee},
        fields=["name", "title", "progress", "date"],
        order_by="date desc",
        limit_page_length=limit,
    )


def skill_gap_analysis(employee):
    """Skill gap between current and expected skill levels."""
    if not frappe.db.exists("DocType", "Employee Skill Map"):
        return {"skills": [], "gaps": []}
    maps = frappe.get_all("Employee Skill Map", filters={"employee": employee}, fields=["name"])
    skills = []
    for m in maps:
        doc = frappe.get_doc("Employee Skill Map", m.name)
        for row in doc.employee_skills or []:
            duration = row.experience or 0  # years
            level = row.proficiency or 0
            skills.append({"skill": row.skill, "proficiency": level, "expected": duration, "gap": max(duration - level, 0) if isinstance(duration, (int, float)) else 0})
    gaps = sorted([s for s in skills if s.get("gap", 0) > 0], key=lambda x: x["gap"], reverse=True)
    return {"skills": skills, "gaps": gaps}


def okr_summary(employee, period=None):
    """High-level OKR / goal progress metric for the dashboard."""
    goals = get_goals(employee, limit=25)
    completed = [g for g in goals if (g.progress or 0) >= 100]
    return {
        "totalGoals": len(goals),
        "completedGoals": len(completed),
        "avgProgress": round(sum(flt(g.progress or 0) for g in goals) / max(len(goals), 1), 1),
    }


def recognition_summary(employee):
    """Awards / recognitions received by the employee."""
    if not frappe.db.exists("DocType", "Recognition"):
        return {"received": 0, "given": 0, "items": []}
    received = frappe.get_all(
        "Recognition",
        filters={"recognized_employee": employee},
        fields=["name", "badge_name", "recognition_type", "energy_points", "posting_date", "message"],
        order_by="posting_date desc",
        limit_page_length=20,
    )
    given = frappe.get_all(
        "Recognition",
        filters={"recognized_by": frappe.session.user},
        fields=["name", "badge_name", "recognition_type", "energy_points", "posting_date"],
        order_by="posting_date desc",
        limit_page_length=20,
    )
    return {
        "received": len(received),
        "given": len(given),
        "received_items": received,
        "given_items": given,
    }


def kpi_trend(employee, months=6):
    """Sample KPI trend for the dashboard (placeholder data hook)."""
    return {
        "months": months,
        "points": [0] * months,
        "labels": [],
    }