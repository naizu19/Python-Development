from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    business_trip_ceo_user_id = fields.Many2one(
        "res.users",
        string="CEO (Business Trip Final Approver)",
    )
    business_trip_short_domestic_rate = fields.Monetary(
        string="Short Domestic Trip Daily Rate (<300km)",
        currency_field="currency_id",
        default=150.0,
    )
    business_trip_min_advance_days = fields.Integer(
        string="Minimum Advance Notice (working days)", default=1
    )
    business_trip_advance_request_min_days = fields.Integer(
        string="Minimum Advance Payment Notice (working days)", default=3
    )
    business_trip_max_single_days = fields.Integer(
        string="Maximum Single Assignment Duration (working days)", default=5
    )
    business_trip_settlement_days = fields.Integer(
        string="Advance Settlement Deadline (days after return)", default=5
    )
    business_trip_transportation_deduction_pct = fields.Float(
        string="Transportation Deduction (%)", default=20.0
    )
    business_trip_senior_mgmt_adjustment_pct = fields.Float(
        string="Senior Management Adjustment (%)", default=20.0
    )
