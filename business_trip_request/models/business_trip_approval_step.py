from odoo import api, fields, models
from odoo.exceptions import ValidationError


class BusinessTripApprovalStep(models.Model):
    _name = "business.trip.approval.step"
    _description = "Business Trip Approval Step (configurable)"
    _order = "sequence, id"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    source = fields.Selection(
        [
            ("employee_manager", "Employee's Direct Manager"),
            ("department_manager", "Employee's Department Manager"),
            ("ceo", "Company CEO (set in Settings)"),
            ("group", "Members of a User Group"),
        ],
        required=True,
        default="group",
        help="Where this step's approver comes from. 'Members of a User Group' lets "
        "any user you add to that group act on this step, instead of relying on "
        "HR hierarchy fields (Direct Manager / Department Manager) being filled in.",
    )
    group_id = fields.Many2one(
        "res.groups",
        string="Approver Group",
        help="Any user who is a member of this group can approve, reject, or "
        "return this step. Required when Source is 'Members of a User Group'.",
    )

    @api.constrains("source", "group_id")
    def _check_group_required(self):
        for rec in self:
            if rec.source == "group" and not rec.group_id:
                raise ValidationError(
                    "An Approver Group is required when Source is "
                    "'Members of a User Group'."
                )
