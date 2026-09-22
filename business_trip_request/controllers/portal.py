from odoo import http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class BusinessTripPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "business_trip_count" in counters:
            employee = request.env.user.employee_id
            values["business_trip_count"] = (
                request.env["business.trip.request"].search_count(
                    [("employee_id", "=", employee.id)]
                )
                if employee
                else 0
            )
        return values

    def _btr_get_searchbar_filters(self):
        return {
            "all": {"label": _("All"), "domain": []},
            "draft": {
                "label": _("Draft / Returned"),
                "domain": [("state", "in", ["draft", "returned"])],
            },
            "pending": {
                "label": _("Pending Approval"),
                "domain": [(
                    "state", "in",
                    ["submitted", "pending_direct_manager", "direct_manager_approved",
                     "pending_department_manager", "department_manager_approved",
                     "pending_ceo", "approved", "pending_approval", "hr_review"],
                )],
            },
            "in_progress": {
                "label": _("In Progress"),
                "domain": [(
                    "state", "in",
                    ["allowance_calculated", "trip_in_progress", "trip_report_required",
                     "report_under_hr_review", "pending_settlement"],
                )],
            },
            "completed": {"label": _("Completed"), "domain": [("state", "=", "completed")]},
            "rejected": {"label": _("Rejected"), "domain": [("state", "=", "rejected")]},
        }

    def _btr_get_state_badge(self):
        return {
            "draft": "secondary",
            "returned": "warning",
            "submitted": "secondary",
            "pending_direct_manager": "warning",
            "direct_manager_approved": "info",
            "pending_department_manager": "warning",
            "department_manager_approved": "info",
            "pending_ceo": "warning",
            "approved": "success",
            "pending_approval": "warning",
            "hr_review": "info",
            "allowance_calculated": "info",
            "trip_in_progress": "primary",
            "trip_report_required": "warning",
            "report_under_hr_review": "info",
            "pending_settlement": "info",
            "completed": "success",
            "rejected": "danger",
            "cancelled": "secondary",
        }

    def _btr_get_approval_badge(self):
        return {
            "pending": "secondary",
            "approved": "success",
            "rejected": "danger",
            "returned": "warning",
        }

    def _btr_check_access(self, request_id):
        trip = request.env["business.trip.request"].sudo().browse(request_id)
        if not trip.exists():
            raise MissingError(_("This request does not exist."))
        employee = request.env.user.employee_id
        if not employee or trip.employee_id.id != employee.id:
            raise AccessError(_("You do not have access to this request."))
        return trip

    def _btr_form_vals(self, kw, employee):
        def to_bool(key):
            return bool(kw.get(key))

        def to_float(key):
            try:
                return float(kw.get(key) or 0)
            except ValueError:
                return 0.0

        def to_int(key):
            try:
                return int(kw.get(key) or 0)
            except ValueError:
                return 0

        return {
            "employee_id": employee.id,
            "destination_city": kw.get("destination_city"),
            "destination_state_id": to_int("destination_state_id") or False,
            "destination_country_id": to_int("destination_country_id") or False,
            "distance_km": to_float("distance_km"),
            "purpose": kw.get("purpose"),
            "objectives": kw.get("objectives"),
            "date_start": kw.get("date_start") or False,
            "date_end": kw.get("date_end") or False,
            "overnight_stay": to_bool("overnight_stay"),
            "flight_duration_hours": to_float("flight_duration_hours"),
            "need_flight": to_bool("need_flight"),
            "need_transportation": to_bool("need_transportation"),
            "need_visa": to_bool("need_visa"),
            "need_other": to_bool("need_other"),
            "other_specify": kw.get("other_specify"),
            "combine_annual_leave": to_bool("combine_annual_leave"),
            "leave_start_date": kw.get("leave_start_date") or False,
            "leave_end_date": kw.get("leave_end_date") or False,
            "advance_required": to_bool("advance_required"),
            "requested_advance": to_float("requested_advance"),
            "payment_timing": kw.get("payment_timing") or "after_trip",
        }

    @http.route(
        ["/my/business-trips", "/my/business-trips/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_business_trips(self, page=1, sortby=None, filterby=None, **kw):
        values = self._prepare_portal_layout_values()
        employee = request.env.user.employee_id
        business_trip = request.env["business.trip.request"]
        domain = [("employee_id", "=", employee.id)] if employee else [("id", "=", 0)]

        searchbar_filters = self._btr_get_searchbar_filters()
        if not filterby or filterby not in searchbar_filters:
            filterby = "all"
        domain += searchbar_filters[filterby]["domain"]

        sortings = {
            "date": {"label": _("Newest"), "order": "create_date desc"},
            "name": {"label": _("Reference"), "order": "name desc"},
        }
        if not sortby or sortby not in sortings:
            sortby = "date"
        order = sortings[sortby]["order"]

        trip_count = business_trip.search_count(domain)
        pager = portal_pager(
            url="/my/business-trips",
            url_args={"sortby": sortby, "filterby": filterby},
            total=trip_count,
            page=page,
            step=self._items_per_page,
        )
        trips = business_trip.search(
            domain, order=order, limit=self._items_per_page, offset=pager["offset"]
        )

        base_domain = [("employee_id", "=", employee.id)] if employee else [("id", "=", 0)]
        stats = {
            "total": business_trip.search_count(base_domain),
            "draft": business_trip.search_count(
                base_domain + searchbar_filters["draft"]["domain"]
            ),
            "pending": business_trip.search_count(
                base_domain + searchbar_filters["pending"]["domain"]
            ),
            "in_progress": business_trip.search_count(
                base_domain + searchbar_filters["in_progress"]["domain"]
            ),
            "completed": business_trip.search_count(
                base_domain + searchbar_filters["completed"]["domain"]
            ),
            "rejected": business_trip.search_count(
                base_domain + searchbar_filters["rejected"]["domain"]
            ),
        }

        values.update(
            {
                "trips": trips,
                "stats": stats,
                "state_badge": self._btr_get_state_badge(),
                "page_name": "business_trip",
                "pager": pager,
                "default_url": "/my/business-trips",
                "searchbar_sortings": sortings,
                "sortby": sortby,
                "searchbar_filters": searchbar_filters,
                "filterby": filterby,
            }
        )
        return request.render(
            "business_trip_request.portal_my_business_trips", values
        )

    @http.route(
        ["/my/business-trips/new"],
        type="http",
        auth="user",
        website=True,
        methods=["GET", "POST"],
    )
    def portal_business_trip_new(self, **kw):
        employee = request.env.user.employee_id
        error = {}
        if not employee:
            error["general"] = _(
                "Your user account is not linked to an employee record. "
                "Please contact HR."
            )
        elif request.httprequest.method == "POST":
            try:
                vals = self._btr_form_vals(kw, employee)
                trip = request.env["business.trip.request"].sudo().create(vals)
                if kw.get("submit_now"):
                    trip.sudo().action_submit()
                return request.redirect("/my/business-trips/%s" % trip.id)
            except Exception as exc:  # noqa: BLE001 - surfaced to the portal form
                error["general"] = str(exc)
        values = {
            "employee": employee,
            "countries": request.env["res.country"].sudo().search([]),
            "states": request.env["res.country.state"].sudo().search([]),
            "error": error,
            "formdata": kw,
            "page_name": "business_trip_new",
        }
        return request.render(
            "business_trip_request.portal_business_trip_form", values
        )

    @http.route(["/my/business-trips/<int:request_id>"], type="http", auth="user", website=True)
    def portal_business_trip_detail(self, request_id, **kw):
        trip = self._btr_check_access(request_id)
        values = {
            "trip": trip,
            "state_badge": self._btr_get_state_badge(),
            "approval_badge": self._btr_get_approval_badge(),
            "page_name": "business_trip",
            "error": kw.get("error"),
        }
        return request.render(
            "business_trip_request.portal_business_trip_detail", values
        )

    @http.route(
        ["/my/business-trips/<int:request_id>/submit"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_business_trip_submit(self, request_id, **kw):
        trip = self._btr_check_access(request_id)
        try:
            trip.sudo().action_submit()
        except Exception as exc:  # noqa: BLE001 - surfaced to the portal page
            return request.redirect(
                "/my/business-trips/%s?error=%s" % (request_id, str(exc))
            )
        return request.redirect("/my/business-trips/%s" % request_id)

    @http.route(
        ["/my/business-trips/<int:request_id>/resubmit"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_business_trip_resubmit(self, request_id, **kw):
        trip = self._btr_check_access(request_id)
        trip.sudo().action_resubmit()
        return request.redirect("/my/business-trips/%s" % request_id)

    @http.route(
        ["/my/business-trips/<int:request_id>/start"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_business_trip_start(self, request_id, **kw):
        trip = self._btr_check_access(request_id)
        try:
            trip.sudo().action_start_trip()
        except Exception as exc:  # noqa: BLE001 - surfaced to the portal page
            return request.redirect(
                "/my/business-trips/%s?error=%s" % (request_id, str(exc))
            )
        return request.redirect("/my/business-trips/%s" % request_id)

    @http.route(
        ["/my/business-trips/<int:request_id>/end"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_business_trip_end(self, request_id, **kw):
        trip = self._btr_check_access(request_id)
        try:
            trip.sudo().action_end_trip()
        except Exception as exc:  # noqa: BLE001 - surfaced to the portal page
            return request.redirect(
                "/my/business-trips/%s?error=%s" % (request_id, str(exc))
            )
        return request.redirect("/my/business-trips/%s" % request_id)

    @http.route(
        ["/my/business-trips/<int:request_id>/report"],
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
    )
    def portal_business_trip_report(self, request_id, **kw):
        trip = self._btr_check_access(request_id)
        trip.sudo().write(
            {
                "actual_date_start": kw.get("actual_date_start") or False,
                "actual_date_end": kw.get("actual_date_end") or False,
                "actual_overnight_count": int(kw.get("actual_overnight_count") or 0),
                "work_summary": kw.get("work_summary"),
                "objectives_achieved": kw.get("objectives_achieved"),
                "report_notes": kw.get("report_notes"),
                "additional_days": int(kw.get("additional_days") or 0),
                "additional_days_justification": kw.get("additional_days_justification"),
            }
        )
        try:
            trip.sudo().action_submit_trip_report()
        except Exception as exc:  # noqa: BLE001 - surfaced to the portal page
            return request.redirect(
                "/my/business-trips/%s?error=%s" % (request_id, str(exc))
            )
        return request.redirect("/my/business-trips/%s" % request_id)
