from datetime import timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.fields import Date
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBusinessTripRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({"country_id": cls.env.ref("base.sa").id})
        cls.saudi = cls.env.ref("base.sa")
        cls.uae = cls.env.ref("base.ae")
        cls.japan = cls.env.ref("base.jp")

        cls.employee = cls.env["hr.employee"].create(
            {"name": "Omar Alhamdan", "company_id": cls.company.id}
        )

        # Run as a member of the HR group so approval actions succeed in
        # tests regardless of whether HR-hierarchy fields (manager, CEO)
        # are configured on the test employee.
        hr_group = cls.env.ref("business_trip_request.group_business_trip_hr")
        hr_group.users = [(4, cls.env.user.id)]

    def _make_request(self, **overrides):
        vals = {
            "employee_id": self.employee.id,
            "destination_city": "Riyadh",
            "destination_country_id": self.saudi.id,
            "purpose": "Client meeting",
            "objectives": "Close the annual services contract",
            "date_start": Date.to_string(Date.today() + timedelta(days=5)),
            "date_end": Date.to_string(Date.today() + timedelta(days=7)),
        }
        vals.update(overrides)
        return self.env["business.trip.request"].create(vals)

    # ------------------------------------------------------------
    # Domestic vs International detection (Section 3.A)
    # ------------------------------------------------------------
    def test_domestic_detection(self):
        trip = self._make_request(distance_km=400)
        self.assertEqual(trip.trip_type, "domestic")
        self.assertTrue(trip.is_formal_assignment)

    def test_international_detection(self):
        trip = self._make_request(
            destination_city="Dubai", destination_country_id=self.uae.id
        )
        self.assertEqual(trip.trip_type, "international")

    # ------------------------------------------------------------
    # Rule 1: Distance below the configurable threshold (default 300km)
    # ------------------------------------------------------------
    def test_short_domestic_trip_below_threshold(self):
        trip = self._make_request(distance_km=120)
        self.assertFalse(trip.is_formal_assignment)
        self.assertGreater(trip.short_trip_daily_amount, 0)

    def test_domestic_trip_above_threshold_is_formal(self):
        trip = self._make_request(distance_km=350)
        self.assertTrue(trip.is_formal_assignment)
        self.assertEqual(trip.short_trip_daily_amount, 0)

    def test_distance_threshold_is_configurable(self):
        self.company.business_trip_formal_distance_km = 100
        trip = self._make_request(distance_km=150)
        self.assertTrue(trip.is_formal_assignment)

    # ------------------------------------------------------------
    # Rule 8: Purpose/Objectives/Dates mandatory before submit
    # ------------------------------------------------------------
    def test_submit_blocks_without_purpose(self):
        trip = self._make_request(purpose=False)
        with self.assertRaises(UserError):
            trip.action_submit()

    def test_submit_blocks_without_objectives(self):
        trip = self._make_request(objectives=False)
        with self.assertRaises(UserError):
            trip.action_submit()

    # ------------------------------------------------------------
    # Rule 7: Minimum advance notice before submitting
    # ------------------------------------------------------------
    def test_submit_blocks_when_less_than_min_advance_days(self):
        trip = self._make_request(
            date_start=Date.to_string(Date.today()),
            date_end=Date.to_string(Date.today() + timedelta(days=2)),
        )
        with self.assertRaises(UserError):
            trip.action_submit()

    def test_submit_succeeds_with_enough_advance_notice(self):
        trip = self._make_request()
        trip.action_submit()
        self.assertEqual(trip.state, "submitted")
        self.assertEqual(trip.current_step_name, "Direct Manager")
        # Default configuration: Direct Manager, Department Manager, CEO
        # (HR Review is automatic routing after CEO approval, not a step)
        self.assertEqual(len(trip.approval_line_ids), 3)

    # ------------------------------------------------------------
    # Rule 17: No overnight stay => reduced allowance (configurable factor)
    # ------------------------------------------------------------
    def test_overnight_stay_full_allowance(self):
        trip = self._make_request(distance_km=400, overnight_stay=True, basic_salary=15000)
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        self.assertEqual(trip.overnight_factor, 1.0)

    def test_no_overnight_stay_half_allowance(self):
        trip = self._make_request(distance_km=400, overnight_stay=False, basic_salary=15000)
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        self.assertEqual(trip.overnight_factor, 0.5)

    def test_no_overnight_factor_is_configurable(self):
        self.company.business_trip_no_overnight_factor = 0.75
        trip = self._make_request(distance_km=400, overnight_stay=False, basic_salary=15000)
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        self.assertEqual(trip.overnight_factor, 0.75)

    # ------------------------------------------------------------
    # Rule 13: Allowance percentage/min/max clamp
    # ------------------------------------------------------------
    def test_domestic_allowance_clamped_to_max(self):
        trip = self._make_request(distance_km=400, overnight_stay=True, basic_salary=15000)
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        # 15000 * 10% = 1500/day, but the domestic rule caps at SAR 500/day
        self.assertEqual(trip.base_daily_allowance, 500)

    # ------------------------------------------------------------
    # Rule 15: Transportation deduction
    # ------------------------------------------------------------
    def test_transportation_deduction_applied(self):
        trip = self._make_request(
            distance_km=400, overnight_stay=True, basic_salary=15000,
            need_transportation=True,
        )
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        self.assertGreater(trip.transportation_deduction, 0)
        self.assertEqual(trip.net_allowance, trip.gross_allowance - trip.transportation_deduction)

    def test_no_transportation_no_deduction(self):
        trip = self._make_request(
            distance_km=400, overnight_stay=True, basic_salary=15000,
            need_transportation=False,
        )
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        self.assertEqual(trip.transportation_deduction, 0)
        self.assertEqual(trip.net_allowance, trip.gross_allowance)

    # ------------------------------------------------------------
    # Rule 22: Requested advance cannot exceed net allowance
    # ------------------------------------------------------------
    def test_requested_advance_exceeds_allowance_blocked(self):
        trip = self._make_request(distance_km=400, overnight_stay=True, basic_salary=15000)
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        with self.assertRaises(ValidationError):
            trip.write({"advance_required": True, "requested_advance": trip.net_allowance + 1000})

    def test_requested_advance_within_allowance_allowed(self):
        trip = self._make_request(distance_km=400, overnight_stay=True, basic_salary=15000)
        trip.write({"state": "hr_review"})
        trip.action_calculate_allowance()
        trip.write({"advance_required": True, "requested_advance": trip.net_allowance / 2})
        self.assertTrue(trip.advance_required)

    # ------------------------------------------------------------
    # Rule 18: International extra travel days by flight duration
    # ------------------------------------------------------------
    def test_international_short_flight_adds_one_day(self):
        trip = self._make_request(
            destination_city="Dubai", destination_country_id=self.uae.id,
            flight_duration_hours=2.5,
        )
        self.assertEqual(trip.extra_days, 1)

    def test_international_long_flight_adds_two_days(self):
        trip = self._make_request(
            destination_city="Tokyo", destination_country_id=self.japan.id,
            flight_duration_hours=10,
        )
        self.assertEqual(trip.extra_days, 2)

    def test_domestic_trip_has_no_extra_days(self):
        trip = self._make_request(distance_km=400)
        self.assertEqual(trip.extra_days, 0)

    # ------------------------------------------------------------
    # Trip Dates - total days / overnight stays calc
    # ------------------------------------------------------------
    def test_total_days_and_overnight_count(self):
        trip = self._make_request(
            date_start=Date.to_string(Date.today() + timedelta(days=5)),
            date_end=Date.to_string(Date.today() + timedelta(days=8)),
            overnight_stay=True,
        )
        self.assertEqual(trip.total_days, 4)
        self.assertEqual(trip.overnight_count, 3)

    def test_no_overnight_count_when_no_overnight_stay(self):
        trip = self._make_request(overnight_stay=False)
        self.assertEqual(trip.overnight_count, 0)

    # ------------------------------------------------------------
    # Travel & Support Requirements checkboxes
    # ------------------------------------------------------------
    def test_travel_services_stored_correctly(self):
        trip = self._make_request(
            need_flight=True,
            need_transportation=True,
            need_visa=False,
            need_other=True,
            other_specify="Need a translator on-site",
        )
        self.assertTrue(trip.need_flight)
        self.assertTrue(trip.need_transportation)
        self.assertFalse(trip.need_visa)
        self.assertEqual(trip.other_specify, "Need a translator on-site")

    # ------------------------------------------------------------
    # Destination State/Province is domain-filtered by country
    # ------------------------------------------------------------
    def test_state_domain_matches_its_country(self):
        state = self.env["res.country.state"].search(
            [("country_id", "=", self.uae.id)], limit=1
        )
        if not state:
            state = self.env["res.country.state"].create(
                {"name": "Dubai Emirate", "code": "DU", "country_id": self.uae.id}
            )
        trip = self._make_request(
            destination_city="Dubai", destination_country_id=self.uae.id,
            destination_state_id=state.id,
        )
        self.assertEqual(trip.destination_state_id.country_id, self.uae)

    # ------------------------------------------------------------
    # Peak period cities: configurable comma-separated list (Settings)
    # ------------------------------------------------------------
    def test_peak_city_from_configured_list_drives_peak_period(self):
        # "Jeddah" is in the default business_trip_peak_cities list;
        # peak season defaults to June-August.
        trip = self._make_request(
            destination_city="Jeddah",
            date_start="2027-07-15",
            date_end="2027-07-18",
        )
        self.assertTrue(trip.is_peak_period)

    def test_non_peak_city_is_never_peak_period(self):
        trip = self._make_request(
            destination_city="Riyadh",
            date_start="2027-07-15",
            date_end="2027-07-18",
        )
        self.assertFalse(trip.is_peak_period)

    def test_peak_cities_list_is_configurable(self):
        self.company.business_trip_peak_cities = "Riyadh"
        trip = self._make_request(
            destination_city="Riyadh",
            date_start="2027-07-15",
            date_end="2027-07-18",
        )
        self.assertTrue(trip.is_peak_period)

    # ------------------------------------------------------------
    # Approval workflow: configurable steps, sequential, group-driven
    # ------------------------------------------------------------
    def test_approval_chain_moves_sequentially_through_all_steps(self):
        trip = self._make_request()
        trip.action_submit()
        self.assertEqual(trip.state, "submitted")
        self.assertEqual(trip.current_step_name, "Direct Manager")
        self.assertEqual(len(trip.approval_line_ids), 3)

        trip.action_approve()
        self.assertEqual(trip.state, "direct_manager_approved")
        self.assertEqual(trip.current_step_name, "Department Manager")

        trip.action_approve()
        self.assertEqual(trip.state, "department_manager_approved")
        self.assertEqual(trip.current_step_name, "CEO")

        # CEO is the last configured step: approving it routes straight to HR
        trip.action_approve()
        self.assertEqual(trip.state, "hr_review")

        for line in trip.approval_line_ids:
            self.assertEqual(line.state, "approved")
            self.assertTrue(line.approved_by)

    def test_approval_chain_uses_bilingual_approved_states(self):
        trip = self._make_request()
        trip.action_submit()
        trip.action_approve()
        state_labels = dict(trip._fields["state"].selection)
        self.assertEqual(trip.state, "direct_manager_approved")
        self.assertIn("Direct Manager", state_labels[trip.state])
        self.assertIn("المدير المباشر", state_labels[trip.state])

    def test_reject_stores_reason_and_stops_workflow(self):
        trip = self._make_request()
        trip.action_submit()
        trip.action_reject("Budget not approved for this quarter")
        self.assertEqual(trip.state, "rejected")
        self.assertEqual(trip.rejection_reason, "Budget not approved for this quarter")
        rejected_line = trip.approval_line_ids.filtered(lambda l: l.state == "rejected")
        self.assertTrue(rejected_line)

    def test_return_for_modification_stores_comment_and_allows_resubmit(self):
        trip = self._make_request()
        trip.action_submit()
        trip.action_return_for_modification("Please add more detail to objectives")
        self.assertEqual(trip.state, "returned")
        self.assertEqual(trip.return_comment, "Please add more detail to objectives")

        trip.action_resubmit()
        self.assertEqual(trip.state, "draft")

    def test_reason_wizard_requires_reason(self):
        trip = self._make_request()
        trip.action_submit()
        with self.assertRaises(Exception):
            self.env["business.trip.reason.wizard"].create(
                {"request_id": trip.id, "action_type": "reject", "reason": False}
            )

    def test_approval_step_config_is_used_and_editable(self):
        # Disable everything except a single group-based step, proving the
        # chain length and source are fully driven by configuration.
        steps = self.env["business.trip.approval.step"].search([])
        steps.write({"active": False})
        finance_group = self.env.ref("business_trip_request.group_business_trip_finance")
        self.env["business.trip.approval.step"].create({
            "name": "Finance Sign-off",
            "sequence": 5,
            "source": "group",
            "group_id": finance_group.id,
        })
        trip = self._make_request()
        trip.action_submit()
        self.assertEqual(len(trip.approval_line_ids), 1)
        self.assertEqual(trip.approval_line_ids.name, "Finance Sign-off")
        self.assertEqual(trip.approval_line_ids.approver_group_id, finance_group)
        self.assertEqual(trip.state, "submitted")
        self.assertEqual(trip.current_step_name, "Finance Sign-off")

        # A step name that isn't Direct Manager/Department Manager/CEO
        # falls back to the generic "pending_approval" state once approved
        # (here it's also the last step, so it's immediately routed to HR).
        trip.action_approve()
        self.assertEqual(trip.state, "hr_review")

        # restore steps for other tests in this class
        steps.write({"active": True})

    def test_unmapped_step_name_uses_pending_approval_fallback(self):
        # Two custom steps (neither named Direct Manager/Department
        # Manager/CEO): approving the first should leave the request on
        # the generic "pending_approval" fallback state while the second
        # step is still outstanding.
        steps = self.env["business.trip.approval.step"].search([])
        steps.write({"active": False})
        finance_group = self.env.ref("business_trip_request.group_business_trip_finance")
        hr_group = self.env.ref("business_trip_request.group_business_trip_hr")
        self.env["business.trip.approval.step"].create({
            "name": "Finance Sign-off", "sequence": 5,
            "source": "group", "group_id": finance_group.id,
        })
        self.env["business.trip.approval.step"].create({
            "name": "Second Sign-off", "sequence": 6,
            "source": "group", "group_id": hr_group.id,
        })
        trip = self._make_request()
        trip.action_submit()
        trip.action_approve()
        self.assertEqual(trip.state, "pending_approval")
        self.assertEqual(trip.current_step_name, "Second Sign-off")
        trip.action_approve()
        self.assertEqual(trip.state, "hr_review")
        steps.write({"active": True})

    # ------------------------------------------------------------
    # Post-approval lifecycle: Start/End Trip, Trip Report, HR report
    # review, Finance settlement, Transaction History
    # ------------------------------------------------------------
    def _approve_full_chain_to_hr_review(self, trip):
        trip.action_submit()
        for _dummy in range(len(trip.approval_line_ids)):
            trip.action_approve()
        self.assertEqual(trip.state, "hr_review")

    def test_full_post_approval_lifecycle_creates_transaction(self):
        trip = self._make_request(distance_km=400, overnight_stay=True, basic_salary=15000)
        self._approve_full_chain_to_hr_review(trip)

        trip.action_calculate_allowance()
        trip.action_approve_allowance()
        self.assertEqual(trip.state, "allowance_calculated")

        trip.action_start_trip()
        self.assertEqual(trip.state, "trip_in_progress")

        trip.action_end_trip()
        self.assertEqual(trip.state, "trip_report_required")

        trip.write({"work_summary": "Met the client and closed the deal."})
        trip.action_submit_trip_report()
        self.assertEqual(trip.state, "report_under_hr_review")
        self.assertEqual(trip.report_state, "submitted")

        trip.action_approve_report()
        self.assertEqual(trip.state, "pending_settlement")
        self.assertEqual(trip.report_state, "approved")

        trip.action_process_settlement()
        self.assertEqual(trip.state, "completed")
        self.assertEqual(trip.settlement_state, "processed")
        self.assertEqual(len(trip.transaction_ids), 1)
        self.assertEqual(trip.transaction_ids.transaction_type, "settlement")
        self.assertEqual(trip.transaction_ids.amount, trip.settlement_amount)

    def test_start_trip_blocked_before_ready_for_travel(self):
        trip = self._make_request()
        with self.assertRaises(UserError):
            trip.action_start_trip()

    def test_submit_trip_report_requires_work_summary(self):
        trip = self._make_request(distance_km=400, overnight_stay=True, basic_salary=15000)
        self._approve_full_chain_to_hr_review(trip)
        trip.action_calculate_allowance()
        trip.action_approve_allowance()
        trip.action_start_trip()
        trip.action_end_trip()
        with self.assertRaises(UserError):
            trip.action_submit_trip_report()

    def test_process_settlement_blocked_before_report_approved(self):
        trip = self._make_request(distance_km=400, overnight_stay=True, basic_salary=15000)
        self._approve_full_chain_to_hr_review(trip)
        trip.action_calculate_allowance()
        trip.action_approve_allowance()
        with self.assertRaises(UserError):
            trip.action_process_settlement()
