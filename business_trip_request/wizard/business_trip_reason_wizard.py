from odoo import fields, models


class BusinessTripReasonWizard(models.TransientModel):
    _name = "business.trip.reason.wizard"
    _description = "Business Trip Request - Reason / Comment"

    request_id = fields.Many2one("business.trip.request", required=True)
    action_type = fields.Selection(
        [
            ("reject", "Reject"),
            ("return", "Return for Modification"),
        ],
        required=True,
    )
    reason = fields.Text(required=True)

    def action_confirm(self):
        self.ensure_one()
        if self.action_type == "reject":
            self.request_id.action_reject(self.reason)
        elif self.action_type == "return":
            self.request_id.action_return_for_modification(self.reason)
        return {"type": "ir.actions.act_window_close"}
