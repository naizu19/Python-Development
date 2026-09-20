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

        cls.allowance_rule_model = cls.env["business.trip.allowance.rule"]

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
    # Rule: Domestic vs International detection (Section 3.A)
    # ------------------------------------------------------------
    def test_domestic_detection(self):
        trip = self._make_request(
            destination_country_id=self.saudi.id, distance_km=400
        )
        self.assertEqual(trip.trip_type, "domestic")
        self.assertTrue(trip.is_formal_assignment)

    def test_international_detection(self):
        trip = self._make_request(
            destination_city="Dubai", destination_country_id=self.uae.id
        )
        self.assertEqual(trip.trip_type, "international")

    # ------------------------------------------------------------
    # Rule 1: Distance < 300km is not a formal assignment
    # ------------------------------------------------------------
    def test_short_domestic_trip_below_300km(self):
        trip = self._make_request(distance_km=120)
        self.assertFalse(trip.is_formal_assignment)
        self.assertGreater(trip.short_trip_daily_amount, 0)

    def test_domestic_trip_above_300km_is_formal(self):
        trip = self._make_request(distance_km=350)
        self.assertTrue(trip.is_formal_assignment)
        self.assertEqual(trip.short_trip_daily_amount, 0)

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
        self.assertEqual(trip.state, "pending_direct_manager")
        self.assertEqual(len(trip.approval_line_ids), 3)

    # ------------------------------------------------------------
    # Rule 17: No overnight stay => 50% allowance
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
