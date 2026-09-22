from odoo import fields, models


class BusinessTripTransaction(models.Model):
    _name = "business.trip.transaction"
    _description = "Business Trip Transaction History"
    _order = "date desc, id desc"

    request_id = fields.Many2one(
        "business.trip.request", required=True, ondelete="cascade",
        string="Trip Request",
    )
    employee_id = fields.Many2one(
        "hr.employee", related="request_id.employee_id", store=True
    )
    user_id = fields.Many2one(
        "res.users", related="employee_id.user_id", string="Employee User", store=True
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
    processed_by = fields.Many2one(
        "res.users", required=True, default=lambda self: self.env.user
    )
    note = fields.Char()

    # ---------------------------------------------------------------
    # Trip snapshot - so the full picture is visible on this record
    # without navigating back to the request.
    # ---------------------------------------------------------------
    destination_city = fields.Char(related="request_id.destination_city", store=True)
    destination_country_id = fields.Many2one(
        related="request_id.destination_country_id", store=True
    )
    trip_type = fields.Selection(related="request_id.trip_type", store=True)
    date_start = fields.Date(related="request_id.date_start", store=True)
    date_end = fields.Date(related="request_id.date_end", store=True)
    total_days = fields.Integer(related="request_id.total_days", store=True)

    # ---------------------------------------------------------------
    # Allowance snapshot
    # ---------------------------------------------------------------
    basic_salary = fields.Monetary(related="request_id.basic_salary")
    applicable_rate = fields.Float(related="request_id.applicable_rate")
    gross_allowance = fields.Monetary(related="request_id.gross_allowance")
    requested_advance = fields.Monetary(related="request_id.requested_advance")
    net_allowance = fields.Monetary(related="request_id.net_allowance")
    settlement_amount = fields.Monetary(related="request_id.settlement_amount")
