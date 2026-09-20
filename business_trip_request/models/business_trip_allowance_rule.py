from odoo import fields, models


class BusinessTripAllowanceRule(models.Model):
    _name = "business.trip.allowance.rule"
    _description = "Business Trip Allowance Rule"
    _order = "trip_type, region, sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    trip_type = fields.Selection(
        [("domestic", "Domestic"), ("international", "International")],
        required=True,
    )
    region = fields.Selection(
        [
            ("arabic", "Arabic Countries"),
            ("asian", "Asian Countries"),
            ("europe_japan", "Europe / Japan"),
        ],
        string="International Region",
        help="Only applicable when Trip Type is International.",
    )
    percentage = fields.Float(
        string="Percentage of Monthly Basic Salary", required=True
    )
    min_amount = fields.Monetary(string="Minimum", currency_field="currency_id")
    max_amount = fields.Monetary(string="Maximum", currency_field="currency_id")
    max_days = fields.Integer(
        string="Maximum Assignment Period (days/year)",
        help="Maximum annual assignment period eligible under this rule.",
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True
    )
