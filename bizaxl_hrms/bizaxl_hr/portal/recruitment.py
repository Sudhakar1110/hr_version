# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today


PIPELINE_STAGES = ["Screening", "Phone Screen", "Interview 1", "Interview 2", "Offer", "Hired", "Rejected"]


def get_job_openings():
    if not frappe.db.exists("DocType", "Job Opening"):
        return []
    return frappe.get_all(
        "Job Opening",
        filters={"status": "Open"},
        fields=["name", "job_title", "description", "department", "designation", "posted", "closed", "publish"],
        order_by="posted desc",
        limit_page_length=50,
    )


def get_job_applicants(limit=100):
    if not frappe.db.exists("DocType", "Job Applicant"):
        return []
    return frappe.get_all(
        "Job Applicant",
        fields=["name", "applicant_name", "email_id", "phone_number", "status", "job_title", "job_opening"],
        limit_page_length=limit,
    )


def get_active_job_applicants():
    if not frappe.db.exists("DocType", "Job Applicant"):
        return []
    return frappe.get_all(
        "Job Applicant",
        filters={"status": ("in", ["Open", "Replied", "Screened", "Schedule Interview"])},
        fields=["name", "applicant_name", "email_id", "status", "job_title", "designation", "created"],
        order_by="created desc",
        limit_page_length=200,
    )


def hiring_pipeline_summary():
    """Counts of applicants per status = the hiring funnel."""
    if not frappe.db.exists("DocType", "Job Applicant"):
        return {"total": 0, "stages": [], "source_breakdown": {}}
    rows = frappe.get_all(
        "Job Applicant",
        fields=["status", "source"],
        limit_page_length=100000,
    )
    total = len(rows)
    from collections import Counter

    by_status = Counter(r.status or "Open" for r in rows)
    by_source = Counter(r.source or "Unknown" for r in rows)
    stages = [{"stage": s, "count": by_status.get(s, 0)} for s in PIPELINE_STAGES]
    return {"total": total, "stages": stages, "source_breakdown": dict(by_source)}


def get_interviews(limit=100):
    if not frappe.db.exists("DocType", "Interview"):
        return []
    return frappe.get_all(
        "Interview",
        fields=["name", "applicant_name", "job_applicant", "scheduled_on", "interview_round", "status", "interview_venue", "custom_location", "interviewers"],
        order_by="scheduled_on desc",
        limit_page_length=limit,
    )


def get_upcoming_interviews(days_ahead=14, limit=50):
    if not frappe.db.exists("DocType", "Interview"):
        return []
    today_dt = getdate(today())
    end = add_days(today_dt, days_ahead)
    return frappe.get_all(
        "Interview",
        filters={"scheduled_on": ("between", [str(today_dt) + " 00:00:00", str(end) + " 23:59:59"])},
        fields=["name", "applicant_name", "job_applicant", "scheduled_on", "interview_round", "status", "interview_venue", "interviewers"],
        order_by="scheduled_on asc",
        limit_page_length=limit,
    )


def applicant_details(job_applicant):
    if not frappe.db.exists("DocType", "Job Applicant"):
        return None
    doc = frappe.get_doc("Job Applicant", job_applicant)
    d = {
        "name": doc.name,
        "applicant_name": doc.applicant_name,
        "email_id": doc.email_id,
        "phone_number": doc.phone_number,
        "status": doc.status,
        "job_title": doc.job_title,
        "designation": doc.designation,
        "source": doc.source,
        "cover_letter": doc.cover_letter,
    }
    interviews = frappe.get_all(
        "Interview",
        filters={"job_applicant": job_applicant},
        fields=["name", "scheduled_on", "interview_round", "status", "feedback"],
        order_by="scheduled_on desc",
    )
    d["interviews"] = interviews
    return d


def add_comment(job_applicant, comment_text):
    doc = frappe.get_doc("Job Applicant", job_applicant)
    doc.add_comment("Comment", comment_text)
    return True