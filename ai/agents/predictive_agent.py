"""Agent 4: Predictive Agent
Predicts future resource demand using time series forecasting.
"""
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from agents.base_agent import BaseAgent
from models.db import Appointment, AppointmentStatus, Bed, BedStatus


class PredictiveAgent(BaseAgent):
    name = "predictive"
    description = "Predicts future resource demand"

    def run(self) -> dict:
        """Predict patient volume and resource needs for the next week."""
        now = datetime.utcnow()
        # Analyze last 30 days of appointments
        thirty_days_ago = now - timedelta(days=30)

        past_appointments = (
            self.db.query(Appointment)
            .filter(Appointment.date_time >= thirty_days_ago, Appointment.date_time < now)
            .all()
        )

        # Count appointments per day of week
        day_counts = Counter()
        daily_totals = Counter()
        for appt in past_appointments:
            day_counts[appt.date_time.weekday()] += 1
            daily_totals[appt.date_time.date()] += 1

        # Calculate averages per day of week
        weeks_analyzed = max(1, (now - thirty_days_ago).days // 7)
        avg_per_day = {}
        for day in range(7):
            avg_per_day[day] = round(day_counts.get(day, 0) / weeks_analyzed, 1)

        # Predict next 7 days
        predictions = []
        for i in range(1, 8):
            future_date = (now + timedelta(days=i)).date()
            day_of_week = future_date.weekday()
            predicted = avg_per_day.get(day_of_week, 0)

            # Add some variance
            predicted_with_variance = max(0, predicted + np.random.normal(0, max(1, predicted * 0.1)))

            predictions.append({
                "date": future_date.isoformat(),
                "day_name": ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"][day_of_week],
                "predicted_patients": round(predicted_with_variance),
                "confidence": 0.8 if len(past_appointments) > 50 else 0.5,
            })

        # Find peak days
        peak_days = sorted(predictions, key=lambda x: x["predicted_patients"], reverse=True)[:3]

        # Bed demand prediction
        beds = self.db.query(Bed).all()
        total_beds = len(beds)
        occupied = sum(1 for b in beds if b.status == BedStatus.OCCUPIED)
        current_rate = occupied / total_beds if total_beds > 0 else 0

        # Simple trend: if occupancy is growing, predict higher
        trend = "stabil"
        if current_rate > 0.7:
            trend = "crescător"
        elif current_rate < 0.3:
            trend = "descrescător"

        suggestions = []
        if any(p["predicted_patients"] > 20 for p in predictions):
            suggestions.append("Se anticipează zile aglomerate. Asigurați personal suplimentar.")
        if current_rate > 0.7:
            suggestions.append(f"Ocuparea actuală ({round(current_rate*100)}%) sugerează necesitatea de paturi suplimentare.")

        result = {
            "predictions": predictions,
            "peak_days": peak_days,
            "trend": trend,
            "current_bed_occupancy": round(current_rate * 100, 1),
            "avg_daily_patients": round(sum(daily_totals.values()) / max(1, len(daily_totals)), 1),
            "suggestions": suggestions,
        }

        self.log_action("prediction_complete", result)
        return result
