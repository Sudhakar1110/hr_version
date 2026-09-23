# -*- coding: utf-8 -*-

import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate, nowdate, today

# ---------------------------------------------------------------------------
# Statutory compliance
# ---------------------------------------------------------------------------


def company_dates():
    """Return default company + fiscal year from Portal Settings (with fallbacks)."""
    company = None
    fy = None
    try:
        company = frappe.db.get_single_value("Portal Settings", "company")
        fy = frappe.db.get_single_value("Portal Settings", "fiscal_year")
    except Exception:
        pass
    if not company:
        company = frappe.db.get_single_value("Global Defaults", "default_company")
    if not fy:
        fy = frappe.db.get_value("Fiscal Year", {"is_year_start_date": ("<=", today())}, "name", order_by="year_start_date desc")
    return company, fy


def get_pf_rates():
    """Indian EPF rules (defaults, overridable in Portal Settings)."""
    return {"employee_rate": 12.0, "employer_rate": 12.0, "ceiling": 15000.0}


def get_esi_rates():
    """Indian ESI rules (defaults)."""
    return {"employee_rate": 0.75, "employer_rate": 3.25, "wage_ceiling": 21000.0}


def get_tds_rates():
    """Simplified Indian income-tax new-regime annual slabs (FY 2025-26)."""
    slabs = [
        (0, 400000, 0.0),
        (400000, 800000, 5.0),
        (800000, 1200000, 10.0),
        (1200000, 1600000, 15.0),
        (1600000, 2000000, 20.0),
        (2000000, 2400000, 25.0),
        (2400000, float("inf"), 30.0),
    ]
    return slabs


def compute_statutories(monthly_gross, basic):
    """Compute monthly PF, ESI, TDS, PT, LWF for an employee."""
    basic = flt(basic) or flt(monthly_gross) * 0.4
    pf_rates = get_pf_rates()
    pf = min(flt(basic) * pf_rates["employee_rate"] / 100, flt(pf_rates["ceiling"]) * pf_rates["employee_rate"] / 100)

    esi_rates = get_esi_rates()
    esi = flt(monthly_gross) * esi_rates["employee_rate"] / 100 if flt(monthly_gross) <= flt(esi_rates["wage_ceiling"]) else 0

    # PT - default state slabs (e.g. Karnataka style: sample)
    annual_taxable = flt(monthly_gross) * 12
    pt = professional_tax_for_annual(annual_taxable)

    lwf = labour_welfare_fund_for_annual(annual_taxable)

    annual_net = max(annual_taxable - 75000, 0)  # standard deduction in new regime
    tds_annual = tds_on_taxable(annual_net)
    tds = tds_annual / 12.0

    return {
        "pf": round(pf, 2),
        "esi": round(esi, 2),
        "tds": round(tds, 2),
        "professional_tax": round(pt, 2),
        "lwf": round(lwf, 2),
    }


def professional_tax_for_annual(annual):
    """Example PT slabs (Karnataka)."""
    monthly = annual / 12.0
    if monthly <= 15000:
        return 0
    return 200.0


def labour_welfare_fund_for_annual(annual):
    monthly = annual / 12.0
    if monthly <= 10000:
        return 0
    return 30.0


def tds_on_taxable(taxable):
    slabs = get_tds_rates()
    tax = 0.0
    prev = 0
    for low, high, rate in slabs:
        if taxable > low:
            chunk = min(taxable, high) - low
            if chunk > 0:
                tax += chunk * rate / 100
        else:
            break
    return tax


# ---------------------------------------------------------------------------
# Payroll preparation
# ---------------------------------------------------------------------------


def get_salary_structure_assignment(employee, on_date=None):
    on_date = on_date or today()
    return frappe.get_all(
        "Salary Structure Assignment",
        filters={"employee": employee, "docstatus": 1, "from_date": ("<=", on_date)},
        fields=["name", "salary_structure", "from_date", "base"],
        order_by="from_date desc",
        limit=1,
    )


def get_active_payroll_employees(company=None):
    company = company or company_dates()[0]
    return frappe.get_all(
        "Employee",
        filters={"status": "Active"},
        fields=["name", "employee_name", "user_id", "department", "designation"],
        order_by="employee_name asc",
    )


def pre_payroll_validation(company=None, date=None):
    """Return issues that would block a clean payroll run (pre-payroll checks)."""
    company = company or company_dates()[0]
    date = getdate(date or today())
    employees = get_active_payroll_employees(company)
    issues = []
    for emp in employees:
        emp_name = emp["name"]
        row = {"employee": emp_name, "employee_name": emp["employee_name"], "issues": []}
        # 1. Bank details
        bank_name = frappe.get_value("Employee", emp_name, "bank_name")
        bank_acct = frappe.get_value("Employee", emp_name, "bank_acct_no")
        if not bank_name or not bank_acct:
            row["issues"].append(_("Bank details missing"))
        # 2. Salary structure assigned
        ssa = get_salary_structure_assignment(emp_name, date)
        if not ssa:
            row["issues"].append(_("No Salary Structure Assignment on {0}").format(date))
        # 3. Attendance for the month
        month_start = getdate(date).replace(day=1)
        attn = frappe.db.count(
            "Attendance",
            {"employee": emp_name, "attendance_date": ("between", [month_start, date]), "status": ("in", ("Present", "On Leave", "Half Day"))},
        )
        working_days = max((date - month_start).days + 1, 1)
        if attn == 0:
            row["issues"].append(_("No attendance recorded this month"))
        if row["issues"]:
            issues.append(row)
    return {
        "as_on": str(date),
        "employee_count": len(employees),
        "issues_flagged": len(issues),
        "issues": issues,
    }


def get_payslip(employee, month):
    """Most recent Salary Slip in the month for an employee."""
    return frappe.get_all(
        "Salary Slip",
        filters={"employee": employee, "start_date": ("like", month + "%")},
        fields=["name", "start_date", "end_date", "gross_pay", "net_pay", "total_deduction", "posting_date"],
        order_by="posting_date desc",
        limit=1,
    )


def get_payslip_history(employee, limit=12):
    return frappe.get_all(
        "Salary Slip",
        filters={"employee": employee},
        fields=["name", "start_date", "end_date", "gross_pay", "net_pay", "total_deduction", "posting_date"],
        order_by="posting_date desc",
        limit_page_length=limit,
    )


def payslip_year_totals(employee, fy_start=1):
    rows = get_payslip_history(employee, limit=24)
    gross = sum((r.gross_pay or 0) for r in rows)
    net = sum((r.net_pay or 0) for r in rows)
    tax = 0
    for r in rows:
        slip = frappe.get_doc("Salary Slip", r.name)
        for d in slip.deductions or []:
            if "tax" in (d.salary_component or "").lower() or "TDS" in (d.salary_component or ""):
                tax += d.amount or 0
    return {"ytd_gross": gross, "ytd_net": net, "ytd_tax": tax}


def compute_arrears(employee, from_date, to_date):
    """Estimate arrears owed due to a backdated salary revision.

    Uses the change in `base` across consecutive Salary Structure Assignments.
    """
    rows = frappe.get_all(
        "Salary Structure Assignment",
        filters={"employee": employee, "docstatus": 1, "from_date": ("<=", to_date)},
        fields=["name", "salary_structure", "from_date", "base"],
        order_by="from_date asc",
    )
    if len(rows) < 2:
        return {"arrears": 0, "months": 0, "previous_base": 0, "new_base": 0}
    new = rows[-1]
    prev = rows[-2]
    months = (getdate(new["from_date"]).year - getdate(prev["from_date"]).year) * 12 + (
        getdate(new["from_date"]).month - getdate(prev["from_date"]).month
    )
    arrears = max(flt(new["base"]) - flt(prev["base"]), 0) * max(months, 1)
    return {"arrears": round(arrears, 2), "months": months, "previous_base": flt(prev["base"]), "new_base": flt(new["base"])}


# ---------------------------------------------------------------------------
# Full & Final settlement + vendor operations
# ---------------------------------------------------------------------------


def prepare_full_final(employee):
    """Create a Full and Final Settlement doc for an employee."""
    emp = frappe.get_doc("Employee", employee)
    docs = frappe.get_all(
        "Full and Final Settlement",
        filters={"employee": employee},
        fields=["name"],
        order_by="creation desc",
    )
    if docs:
        return frappe.get_doc("Full and Final Settlement", docs[0].name)
    doc = frappe.get_doc(
        {
            "doctype": "Full and Final Settlement",
            "employee": employee,
            "date_of_joining": emp.date_of_joining,
            "last_working_day": None,
            "status": "Draft",
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def summary_of_vendor_payouts():
    rows = frappe.get_all(
        "Vendor Payout",
        fields=["vendor", "vendor_name", "amount", "paid_amount", "status", "posting_date"],
        order_by="posting_date desc",
        limit_page_length=100,
    )
    totals = {"pending": 0, "paid": 0, "processing": 0}
    for r in rows:
        if r.status == "Paid":
            totals["paid"] += flt(r.amount)
        elif r.status == "Processing":
            totals["processing"] += flt(r.amount)
        else:
            totals["pending"] += flt(r.amount) - flt(r.paid_amount)
    return {"payouts": rows, "totals": totals}