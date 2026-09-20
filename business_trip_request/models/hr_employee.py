from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

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
        "than their eligibility.",
    )
