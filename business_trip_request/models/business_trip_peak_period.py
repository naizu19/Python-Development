from odoo import fields, models

PEAK_CITIES = ["abha", "jeddah", "makkah", "mecca", "madinah", "medina", "dammam", "neom"]


class BusinessTripPeakPeriod(models.Model):
    _name = "business.trip.peak.period"
    _description = "Business Trip Peak Period (e.g. Eid holiday weeks)"
    _order = "date_from desc"

    name = fields.Char(required=True, help="E.g. 'Eid Al-Fitr 2026'")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
