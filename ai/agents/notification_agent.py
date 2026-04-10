"""Agent 6: Notification Agent
Manages all system notifications with priority queue.
"""
from datetime import datetime, timedelta
from agents.base_agent import BaseAgent
from models.db import (
    Appointment, AppointmentStatus, Doctor, Patient, User, Notification,
)


class NotificationAgent(BaseAgent):
    name = "notification"
    description = "Manages system notifications"

    def run(self) -> dict:
        """Check for pending notifications to send."""
        sent = []

        # Appointment reminders (24h before)
        sent.extend(self._send_appointment_reminders())

        # Pending appointment alerts for doctors
        sent.extend(self._send_pending_alerts())

        result = {
            "notifications_sent": len(sent),
            "details": sent,
        }

        self.log_action("notification_run", result)
        return result

    def _send_appointment_reminders(self) -> list[dict]:
        """Send reminders for appointments happening in the next 24 hours."""
        now = datetime.utcnow()
        tomorrow = now + timedelta(hours=24)

        upcoming = (
            self.db.query(Appointment)
            .filter(
                Appointment.date_time.between(now, tomorrow),
                Appointment.status == AppointmentStatus.CONFIRMED,
            )
            .all()
        )

        sent = []
        for appt in upcoming:
            # Check if reminder already sent
            existing = (
                self.db.query(Notification)
                .filter(
                    Notification.user_id == self._get_patient_user_id(appt.patient_id),
                    Notification.title == "Reminder Programare",
                    Notification.created_at >= now - timedelta(hours=24),
                )
                .first()
            )
            if existing:
                continue

            patient = self.db.query(Patient).filter(Patient.id == appt.patient_id).first()
            doctor = self.db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()

            if patient and doctor:
                time_str = appt.date_time.strftime("%d.%m.%Y la %H:%M")
                # Notify patient
                notif = Notification(
                    user_id=patient.user_id,
                    title="Reminder Programare",
                    message=f"Aveți o programare cu Dr. {doctor.first_name} {doctor.last_name} mâine, {time_str}.",
                    type="appointment",
                    created_at=now,
                )
                self.db.add(notif)
                sent.append({"type": "reminder", "patient_id": patient.id, "appointment_id": appt.id})

        self.db.commit()
        return sent

    def _send_pending_alerts(self) -> list[dict]:
        """Alert doctors about unconfirmed appointments."""
        now = datetime.utcnow()
        soon = now + timedelta(hours=48)

        pending = (
            self.db.query(Appointment)
            .filter(
                Appointment.date_time.between(now, soon),
                Appointment.status == AppointmentStatus.PENDING,
            )
            .all()
        )

        sent = []
        for appt in pending:
            doctor = self.db.query(Doctor).filter(Doctor.id == appt.doctor_id).first()
            patient = self.db.query(Patient).filter(Patient.id == appt.patient_id).first()

            if doctor and patient:
                existing = (
                    self.db.query(Notification)
                    .filter(
                        Notification.user_id == doctor.user_id,
                        Notification.title == "Programare neconfirmată",
                        Notification.created_at >= now - timedelta(hours=12),
                    )
                    .first()
                )
                if existing:
                    continue

                notif = Notification(
                    user_id=doctor.user_id,
                    title="Programare neconfirmată",
                    message=f"Programarea cu {patient.first_name} {patient.last_name} pe {appt.date_time.strftime('%d.%m.%Y %H:%M')} nu este confirmată.",
                    type="warning",
                    created_at=now,
                )
                self.db.add(notif)
                sent.append({"type": "pending_alert", "doctor_id": doctor.id, "appointment_id": appt.id})

        self.db.commit()
        return sent

    def _get_patient_user_id(self, patient_id: int) -> int | None:
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        return patient.user_id if patient else None
