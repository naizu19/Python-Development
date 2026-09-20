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
* Sequential approval workflow: Direct Manager -> Department Manager -> CEO
* HR review and configurable allowance calculation
  (domestic / international / peak-period / senior management / transportation
  deduction / overnight 50% rule / international extra travel days)
* Cash advance request and control
* Post-trip report, report approval and HR/Finance settlement
* Frequent traveler flag and travel-class eligibility informational data
""",
    "author": "naizu19",
    "license": "LGPL-3",
    "depends": ["hr", "mail"],
    "data": [
        "security/business_trip_security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/allowance_rule_data.xml",
        "views/hr_employee_views.xml",
        "views/business_trip_allowance_rule_views.xml",
        "views/business_trip_peak_period_views.xml",
        "views/business_trip_request_views.xml",
        "views/res_company_views.xml",
        "views/business_trip_menus.xml",
        "wizard/business_trip_reason_wizard_views.xml",
    ],
    "installable": True,
    "application": True,
}
