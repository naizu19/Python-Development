from odoo import fields, models


class BusinessTripTransaction(models.Model):
    _name = "business.trip.transaction"
    _description = "Business Trip Transaction History"
    _order = "date desc, id desc"

    request_id = fields.Many2one(
        "business.trip.request", required=True, ondelete="cascade"
    )
    employee_id = fields.Many2one(
        "hr.employee", related="request_id.employee_id", store=True
    )
    transaction_type = fields.Selection(
        [
            ("advance_payment", "Advance Payment"),
            ("settlement", "Settlement"),
        ],
        required=True,
        default="settlement",
    )
    amount = fields.Monetary(required=True)
    currency_id = fields.Many2one(
        "res.currency", related="request_id.currency_id", store=True
    )
    date = fields.Date(required=True, default=fields.Date.context_today)
    processed_by = fields.Many2one("res.users", required=True)
    note = fields.Char()
