#!/usr/bin/env python3
"""Entry point for the Louvois Salary CLI project."""

import json
import sys
import time
from datetime import datetime


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def fmt_amount(value: float) -> str:
    return f"{value:.2f}"


def lookup_band_allowance(commute_km, bands):
    try:
        km = float(commute_km)
    except (TypeError, ValueError):
        return None
    if km <= 0:
        return None
    for band in sorted(bands or [], key=lambda b: b.get("max_km", 0)):
        max_km = band.get("max_km")
        if max_km is None:
            continue
        if km <= max_km:
            return band.get("allowance", 0)
    return None


def main() -> None:
    # Track CLI runtime in seconds.
    start_time = time.perf_counter()
    # Very simple CLI: optionally filter by employee id (e.g., E001)
    target_id = None
    try:
        if len(sys.argv) > 1:
            target_id = sys.argv[1]

        employees = load_json("data/employees.json")
        rules = load_json("data/rules.json")
        lookup_tables = load_json("data/lookup_table.json")
        missions = load_json("data/missions.json")

        # Base salary table for R001 (rank -> amount)
        base_salary_table = lookup_tables.get("base_salary_table", {})

        # Find R001 rule
        rule_r001 = None
        for rule in rules:
            if rule.get("id") == "R001":
                rule_r001 = rule

        if rule_r001 is None:
            print("R001 not found in data/rules.json")
            return

        print(
            "id,name,rank,promotion_date,new_rank,months_in_service,base_salary_raw,base_salary,"
            "seniority_allowance,acting_allowance,"
            "commute_allowance,selected_housing_allowance,selected_transport_allowance,"
            "night_allowance,weekend_allowance,holiday_allowance,overtime_allowance,"
            "call_back_allowance,standby_allowance,training_allowance,"
            "per_diem_domestic,per_diem_international,hazard_allowance,"
            "combat_allowance,sea_duty_allowance,joint_mission_bonus,"
            "per_diem_recovery,cancel_compensation,"
            "housing_allowance,barracks_deduction,meal_deduction,special_meal_allowance,"
            "fatigue_multiplier,total_base"
        )

        # Apply R001 to employees
        for emp in employees:
            if target_id is not None and emp.get("id") != target_id:
                continue
            rank = emp.get("rank")
            base_salary_raw = 0
            if rank in base_salary_table:
                base_salary_raw = base_salary_table[rank]
            # R006: pro-rate base salary in promotion month
            promotion_date = emp.get("promotion_date")
            new_rank = emp.get("new_rank")
            if promotion_date and new_rank:
                try:
                    promotion_day = datetime.strptime(
                        promotion_date, "%Y-%m-%d"
                    ).day
                except ValueError:
                    promotion_day = None
                if promotion_day is not None:
                    days_in_month = (
                        lookup_tables.get("payroll_period", {}).get(
                            "days_in_month", 30
                        )
                    )
                    old_days = max(promotion_day - 1, 0)
                    new_days = max(days_in_month - old_days, 0)
                    new_rank_salary = base_salary_table.get(new_rank, base_salary_raw)
                    base_salary_raw = (
                        base_salary_raw * old_days / days_in_month
                        + new_rank_salary * new_days / days_in_month
                    )
            # R003: probation reduction for base salary
            months_in_service = emp.get("months_in_service", 0)
            probation = lookup_tables.get("probation", {})
            probation_months = probation.get("probation_months", 6)
            probation_factor = probation.get("probation_factor", 0.8)
            base_salary = base_salary_raw
            if months_in_service < probation_months:
                base_salary = base_salary_raw * probation_factor
            # R002: seniority allowance (years * base_salary * rate, capped)
            seniority_years = emp.get("seniority_years", 0)
            seniority = lookup_tables.get("seniority_allowance", {})
            seniority_rate = seniority.get("seniority_rate", 0.02)
            seniority_cap = seniority.get("seniority_cap", 800)
            seniority_allowance = 0
            if seniority_years > 0:
                seniority_allowance = base_salary * seniority_rate * seniority_years
                if seniority_allowance > seniority_cap:
                    seniority_allowance = seniority_cap
            # R004: acting allowance (days * per-day, if over threshold)
            acting_days = emp.get("acting_days", 0)
            acting_cfg = lookup_tables.get("acting_allowance", {})
            acting_threshold = acting_cfg.get("n", 0)
            acting_per_day = acting_cfg.get("acting_allowance_per_day", 0)
            acting_allowance = 0
            if acting_days > acting_threshold:
                acting_allowance = acting_days * acting_per_day
            # R005: mutual exclusive allowances (pick max within each group)
            housing_allowance = emp.get("housing_allowance", 0)
            barracks_subsidy = emp.get("barracks_subsidy", 0)
            selected_housing_allowance = max(housing_allowance, barracks_subsidy)
            # R401: commute allowance by distance band
            commute_allowance = emp.get("commute_allowance", 0)
            commute_band = lookup_tables.get("commute_allowance_band", [])
            commute_km = emp.get("commute_km")
            band_allowance = lookup_band_allowance(commute_km, commute_band)
            if band_allowance is not None:
                commute_allowance = band_allowance
            official_vehicle_allowance = emp.get("official_vehicle_allowance", 0)
            selected_transport_allowance = max(
                commute_allowance, official_vehicle_allowance
            )
            # R101: night duty allowance
            night_hours = emp.get("night_hours", 0)
            night_rate = lookup_tables.get("night_allowance", {}).get("night_rate", 0)
            night_allowance = night_hours * night_rate
            # R102: weekend duty allowance (stack or max with night)
            weekend_hours = emp.get("weekend_hours", 0)
            weekend_cfg = lookup_tables.get("weekend_allowance", {})
            weekend_rate = weekend_cfg.get("weekend_rate", 0)
            combine_with_night = weekend_cfg.get("combine_with_night", "stack")
            weekend_allowance = weekend_hours * weekend_rate
            if combine_with_night == "max":
                if weekend_allowance < night_allowance:
                    weekend_allowance = 0
            # R103: holiday duty allowance
            holiday_hours = emp.get("holiday_hours", 0)
            holiday_rate = lookup_tables.get("holiday_allowance", {}).get(
                "holiday_rate", 0
            )
            holiday_allowance = holiday_hours * holiday_rate
            # R104: overtime allowance
            daily_hours = emp.get("daily_hours", 0)
            overtime_cfg = lookup_tables.get("overtime", {})
            daily_standard_hours = overtime_cfg.get("daily_standard_hours", 8)
            overtime_rate = overtime_cfg.get("overtime_rate", 0)
            overtime_hours = daily_hours - daily_standard_hours
            if overtime_hours < 0:
                overtime_hours = 0
            overtime_allowance = overtime_hours * overtime_rate
            # R106: call-back allowance
            call_back = emp.get("call_back", False)
            call_back_count = emp.get("call_back_count", 0)
            call_back_flat = lookup_tables.get("call_back", {}).get(
                "call_back_flat", 0
            )
            call_back_allowance = 0
            if call_back:
                call_back_allowance = call_back_count * call_back_flat
            # R107: standby allowance (skip if called in)
            standby_hours = emp.get("standby_hours", 0)
            called_in = emp.get("called_in", False)
            standby_rate = lookup_tables.get("standby", {}).get("standby_rate", 0)
            standby_allowance = 0
            if standby_hours > 0 and not called_in:
                standby_allowance = standby_hours * standby_rate
            # R201/R202: per diem by mission zone/city and days
            per_diem_domestic = 0
            per_diem_international = 0
            per_diem_domestic_table = lookup_tables.get("per_diem_domestic", {})
            per_diem_international_table = lookup_tables.get("per_diem_international", {})
            emp_unit = emp.get("unit")
            training_in_hazard_zone = False
            hazard_allowance = 0
            hazard_cfg = lookup_tables.get("hazard", {})
            hazard_rate = hazard_cfg.get("hazard_rate", 0)
            hazard_flat = hazard_cfg.get("hazard_flat", 0)
            combat_cfg = lookup_tables.get("combat", {})
            combat_allowance = 0
            combat_cap = combat_cfg.get("combat_cap", 0)
            sea_cfg = lookup_tables.get("sea_duty", {})
            sea_days_threshold = sea_cfg.get("sea_days_threshold", 0)
            sea_duty_bonus_per_day = sea_cfg.get("sea_duty_bonus_per_day", 0)
            sea_duty_allowance = 0
            joint_mission_bonus = 0
            joint_cfg = lookup_tables.get("joint_mission", {})
            per_diem_recovery = 0
            default_prepaid = lookup_tables.get("prepaid", {}).get(
                "default_prepaid_amount", 0
            )
            cancel_compensation = 0
            cancel_cfg = lookup_tables.get("cancel", {})
            cancel_threshold_hours = cancel_cfg.get("cancel_threshold_hours", 0)
            cancel_compensation_flat = cancel_cfg.get("cancel_compensation_flat", 0)
            for m in missions:
                if m.get("unit") != emp_unit:
                    continue
                trip_days = m.get("trip_days", 0)
                zone = m.get("domestic_zone")
                per_day_domestic = per_diem_domestic_table.get(zone, 0)
                per_diem_domestic += trip_days * per_day_domestic
                country_city = m.get("country_city")
                per_day_intl = per_diem_international_table.get(country_city, 0)
                exchange_rate = m.get("exchange_rate", 1)
                per_diem_international += trip_days * per_day_intl * exchange_rate
                if m.get("hazard_zone") is True:
                    training_in_hazard_zone = True
                    daily_hazard = max(base_salary * hazard_rate, hazard_flat)
                    hazard_allowance += daily_hazard * trip_days
                if m.get("mission_type") == "combat":
                    combat_allowance += combat_cfg.get("combat_allowance", 0)
                sea_days = m.get("sea_days", 0)
                if sea_days >= sea_days_threshold:
                    sea_duty_allowance += sea_days * sea_duty_bonus_per_day
                if m.get("joint_mission") is True:
                    joint_mission_bonus += joint_cfg.get("joint_mission_bonus", 0)
                planned_days = m.get("planned_days", trip_days)
                actual_days = m.get("actual_days", trip_days)
                if actual_days < planned_days:
                    per_diem_recovery += default_prepaid
                cancel_hours_before = m.get("cancel_hours_before")
                if cancel_hours_before is not None:
                    if cancel_hours_before <= cancel_threshold_hours:
                        cancel_compensation += cancel_compensation_flat
            if combat_cap > 0:
                combined_combat = hazard_allowance + combat_allowance
                if combined_combat > combat_cap:
                    combat_allowance = max(combat_cap - hazard_allowance, 0)
            # R108: training day allowance (skip if in hazard zone)
            training_days = emp.get("training_days", 0)
            training_rate = lookup_tables.get("training", {}).get(
                "training_day_allowance", 0
            )
            training_allowance = 0
            if training_days > 0 and not training_in_hazard_zone:
                training_allowance = training_days * training_rate
            # R301: housing allowance (if no barracks)
            housing_allowance = 0
            unit_map = {}
            for u in load_json("data/units.json"):
                unit_map[u.get("id")] = u
            unit = unit_map.get(emp.get("unit"), {})
            barracks_provided = unit.get("barracks_provided", False)
            city = unit.get("location")
            if not barracks_provided and city:
                housing_table = lookup_tables.get("housing_allowance_table", {})
                rank_table = housing_table.get(city, {})
                housing_allowance = rank_table.get(rank, 0)
            # R302: housing cap (self-pay for excess)
            housing_cap = lookup_tables.get("housing_cap")
            if housing_cap is not None and housing_cap > 0:
                if housing_allowance > housing_cap:
                    housing_allowance = housing_cap
            # R303: barracks fee deduction (if barracks provided)
            barracks_fee = lookup_tables.get("barracks_fee", 0)
            barracks_deduction = 0
            if barracks_provided:
                barracks_deduction = barracks_fee
            # R304: meal deduction (if meals provided)
            meals_provided = unit.get("meals_provided", False)
            meal_deduction = 0
            if meals_provided:
                meal_deduction = lookup_tables.get("meal_deduction", 0)
            # R305: special meal allowance (if eligible)
            special_meal_allowance = 0
            if emp.get("special_meal_eligible", False):
                special_meal_allowance = lookup_tables.get(
                    "special_meal_allowance", 0
                )
            # R105: fatigue multiplier (applied to duty allowances)
            fatigue_cfg = lookup_tables.get("fatigue", {})
            streak_threshold = fatigue_cfg.get("streak_threshold", 0)
            fatigue_multiplier = fatigue_cfg.get("fatigue_multiplier", 1)
            streak_days = emp.get("streak_days", 0)
            applied_multiplier = 1
            if streak_days >= streak_threshold:
                applied_multiplier = fatigue_multiplier
            night_allowance *= applied_multiplier
            weekend_allowance *= applied_multiplier
            holiday_allowance *= applied_multiplier
            overtime_allowance *= applied_multiplier
            total_base = (
                base_salary
                + seniority_allowance
                + acting_allowance
                + selected_housing_allowance
                + selected_transport_allowance
                + night_allowance
                + weekend_allowance
                + holiday_allowance
                + overtime_allowance
                + call_back_allowance
                + standby_allowance
                + training_allowance
                + per_diem_domestic
                + per_diem_international
                + hazard_allowance
                + combat_allowance
                + sea_duty_allowance
                + joint_mission_bonus
                - per_diem_recovery
                + cancel_compensation
                + housing_allowance
                - barracks_deduction
                - meal_deduction
                + special_meal_allowance
            )
            print(
                f"{emp.get('id')},"
                f"{emp.get('name')},"
                f"{rank},"
                f"{promotion_date},"
                f"{new_rank},"
                f"{months_in_service},"
                f"{fmt_amount(base_salary_raw)},"
                f"{fmt_amount(base_salary)},"
                f"{fmt_amount(seniority_allowance)},"
                f"{fmt_amount(acting_allowance)},"
                f"{fmt_amount(commute_allowance)},"
                f"{fmt_amount(selected_housing_allowance)},"
                f"{fmt_amount(selected_transport_allowance)},"
                f"{fmt_amount(night_allowance)},"
                f"{fmt_amount(weekend_allowance)},"
                f"{fmt_amount(holiday_allowance)},"
                f"{fmt_amount(overtime_allowance)},"
                f"{fmt_amount(call_back_allowance)},"
                f"{fmt_amount(standby_allowance)},"
                f"{fmt_amount(training_allowance)},"
                f"{fmt_amount(per_diem_domestic)},"
                f"{fmt_amount(per_diem_international)},"
                f"{fmt_amount(hazard_allowance)},"
                f"{fmt_amount(combat_allowance)},"
                f"{fmt_amount(sea_duty_allowance)},"
                f"{fmt_amount(joint_mission_bonus)},"
                f"{fmt_amount(per_diem_recovery)},"
                f"{fmt_amount(cancel_compensation)},"
                f"{fmt_amount(housing_allowance)},"
                f"{fmt_amount(barracks_deduction)},"
                f"{fmt_amount(meal_deduction)},"
                f"{fmt_amount(special_meal_allowance)},"
                f"{fmt_amount(applied_multiplier)},"
                f"{fmt_amount(total_base)}"
            )
    finally:
        elapsed = time.perf_counter() - start_time
        print(f"runtime_seconds={elapsed:.4f}")


if __name__ == "__main__":
    main()
