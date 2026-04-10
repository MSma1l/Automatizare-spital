"""Agent 5: Recommendation Agent
Provides personalized recommendations for doctors based on patient history.
"""
from datetime import datetime, timedelta
from collections import Counter
from agents.base_agent import BaseAgent
from models.db import (
    Appointment, AppointmentStatus, Doctor, Patient, User, UserRole,
)


class RecommendationAgent(BaseAgent):
    name = "recommendation"
    description = "Personalized recommendations for doctors"

    def run(self) -> dict:
        """Generate recommendations for all active doctors."""
        doctors = (
            self.db.query(Doctor)
            .join(User, Doctor.user_id == User.id)
            .filter(User.is_active == True)
            .all()
        )

        all_recommendations = []

        for doctor in doctors:
            recs = self._generate_doctor_recommendations(doctor)
            all_recommendations.extend(recs)

        result = {
            "total_recommendations": len(all_recommendations),
            "recommendations": all_recommendations,
        }

        self.log_action("recommendations_generated", {"count": len(all_recommendations)})
        return result

    def _generate_doctor_recommendations(self, doctor: Doctor) -> list[dict]:
        recs = []
        now = datetime.utcnow()

        # Find patients who haven't visited in a long time but had ongoing conditions
        patient_ids = (
            self.db.query(Appointment.patient_id)
            .filter(Appointment.doctor_id == doctor.id)
            .distinct()
            .all()
        )

        for (patient_id,) in patient_ids:
            last_visit = (
                self.db.query(Appointment)
                .filter(
                    Appointment.doctor_id == doctor.id,
                    Appointment.patient_id == patient_id,
                    Appointment.status == AppointmentStatus.COMPLETED,
                )
                .order_by(Appointment.date_time.desc())
                .first()
            )

            if last_visit:
                days_since = (now - last_visit.date_time).days
                patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
                patient_name = f"{patient.first_name} {patient.last_name}" if patient else f"Pacient #{patient_id}"

                # Patient hasn't visited in 90+ days - suggest follow-up
                if days_since > 90:
                    rec = {
                        "doctor_id": doctor.id,
                        "patient_id": patient_id,
                        "type": "follow_up",
                        "message": f"Pacientul {patient_name} nu a mai avut o consultație de {days_since} zile. Recomandare: programare control.",
                        "priority": "normal",
                    }
                    recs.append(rec)
                    self.create_recommendation(
                        doctor.user_id,
                        rec["message"],
                        priority=rec["priority"],
                        data={"patient_id": patient_id, "days_since_visit": days_since},
                    )

                # Patient with many cancelled appointments - attention needed
                cancelled_count = (
                    self.db.query(Appointment)
                    .filter(
                        Appointment.patient_id == patient_id,
                        Appointment.doctor_id == doctor.id,
                        Appointment.status == AppointmentStatus.CANCELLED,
                    )
                    .count()
                )
                if cancelled_count >= 3:
                    rec = {
                        "doctor_id": doctor.id,
                        "patient_id": patient_id,
                        "type": "attention",
                        "message": f"Pacientul {patient_name} a anulat {cancelled_count} programări. Poate necesita contactare telefonică.",
                        "priority": "high",
                    }
                    recs.append(rec)
                    self.create_recommendation(
                        doctor.user_id,
                        rec["message"],
                        priority="high",
                        data={"patient_id": patient_id, "cancelled_count": cancelled_count},
                    )

        return recs

    def get_doctor_recommendations(self, doctor_id: int) -> list[dict]:
        """Get recommendations for a specific doctor."""
        doctor = self.db.query(Doctor).filter(Doctor.id == doctor_id).first()
        if not doctor:
            return []
        return self._generate_doctor_recommendations(doctor)
