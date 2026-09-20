from odoo import fields, models


class ResCity(models.Model):
    _inherit = "res.city"

    is_peak_city = fields.Boolean(
        string="Peak Period City",
        help="Marked cities are treated as peak-period locations during the "
        "configured peak season (Settings > Business Trips) or any configured "
        "Peak Period date range.",
    )
