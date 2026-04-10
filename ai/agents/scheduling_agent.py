"""Agent 2: Scheduling Agent
Optimizes appointment scheduling using ML + conflict detection.
"""
from datetime import datetime, timedelta
from sqlalchemy import and_
from agents.base_agent import BaseAgent
from models.db import Appointment, AppointmentStatus, Doctor


class SchedulingAgent(BaseAgent):
    name = "scheduling"
    description = "Optimizes appointment scheduling"

    def run(self) -> dict:
        """Analyze scheduling and detect conflicts."""
        now = datetime.utcnow()
        upcoming = (
            self.db.query(Appointment)
            .filter(
                Appointment.date_time >= now,
                Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
            )
            .order_by(Appointment.date_time)
            .all()
        )

        conflicts = []
        suggestions = []

        # Detect conflicts: same doctor, overlapping time
        doctor_appts: dict[int, list] = {}
        for appt in upcoming:
            if appt.doctor_id not in doctor_appts:
                doctor_appts[appt.doctor_id] = []
            doctor_appts[appt.doctor_id].append(appt)

        for doctor_id, appts in doctor_appts.items():
            appts.sort(key=lambda a: a.date_time)
            for i in range(len(appts) - 1):
                end_time = appts[i].date_time + timedelta(minutes=appts[i].duration_minutes)
                if end_time > appts[i + 1].date_time:
                    conflicts.append({
                        "doctor_id": doctor_id,
                        "appointment_1": appts[i].id,
                        "appointment_2": appts[i + 1].id,
                        "overlap_minutes": int((end_time - appts[i + 1].date_time).total_seconds() / 60),
                    })

        # Find overloaded doctors (more than 8 appointments per day)
        from collections import Counter
        daily_counts: dict[int, Counter] = {}
        for appt in upcoming:
            date_key = appt.date_time.date()
            if appt.doctor_id not in daily_counts:
                daily_counts[appt.doctor_id] = Counter()
            daily_counts[appt.doctor_id][date_key] += 1

        overloaded = []
        for doctor_id, counts in daily_counts.items():
            for day, count in counts.items():
                if count > 8:
                    doctor = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
                    overloaded.append({
                        "doctor_id": doctor_id,
                        "doctor_name": f"Dr. {doctor.first_name} {doctor.last_name}" if doctor else str(doctor_id),
                        "date": day.isoformat(),
                        "count": count,
                    })
                    suggestions.append(
                        f"Dr. {doctor.first_name} {doctor.last_name} are {count} programări pe {day}. Redistribuiți."
                    )

        if conflicts:
            suggestions.append(f"Detectate {len(conflicts)} conflicte de programare. Verificați și redistribuiți.")

        result = {
            "upcoming_count": len(upcoming),
            "conflicts": conflicts,
            "overloaded_doctors": overloaded,
            "suggestions": suggestions,
        }

        self.log_action("scheduling_analysis", result)
        return result

    def suggest_best_slot(self, doctor_id: int, date: datetime, duration: int = 30) -> list[str]:
        """Suggest best available time slots for a doctor on a given date."""
        start_of_day = datetime.combine(date.date(), datetime.min.time()).replace(hour=8)
        end_of_day = datetime.combine(date.date(), datetime.min.time()).replace(hour=18)

        existing = (
            self.db.query(Appointment)
            .filter(
                Appointment.doctor_id == doctor_id,
                Appointment.date_time >= start_of_day,
                Appointment.date_time < end_of_day,
                Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
            )
            .all()
        )

        booked_ranges = []
        for appt in existing:
            booked_ranges.append((appt.date_time, appt.date_time + timedelta(minutes=appt.duration_minutes)))

        available = []
        current = start_of_day
        while current + timedelta(minutes=duration) <= end_of_day:
            slot_end = current + timedelta(minutes=duration)
            is_free = all(not (current < end and slot_end > start) for start, end in booked_ranges)
            if is_free:
                available.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)

        return available
