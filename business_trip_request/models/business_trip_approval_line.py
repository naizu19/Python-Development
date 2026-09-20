from odoo import fields, models


class BusinessTripApprovalLine(models.Model):
    _name = "business.trip.approval.line"
    _description = "Business Trip Approval Step"
    _order = "sequence"

    request_id = fields.Many2one(
        "business.trip.request", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(required=True)
    role = fields.Selection(
        [
            ("direct_manager", "Direct Manager"),
            ("department_manager", "Department Manager"),
            ("ceo", "CEO"),
        ],
        required=True,
    )
    approver_id = fields.Many2one("res.users", string="Approver")
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("returned", "Returned for Modification"),
        ],
        default="pending",
        required=True,
    )
    comment = fields.Text()
    date = fields.Datetime()
