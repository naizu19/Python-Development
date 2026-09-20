from odoo import fields, models


class BusinessTripCity(models.Model):
    _name = "business.trip.city"
    _description = "Business Trip Destination City"
    _order = "name"

    name = fields.Char(required=True)
    country_id = fields.Many2one("res.country", required=True)
    is_peak_city = fields.Boolean(
        string="Peak Period City",
        help="Marked cities are treated as peak-period locations during the "
        "configured peak season (Settings) or any configured Peak Period date range.",
    )
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

    _sql_constraints = [
        (
            "name_country_uniq",
            "unique(name, country_id, company_id)",
            "This city already exists for the selected country.",
        )
    ]

    def name_get(self):
        return [(rec.id, "%s, %s" % (rec.name, rec.country_id.name)) for rec in self]
