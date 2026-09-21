from datetime import date

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    domestic_days_ytd = fields.Integer(
        string="Domestic Travel Days (This Year)",
        compute="_compute_travel_days_ytd",
        help="Total domestic business trip days this calendar year, across "
        "requests that are not draft/rejected/returned.",
    )
    international_days_ytd = fields.Integer(
        string="International Travel Days (This Year)",
        compute="_compute_travel_days_ytd",
        help="Total international business trip days this calendar year, "
        "across requests that are not draft/rejected/returned.",
    )

    def _compute_travel_days_ytd(self):
        year_start = date(fields.Date.context_today(self).year, 1, 1)
        for employee in self:
            trips = self.env["business.trip.request"].search([
                ("employee_id", "=", employee.id),
                ("date_start", ">=", year_start),
                ("state", "not in", ["draft", "rejected", "returned"]),
            ])
            employee.domestic_days_ytd = sum(
                trips.filtered(lambda t: t.trip_type == "domestic").mapped("total_days")
            )
            employee.international_days_ytd = sum(
                trips.filtered(lambda t: t.trip_type == "international").mapped("total_days")
            )

    is_senior_management = fields.Boolean(
        string="Senior Management (President/VP/Business Advisor)",
        help="Employees whose work is not operational/executive in nature. "
        "Grants the +20% senior management assignment allowance adjustment.",
    )
    frequent_traveler = fields.Boolean(
        string="Frequent Traveler",
        help="Employee excluded from the standard assignment allowance system "
        "because frequent travel is part of their job (e.g. sales, continuous "
        "regional travel, or employees exceeding 18 international / 45 "
        "domestic travel days). Subject to a fixed/permanent travel allowance "
        "instead of the standard per-request assignment allowance.",
    )
    travel_class_id = fields.Selection(
        [
            ("economy", "Economy"),
            ("business", "Business"),
            ("first", "First Class"),
        ],
        string="Travel Class Eligibility",
        default="economy",
        help="Flight ticket class the employee is entitled to according to "
        "their approved job level. Employees cannot select a higher class "
        "than their eligibility. Auto-suggested when Senior Management is "
        "ticked (see below) - HR can still override it manually.",
    )

    @api.onchange("is_senior_management")
    def _onchange_is_senior_management_travel_class(self):
        for employee in self:
            if not employee.is_senior_management:
                employee.travel_class_id = "economy"
                continue
            ceo_user = employee.company_id.business_trip_ceo_user_id
            if ceo_user and employee.user_id == ceo_user:
                employee.travel_class_id = "first"
            else:
                employee.travel_class_id = "business"
