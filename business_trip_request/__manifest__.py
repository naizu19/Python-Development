{
    "name": "Business Trip / Assignment Request",
    "version": "17.0.1.0.0",
    "category": "Human Resources",
    "summary": "Business Trip / Assignment Request workflow, allowance calculation and settlement",
    "description": """
Business Trip / Assignment Request (Sanad Employee Portal)
============================================================

Implements the full business-assignment lifecycle:

* Employee request (auto-populated employee data, trip info, dates, services)
* Business rules: minimum distance, minimum advance notice, mandatory fields,
  maximum single assignment duration, overnight-stay rule
* Fully configurable, group-driven approval workflow: add/remove/reorder
  approval steps and assign any user group as approver, without code changes
* HR review and configurable allowance calculation
  (domestic / international / peak-period / senior management / transportation
  deduction / overnight allowance rule / international extra travel days) -
  every threshold and percentage is editable from Settings, nothing hardcoded
* Cash advance request and control
* Post-trip report, report approval and HR/Finance settlement
* Frequent traveler flag and travel-class eligibility informational data
* Destination City (free text) plus an optional State/Province dropdown
  filtered by country; peak-period cities configured as a simple list in
  Settings
* Employee self-service Website/Portal pages (/my/business-trips) to submit,
  track and report on requests without needing an internal user seat
""",
    "author": "naizu19",
    "license": "LGPL-3",
    "depends": ["hr", "mail", "portal"],
    "data": [
        "security/business_trip_security.xml",
        "security/portal_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/allowance_rule_data.xml",
        "data/approval_step_data.xml",
        "data/peak_period_data.xml",
        "views/hr_employee_views.xml",
        "views/business_trip_allowance_rule_views.xml",
        "views/business_trip_peak_period_views.xml",
        "views/business_trip_approval_step_views.xml",
        "views/business_trip_request_views.xml",
        "views/res_config_settings_views.xml",
        "views/business_trip_menus.xml",
        "views/portal_templates.xml",
        "wizard/business_trip_reason_wizard_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "business_trip_request/static/src/css/business_trip_portal.css",
        ],
    },
    "installable": True,
    "application": True,
}
