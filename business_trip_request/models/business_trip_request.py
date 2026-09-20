from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

ARAB_COUNTRY_CODES = {
    "SA", "AE", "BH", "KW", "OM", "QA", "EG", "JO", "LB", "SY", "IQ",
    "YE", "PS", "MA", "DZ", "TN", "LY", "SD", "MR", "SO", "DJ", "KM",
}
EUROPE_JAPAN_CODES = {
    "JP", "GB", "FR", "DE", "IT", "ES", "PT", "NL", "BE", "CH", "AT",
    "SE", "NO", "DK", "FI", "IE", "GR", "PL", "CZ",
}

WEEKEND_ISO_WEEKDAYS = {5, 6}  # Friday, Saturday


def _count_working_days(date_from, date_to):
    if not date_from or not date_to or date_to < date_from:
        return 0
    days = 0
    current = date_from
    while current <= date_to:
        if current.isoweekday() not in WEEKEND_ISO_WEEKDAYS:
            days += 1
        current += timedelta(days=1)
    return days


class BusinessTripRequest(models.Model):
    _name = "business.trip.request"
    _description = "Business Trip / Assignment Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(
        string="Request Number", default="New", copy=False, tracking=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", store=True
    )

    # ---------------------------------------------------------------
    # Employee (auto-populated, read-only to the employee)
    # ---------------------------------------------------------------
    employee_id = fields.Many2one(
        "hr.employee",
        required=True,
        tracking=True,
        default=lambda self: self.env.user.employee_id,
    )
    job_title = fields.Char(related="employee_id.job_title", store=True)
    department_id = fields.Many2one(
        related="employee_id.department_id", store=True
    )
    direct_manager_id = fields.Many2one(
        "hr.employee", related="employee_id.parent_id", store=True
    )
    direct_manager_user_id = fields.Many2one(
        "res.users", compute="_compute_approver_users", store=True
    )
    department_manager_user_id = fields.Many2one(
        "res.users", compute="_compute_approver_users", store=True
    )
    ceo_user_id = fields.Many2one(
        "res.users", compute="_compute_approver_users", store=True
    )
    is_senior_management = fields.Boolean(
        related="employee_id.is_senior_management"
    )
    is_frequent_traveler = fields.Boolean(related="employee_id.frequent_traveler")
    travel_class_id = fields.Selection(related="employee_id.travel_class_id")

    @api.depends("employee_id", "employee_id.parent_id", "employee_id.department_id",
                 "company_id.business_trip_ceo_user_id")
    def _compute_approver_users(self):
        for rec in self:
            rec.direct_manager_user_id = rec.employee_id.parent_id.user_id
            rec.department_manager_user_id = (
                rec.employee_id.department_id.manager_id.user_id
            )
            rec.ceo_user_id = rec.company_id.business_trip_ceo_user_id

    # ---------------------------------------------------------------
    # Trip information
    # ---------------------------------------------------------------
    destination_city = fields.Char(string="Assignment Location (City)", required=True)
    destination_country_id = fields.Many2one("res.country", required=True)
    distance_km = fields.Float(
        string="Total Travel Distance (km)",
        help="Used to determine whether a domestic assignment qualifies as a "
        "formal business assignment (>= 300 km).",
    )
    purpose = fields.Text(string="Assignment Purpose")
    objectives = fields.Text(string="Business Trip Objectives")

    date_start = fields.Date(string="Start Date", required=True, tracking=True)
    date_end = fields.Date(string="End Date", required=True, tracking=True)
    overnight_stay = fields.Boolean(string="Overnight Stay Required")

    total_days = fields.Integer(compute="_compute_dates", store=True)
    overnight_count = fields.Integer(compute="_compute_dates", store=True)

    trip_type = fields.Selection(
        [("domestic", "Domestic"), ("international", "International")],
        compute="_compute_trip_type",
        store=True,
    )
    region = fields.Selection(
        [
            ("arabic", "Arabic Countries"),
            ("asian", "Asian Countries"),
            ("europe_japan", "Europe / Japan"),
        ],
        string="International Region",
        compute="_compute_trip_type",
        store=True,
        readonly=False,
    )
    is_formal_assignment = fields.Boolean(
        string="Formal Business Assignment",
        compute="_compute_dates",
        store=True,
        help="False when domestic distance is below 300 km: treated as a "
        "Short Domestic Business Trip instead of a formal assignment.",
    )
    is_peak_period = fields.Boolean(
        string="Peak Period Location/Date", compute="_compute_peak_period"
    )

    flight_duration_hours = fields.Float(string="Flight Duration (hours)")
    extra_days = fields.Integer(
        string="International Extra Travel Days", compute="_compute_extra_days", store=True
    )

    @api.depends("date_start", "date_end", "overnight_stay", "trip_type", "distance_km")
    def _compute_dates(self):
        for rec in self:
            total_days = 0
            if rec.date_start and rec.date_end and rec.date_end >= rec.date_start:
                total_days = (rec.date_end - rec.date_start).days + 1
            rec.total_days = total_days
            rec.overnight_count = max(total_days - 1, 0) if rec.overnight_stay else 0
            if rec.trip_type == "domestic":
                rec.is_formal_assignment = rec.distance_km >= 300
            else:
                rec.is_formal_assignment = True

    @api.depends("destination_country_id", "company_id")
    def _compute_trip_type(self):
        for rec in self:
            home_country = rec.company_id.country_id
            if rec.destination_country_id and home_country:
                if rec.destination_country_id == home_country:
                    rec.trip_type = "domestic"
                    rec.region = False
                else:
                    rec.trip_type = "international"
                    code = rec.destination_country_id.code
                    if code in ARAB_COUNTRY_CODES:
                        rec.region = rec.region or "arabic"
                    elif code in EUROPE_JAPAN_CODES:
                        rec.region = rec.region or "europe_japan"
                    else:
                        rec.region = rec.region or "asian"
            else:
                rec.trip_type = False

    @api.depends("destination_city", "date_start")
    def _compute_peak_period(self):
        from .business_trip_peak_period import PEAK_CITIES

        for rec in self:
            is_peak = False
            city = (rec.destination_city or "").strip().lower()
            if city in PEAK_CITIES and rec.date_start:
                if rec.date_start.month in (6, 7, 8):
                    is_peak = True
                else:
                    periods = self.env["business.trip.peak.period"].search(
                        [
                            ("date_from", "<=", rec.date_start),
                            ("date_to", ">=", rec.date_start),
                        ],
                        limit=1,
                    )
                    is_peak = bool(periods)
            rec.is_peak_period = is_peak

    @api.depends("trip_type", "flight_duration_hours")
    def _compute_extra_days(self):
        for rec in self:
            if rec.trip_type != "international" or not rec.flight_duration_hours:
                rec.extra_days = 0
            elif rec.flight_duration_hours < 4:
                rec.extra_days = 1
            else:
                rec.extra_days = 2

    # ---------------------------------------------------------------
    # Required travel services
    # ---------------------------------------------------------------
    need_flight = fields.Boolean(string="Flight Ticket Booking")
    need_transportation = fields.Boolean(string="Transportation / Rental Car")
    need_visa = fields.Boolean(string="Exit/Re-entry Visa – International Assignment")
    need_other = fields.Boolean(string="Other")
    other_specify = fields.Char(string="Please Specify")

    # ---------------------------------------------------------------
    # Combine with annual leave
    # ---------------------------------------------------------------
    combine_annual_leave = fields.Boolean(string="Combine with Annual Leave?")
    leave_start_date = fields.Date(string="Leave Start Date")
    leave_end_date = fields.Date(string="Leave End Date")

    # ---------------------------------------------------------------
    # Validation engine (non-blocking warnings)
    # ---------------------------------------------------------------
    validation_warning_ids = fields.Text(
        string="Business Rules Validation", compute="_compute_validation_warnings"
    )

    @api.depends(
        "purpose", "objectives", "date_start", "date_end", "distance_km",
        "trip_type", "need_transportation", "total_days",
    )
    def _compute_validation_warnings(self):
        for rec in self:
            messages = []
            messages.append(
                _("✓ Assignment purpose provided.") if rec.purpose
                else _("✕ Assignment purpose missing.")
            )
            messages.append(
                _("✓ Business trip objectives provided.") if rec.objectives
                else _("✕ Business trip objectives missing.")
            )
            if rec.date_start:
                working_days = _count_working_days(
                    fields.Date.context_today(rec), rec.date_start
                )
                min_days = rec.company_id.business_trip_min_advance_days or 1
                if working_days >= min_days:
                    messages.append(_("✓ More than %s working day(s) before travel.") % min_days)
                else:
                    messages.append(
                        _("✕ Less than %s working day(s) before travel.") % min_days
                    )
            if rec.trip_type == "domestic" and rec.distance_km and rec.distance_km < 300:
                messages.append(
                    _("⚠ Trip is below 300 km and may not qualify as a formal assignment.")
                )
            if rec.need_transportation:
                messages.append(
                    _("⚠ Transportation selected — transportation component reduced by %s%%.")
                    % (rec.company_id.business_trip_transportation_deduction_pct or 20)
                )
            max_days = rec.company_id.business_trip_max_single_days or 5
            working_duration = _count_working_days(rec.date_start, rec.date_end)
            if rec.date_start and rec.date_end and working_duration > max_days:
                messages.append(
                    _("⚠ The duration of a single assignment should not exceed %s working "
                      "days according to the policy.") % max_days
                )
            rec.validation_warning_ids = "\n".join(messages)

    # ---------------------------------------------------------------
    # Advance / cash advance
    # ---------------------------------------------------------------
    advance_required = fields.Boolean(string="Advance Required?")
    requested_advance = fields.Monetary(string="Requested Advance")

    @api.constrains("advance_required", "requested_advance", "net_allowance")
    def _check_requested_advance(self):
        for rec in self:
            if rec.advance_required and rec.requested_advance > rec.net_allowance > 0:
                raise ValidationError(
                    _("The requested advance must not exceed the expected applicable "
                      "allowance (%s).") % rec.net_allowance
                )

    # ---------------------------------------------------------------
    # HR allowance calculation
    # ---------------------------------------------------------------
    basic_salary = fields.Monetary(string="Monthly Basic Salary")
    applicable_rate = fields.Float(string="Applicable Rate (%)")
    base_daily_allowance = fields.Monetary(string="Base Daily Assignment Allowance")
    eligible_days = fields.Integer(string="Number of Eligible Days")
    overnight_factor = fields.Float(string="Overnight Factor", default=1.0)
    gross_allowance = fields.Monetary(string="Gross Allowance")
    accommodation_amount = fields.Monetary(string="Accommodation (40%)")
    transportation_amount = fields.Monetary(string="Transportation (30%)")
    food_amount = fields.Monetary(string="Food (15%)")
    misc_allowance_amount = fields.Monetary(string="Assignment Allowance (15%)")
    transportation_deduction = fields.Monetary(string="Transportation Deduction")
    net_allowance = fields.Monetary(string="Net Allowance", tracking=True)
    short_trip_daily_amount = fields.Monetary(
        string="Short Trip Daily Allowance (SAR 150/day)", compute="_compute_short_trip", store=True
    )
    accommodation_actual_cost = fields.Monetary(string="Actual Accommodation Cost")
    payment_timing = fields.Selection(
        [("before_trip", "Paid Before Trip"), ("after_trip", "Paid After Trip")],
        default="after_trip",
    )

    @api.depends("total_days", "is_formal_assignment", "trip_type", "company_id")
    def _compute_short_trip(self):
        for rec in self:
            if rec.trip_type == "domestic" and not rec.is_formal_assignment:
                rate = rec.company_id.business_trip_short_domestic_rate or 150.0
                rec.short_trip_daily_amount = rate * rec.total_days
            else:
                rec.short_trip_daily_amount = 0.0

    def _find_allowance_rule(self):
        self.ensure_one()
        domain = [
            ("company_id", "=", self.company_id.id),
            ("trip_type", "=", self.trip_type),
        ]
        if self.trip_type == "international":
            domain.append(("region", "=", self.region))
        return self.env["business.trip.allowance.rule"].search(domain, limit=1)

    def action_calculate_allowance(self):
        for rec in self:
            if rec.state != "hr_review":
                raise UserError(_("Allowance can only be calculated during HR Review."))
            rule = rec._find_allowance_rule()
            if not rule:
                raise UserError(
                    _("No allowance rule configured for %s.") % (rec.region or rec.trip_type)
                )
            rate = rule.percentage
            if rec.is_senior_management:
                rate += rec.company_id.business_trip_senior_mgmt_adjustment_pct or 20.0
            rec.applicable_rate = rate

            base = rec.basic_salary * (rate / 100.0)
            if rule.min_amount:
                base = max(base, rule.min_amount)
            if rule.max_amount:
                base = min(base, rule.max_amount)
            rec.base_daily_allowance = base

            eligible_days = rec.total_days + rec.extra_days
            rec.eligible_days = eligible_days

            rec.overnight_factor = 1.0 if rec.overnight_stay else 0.5
            gross = base * eligible_days * rec.overnight_factor
            rec.gross_allowance = gross

            rec.accommodation_amount = gross * 0.40
            transportation_component = gross * 0.30
            rec.food_amount = gross * 0.15
            rec.misc_allowance_amount = gross * 0.15

            deduction = 0.0
            if rec.need_transportation:
                pct = rec.company_id.business_trip_transportation_deduction_pct or 20.0
                deduction = transportation_component * (pct / 100.0)
            rec.transportation_deduction = deduction
            rec.transportation_amount = transportation_component - deduction
            rec.net_allowance = gross - deduction

            rec.message_post(
                body=_(
                    "Allowance calculated: rate %(rate)s%%, base/day %(base)s, "
                    "eligible days %(days)s, overnight factor %(factor)s, "
                    "gross %(gross)s, transportation deduction %(ded)s, "
                    "net allowance %(net)s."
                )
                % {
                    "rate": rate,
                    "base": base,
                    "days": eligible_days,
                    "factor": rec.overnight_factor,
                    "gross": gross,
                    "ded": deduction,
                    "net": rec.net_allowance,
                }
            )
            rec.state = "allowance_calculated"

    # ---------------------------------------------------------------
    # Trip report
    # ---------------------------------------------------------------
    actual_date_start = fields.Date(string="Actual Start Date")
    actual_date_end = fields.Date(string="Actual Return Date")
    actual_overnight_count = fields.Integer(string="Actual Number of Overnight Stays")
    work_summary = fields.Text(string="Summary of Work Performed")
    objectives_achieved = fields.Text(string="Objectives Achieved")
    report_notes = fields.Text(string="Notes")
    report_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="draft",
        tracking=True,
    )
    actual_days = fields.Integer(compute="_compute_actual_days", store=True)
    days_difference = fields.Integer(compute="_compute_actual_days", store=True)
    additional_days = fields.Integer(string="Additional Days Beyond Plan")
    additional_days_justification = fields.Text(string="Justification for Additional Days")

    @api.depends("actual_date_start", "actual_date_end", "total_days")
    def _compute_actual_days(self):
        for rec in self:
            if rec.actual_date_start and rec.actual_date_end and rec.actual_date_end >= rec.actual_date_start:
                actual = (rec.actual_date_end - rec.actual_date_start).days + 1
            else:
                actual = 0
            rec.actual_days = actual
            rec.days_difference = actual - rec.total_days

    # ---------------------------------------------------------------
    # Settlement
    # ---------------------------------------------------------------
    settlement_state = fields.Selection(
        [("pending", "Pending"), ("processed", "Processed")],
        default="pending",
        tracking=True,
    )
    settlement_date = fields.Date()
    settlement_amount = fields.Monetary(compute="_compute_settlement_amount", store=True)
    processed_by = fields.Many2one("res.users")

    @api.depends("net_allowance", "requested_advance", "advance_required")
    def _compute_settlement_amount(self):
        for rec in self:
            advance = rec.requested_advance if rec.advance_required else 0.0
            rec.settlement_amount = rec.net_allowance - advance

    # ---------------------------------------------------------------
    # Approval workflow
    # ---------------------------------------------------------------
    approval_line_ids = fields.One2many(
        "business.trip.approval.line", "request_id", string="Approval History"
    )
    rejection_reason = fields.Text()
    return_comment = fields.Text()
    can_current_user_approve = fields.Boolean(
        compute="_compute_can_current_user_approve"
    )

    @api.depends("approval_line_ids.state", "approval_line_ids.approver_id", "state")
    def _compute_can_current_user_approve(self):
        hr_group = self.env.ref(
            "business_trip_request.group_business_trip_hr", raise_if_not_found=False
        )
        is_hr = bool(hr_group) and self.env.user in hr_group.users
        for rec in self:
            line = rec._current_approval_line()
            rec.can_current_user_approve = bool(line) and (
                is_hr or line.approver_id == self.env.user
            )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("pending_direct_manager", "Pending Direct Manager Approval"),
            ("pending_department_manager", "Pending Department Manager Approval"),
            ("pending_ceo", "Pending CEO Approval"),
            ("approved", "Approved"),
            ("hr_review", "HR Review"),
            ("allowance_calculated", "Allowance Calculated"),
            ("ready_for_travel", "Ready for Travel"),
            ("trip_in_progress", "Trip in Progress"),
            ("trip_report_required", "Trip Report Required"),
            ("trip_report_under_approval", "Trip Report Under Approval"),
            ("settlement", "Settlement"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
            ("returned", "Returned for Modification"),
        ],
        default="draft",
        required=True,
        tracking=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "business.trip.request"
                ) or "New"
        return super().create(vals_list)

    def _current_approval_line(self):
        self.ensure_one()
        return self.approval_line_ids.filtered(lambda l: l.state == "pending").sorted(
            "sequence"
        )[:1]

    def _check_is_current_approver(self):
        self.ensure_one()
        line = self._current_approval_line()
        if not line:
            raise UserError(_("There is no pending approval step for this request."))
        user = self.env.user
        is_hr = user.has_group("business_trip_request.group_business_trip_hr")
        if not is_hr and line.approver_id != user:
            raise UserError(
                _("Only %s can act on this approval step.")
                % (line.approver_id.name or _("the assigned approver"))
            )
        return line

    def action_submit(self):
        for rec in self:
            if not rec.purpose or not rec.objectives:
                raise UserError(
                    _("Assignment purpose and objectives are mandatory before submission.")
                )
            if not rec.date_start or not rec.date_end:
                raise UserError(_("Assignment duration (start/end dates) is mandatory."))
            min_days = rec.company_id.business_trip_min_advance_days or 1
            working_days = _count_working_days(
                fields.Date.context_today(rec), rec.date_start
            )
            if working_days < min_days:
                raise UserError(
                    _("The business assignment request must normally be submitted at "
                      "least %s working day(s) before the assignment start date.")
                    % min_days
                )
            if rec.advance_required:
                adv_min_days = rec.company_id.business_trip_advance_request_min_days or 3
                if working_days < adv_min_days:
                    raise UserError(
                        _("The advance request must be submitted at least %s working "
                          "day(s) before travel.") % adv_min_days
                    )

            rec.approval_line_ids.sudo().unlink()
            lines = [
                (0, 0, {
                    "sequence": 10, "role": "direct_manager",
                    "approver_id": rec.direct_manager_user_id.id,
                }),
                (0, 0, {
                    "sequence": 20, "role": "department_manager",
                    "approver_id": rec.department_manager_user_id.id,
                }),
                (0, 0, {
                    "sequence": 30, "role": "ceo",
                    "approver_id": rec.ceo_user_id.id,
                }),
            ]
            rec.write({"approval_line_ids": lines, "state": "pending_direct_manager"})
            rec.message_post(body=_("Request submitted for approval."))
            if rec.direct_manager_user_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=rec.direct_manager_user_id.id,
                    summary=_("Approve Business Trip Request %s") % rec.name,
                )

    def action_approve(self):
        for rec in self:
            line = rec._check_is_current_approver()
            line.write({"state": "approved", "date": fields.Datetime.now()})
            rec.message_post(
                body=_("%s approved (%s).") % (line.role.replace("_", " ").title(), line.approver_id.name or "")
            )
            next_line = rec._current_approval_line()
            if next_line:
                rec.state = {
                    "direct_manager": "pending_direct_manager",
                    "department_manager": "pending_department_manager",
                    "ceo": "pending_ceo",
                }[next_line.role]
                if next_line.approver_id:
                    rec.activity_schedule(
                        "mail.mail_activity_data_todo",
                        user_id=next_line.approver_id.id,
                        summary=_("Approve Business Trip Request %s") % rec.name,
                    )
            else:
                rec.state = "hr_review"
                rec.message_post(body=_("Request fully approved. Routed to HR for review."))
                hr_group = self.env.ref(
                    "business_trip_request.group_business_trip_hr", raise_if_not_found=False
                )
                if hr_group:
                    for user in hr_group.users:
                        rec.activity_schedule(
                            "mail.mail_activity_data_todo",
                            user_id=user.id,
                            summary=_("Business Trip Request %s ready for HR review") % rec.name,
                        )

    def _open_reason_wizard(self, action_type):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reason / Comment"),
            "res_model": "business.trip.reason.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_request_id": self.id,
                "default_action_type": action_type,
            },
        }

    def action_open_reject_wizard(self):
        return self._open_reason_wizard("reject")

    def action_open_return_wizard(self):
        return self._open_reason_wizard("return")

    def action_open_reject_report_wizard(self):
        return self._open_reason_wizard("reject_report")

    def action_reject(self, reason):
        for rec in self:
            line = rec._check_is_current_approver()
            line.write(
                {"state": "rejected", "comment": reason, "date": fields.Datetime.now()}
            )
            rec.write({"state": "rejected", "rejection_reason": reason})
            rec.message_post(body=_("Request rejected: %s") % reason)

    def action_return_for_modification(self, comment):
        for rec in self:
            line = rec._check_is_current_approver()
            line.write(
                {"state": "returned", "comment": comment, "date": fields.Datetime.now()}
            )
            rec.write({"state": "returned", "return_comment": comment})
            rec.message_post(body=_("Request returned for modification: %s") % comment)

    def action_resubmit(self):
        for rec in self:
            if rec.state != "returned":
                raise UserError(_("Only requests returned for modification can be resubmitted."))
            rec.state = "draft"

    def action_mark_ready_for_travel(self):
        for rec in self:
            if rec.state != "allowance_calculated":
                raise UserError(_("Allowance must be calculated first."))
            rec.state = "ready_for_travel"

    def action_start_trip(self):
        for rec in self:
            if rec.state != "ready_for_travel":
                raise UserError(_("Request is not ready for travel."))
            rec.state = "trip_in_progress"

    def action_end_trip(self):
        for rec in self:
            if rec.state != "trip_in_progress":
                raise UserError(_("Trip is not in progress."))
            rec.state = "trip_report_required"
            if rec.employee_id.user_id:
                rec.activity_schedule(
                    "mail.mail_activity_data_todo",
                    user_id=rec.employee_id.user_id.id,
                    summary=_("Submit Business Trip Report for %s") % rec.name,
                )

    def action_submit_trip_report(self):
        for rec in self:
            if rec.state != "trip_report_required":
                raise UserError(_("Trip report is not required at this stage."))
            if not rec.actual_date_start or not rec.actual_date_end or not rec.work_summary:
                raise UserError(
                    _("Actual dates and summary of work performed are mandatory to "
                      "submit the trip report.")
                )
            rec.write({"state": "trip_report_under_approval", "report_state": "submitted"})
            rec.message_post(body=_("Trip report submitted."))

    def action_approve_trip_report(self):
        for rec in self:
            if rec.state != "trip_report_under_approval":
                raise UserError(_("There is no trip report pending approval."))
            rec.write({"state": "settlement", "report_state": "approved"})
            rec.message_post(
                body=_("Trip report approved. Forwarded to HR and Finance for settlement.")
            )

    def action_reject_trip_report(self, reason):
        for rec in self:
            if rec.state != "trip_report_under_approval":
                raise UserError(_("There is no trip report pending approval."))
            rec.write({"state": "trip_report_required", "report_state": "rejected"})
            rec.message_post(body=_("Trip report rejected: %s") % reason)

    def action_process_settlement(self):
        for rec in self:
            if rec.state != "settlement":
                raise UserError(_("Request is not at the settlement stage."))
            if rec.report_state != "approved":
                raise UserError(
                    _("Settlement cannot be finalized until the trip report has been "
                      "submitted and approved.")
                )
            rec.write(
                {
                    "state": "completed",
                    "settlement_state": "processed",
                    "settlement_date": fields.Date.context_today(rec),
                    "processed_by": self.env.user.id,
                }
            )
            rec.message_post(body=_("Settlement processed. Request completed."))
