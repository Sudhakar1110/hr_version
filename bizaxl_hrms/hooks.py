app_name = "bizaxl_hrms"
app_title = "Bizaxl HRMS Portal"
app_publisher = "Bizaxl HRMS Contributors"
app_description = "A complete, role-based HR self-service portal built for Frappe v15 and ERPNext v15. Covers the Bizaxl HR portal feature set: Dashboard, Attendance, Leave, Shift, Expense, Payroll, Performance, Recruitment, Employee Lifecycle (Onboarding/Offboarding), Tasks, Training, Documents, Help Desk, Announcements, Holiday Calendar, Directory, Reports, Meetings, Rewards & Recognition, Wellness, Notifications, AI Assistant, Settings and field/location tracking."
app_license = "MIT"
app_email = "sudhakar+hrms@example.com"

# Apps installed by default when you setup this app (compatible with bench v15)
required_apps = ["frappe", "erpnext", "hrms"]

# Includes in <head> and <body>
app_include_css = "/assets/bizaxl_hrms/css/bizaxl_portal.css"
app_include_js = "/assets/bizaxl_hrms/js/bizaxl_portal.js"
web_include_css = "/assets/bizaxl_hrms/css/bizaxl_portal.css"
web_include_js = "/assets/bizaxl_hrms/js/bizaxl_portal.js"

# Fixtures exported with `bench export-fixtures`
fixtures = []

# Before / after app install
before_install = "bizaxl_hrms.setup.before_install"
after_install = "bizaxl_hrms.setup.after_install"

# Website route rules
website_route_rules = []

# Scheduler events
scheduler_events = {
    "daily": [
        "bizaxl_hrms.bizaxl_hr.scheduler.daily_digest",
        "bizaxl_hrms.bizaxl_hr.scheduler.sla_escalations",
    ],
    "hourly": [
        "bizaxl_hrms.bizaxl_hr.scheduler.compliance_reminders",
    ],
}

# Notification configuration for Frappe notifications
notification_config = "bizaxl_hrms.hooks.notification_config"

# User data protection - export personal data
user_data_fields = [
    {
        "doctype": "{doctype}",
        "filter_by": "{filter_by}",
        "redact_fields": [],
        "partial": False,
    }
]

# Permissions to export
permissions = [
    {"role": "System Manager", "type": "all"},
    {"role": "HR Manager", "type": "all"},
]


def notification_config():
    return {
        "for_doctype": "Help Desk Ticket",
        "condition": "doc.status not in ('Resolved', 'Closed')",
        "message": "New ticket {doc.subject} requires attention.",
        "subject": "{doc.subject}",
    }


# App doc link
doc_events = {}


# Custom Fields / property setters applied on install
def get_standard_fixtures():
    return []