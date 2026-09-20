from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    business_trip_ceo_user_id = fields.Many2one(
        related="company_id.business_trip_ceo_user_id", readonly=False
    )
    business_trip_short_domestic_rate = fields.Monetary(
        related="company_id.business_trip_short_domestic_rate", readonly=False
    )
    business_trip_min_advance_days = fields.Integer(
        related="company_id.business_trip_min_advance_days", readonly=False
    )
    business_trip_advance_request_min_days = fields.Integer(
        related="company_id.business_trip_advance_request_min_days", readonly=False
    )
    business_trip_max_single_days = fields.Integer(
        related="company_id.business_trip_max_single_days", readonly=False
    )
    business_trip_settlement_days = fields.Integer(
        related="company_id.business_trip_settlement_days", readonly=False
    )
    business_trip_transportation_deduction_pct = fields.Float(
        related="company_id.business_trip_transportation_deduction_pct", readonly=False
    )
    business_trip_senior_mgmt_adjustment_pct = fields.Float(
        related="company_id.business_trip_senior_mgmt_adjustment_pct", readonly=False
    )
    business_trip_formal_distance_km = fields.Float(
        related="company_id.business_trip_formal_distance_km", readonly=False
    )
    business_trip_no_overnight_factor = fields.Float(
        related="company_id.business_trip_no_overnight_factor", readonly=False
    )
    business_trip_pct_accommodation = fields.Float(
        related="company_id.business_trip_pct_accommodation", readonly=False
    )
    business_trip_pct_transportation = fields.Float(
        related="company_id.business_trip_pct_transportation", readonly=False
    )
    business_trip_pct_food = fields.Float(
        related="company_id.business_trip_pct_food", readonly=False
    )
    business_trip_pct_misc = fields.Float(
        related="company_id.business_trip_pct_misc", readonly=False
    )
    business_trip_intl_short_flight_hours = fields.Float(
        related="company_id.business_trip_intl_short_flight_hours", readonly=False
    )
    business_trip_intl_short_flight_extra_days = fields.Integer(
        related="company_id.business_trip_intl_short_flight_extra_days", readonly=False
    )
    business_trip_intl_long_flight_extra_days = fields.Integer(
        related="company_id.business_trip_intl_long_flight_extra_days", readonly=False
    )
    business_trip_peak_season_start_month = fields.Integer(
        related="company_id.business_trip_peak_season_start_month", readonly=False
    )
    business_trip_peak_season_end_month = fields.Integer(
        related="company_id.business_trip_peak_season_end_month", readonly=False
    )
