{
    "name": "Business Trip / Assignment Request - Portal",
    "version": "17.0.1.0.0",
    "category": "Human Resources",
    "summary": "Employee self-service portal for Business Trip / Assignment Requests",
    "description": """
Adds an Odoo Website/Portal front-end (/my/business-trips) so employees can
submit and track their own Business Trip / Assignment Requests and trip
reports with a portal login, without needing an internal user seat.

Approvals, HR allowance calculation, and Finance settlement remain in the
internal backend provided by the business_trip_request module.
""",
    "author": "naizu19",
    "license": "LGPL-3",
    "depends": ["portal", "business_trip_request"],
    "data": [
        "security/portal_security.xml",
        "security/ir.model.access.csv",
        "views/portal_templates.xml",
    ],
    "installable": True,
    "application": False,
}
