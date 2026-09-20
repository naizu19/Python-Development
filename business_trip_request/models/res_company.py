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
    business_trip_formal_distance_km = fields.Float(
        string="Formal Assignment Minimum Distance (km)", default=300.0
    )
    business_trip_no_overnight_factor = fields.Float(
        string="No-Overnight-Stay Allowance Factor", default=0.5,
        help="Fraction of the full allowance paid when no overnight stay is required (0.5 = 50%).",
    )
    business_trip_pct_accommodation = fields.Float(
        string="Accommodation Share (%)", default=40.0
    )
    business_trip_pct_transportation = fields.Float(
        string="Transportation Share (%)", default=30.0
    )
    business_trip_pct_food = fields.Float(
        string="Food Share (%)", default=15.0
    )
    business_trip_pct_misc = fields.Float(
        string="Assignment Allowance Share (%)", default=15.0
    )
    business_trip_intl_short_flight_hours = fields.Float(
        string="International Short-Flight Threshold (hours)", default=4.0
    )
    business_trip_intl_short_flight_extra_days = fields.Integer(
        string="Extra Days for Short Flights", default=1
    )
    business_trip_intl_long_flight_extra_days = fields.Integer(
        string="Extra Days for Long Flights", default=2
    )
    business_trip_peak_season_start_month = fields.Integer(
        string="Peak Season Start Month", default=6
    )
    business_trip_peak_season_end_month = fields.Integer(
        string="Peak Season End Month", default=8
    )
    business_trip_peak_cities = fields.Char(
        string="Peak Period Cities",
        default="Abha, Jeddah, Makkah, Madinah, Dammam, NEOM",
        help="Comma-separated city names treated as peak-period locations "
        "during the configured peak season (or a configured Peak Period date range).",
    )
