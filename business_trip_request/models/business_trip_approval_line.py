from odoo import fields, models


class BusinessTripApprovalLine(models.Model):
    _name = "business.trip.approval.line"
    _description = "Business Trip Approval Step (on a request)"
    _order = "sequence"

    request_id = fields.Many2one(
        "business.trip.request", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(required=True)
    name = fields.Char(required=True, help="Step label, copied from the configured approval step.")
    approver_id = fields.Many2one(
        "res.users", string="Approver",
        help="Set when this step's source is an HR relation (Direct/Department Manager, CEO).",
    )
    approver_group_id = fields.Many2one(
        "res.groups", string="Approver Group",
        help="Set when this step's source is a user group: any member of this group may act.",
    )
    approved_by = fields.Many2one(
        "res.users", string="Actioned By",
        help="The specific user who actually approved/rejected/returned this step "
        "(relevant when the step is group-based and several users could act on it).",
    )
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
