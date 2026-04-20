"""Agent 3: Monitoring Agent
Monitors resource status in real-time using rule-based + anomaly detection.
"""
from datetime import datetime
from agents.base_agent import BaseAgent
from models.db import Resource, Bed, BedStatus, User, UserRole, Notification


class MonitoringAgent(BaseAgent):
    name = "monitoring"
    description = "Monitors resource status in real-time"

    def run(self) -> dict:
        """Run monitoring checks on all resources."""
        alerts = []
        warnings = []

        # Check medication stock
        low_stock = (
            self.db.query(Resource)
            .filter(Resource.quantity <= Resource.min_quantity, Resource.min_quantity > 0)
            .all()
        )
        for r in low_stock:
            severity = "critical" if r.quantity == 0 else "warning"
            msg = f"{r.name}: stoc {r.quantity} (minim: {r.min_quantity})"
            if severity == "critical":
                alerts.append({"resource_id": r.id, "message": msg, "severity": severity})
            else:
                warnings.append({"resource_id": r.id, "message": msg, "severity": severity})

        # Check equipment in maintenance (Postgres enum stores NAMES, not values)
        in_maintenance = self.db.query(Resource).filter(Resource.status == "MAINTENANCE").all()
        for r in in_maintenance:
            warnings.append({
                "resource_id": r.id,
                "message": f"Echipament '{r.name}' în mentenanță la {r.location or 'necunoscut'}",
                "severity": "info",
            })

        # Check bed status
        beds = self.db.query(Bed).all()
        total_beds = len(beds)
        occupied = sum(1 for b in beds if b.status == BedStatus.OCCUPIED)
        if total_beds > 0 and occupied / total_beds > 0.9:
            alerts.append({
                "message": f"Capacitate critică: {occupied}/{total_beds} paturi ocupate ({round(occupied/total_beds*100)}%)",
                "severity": "critical",
            })

        # Notify admins of critical alerts
        if alerts:
            admins = self.db.query(User).filter(User.role == UserRole.ADMIN, User.is_active == True).all()
            for admin in admins:
                for alert in alerts:
                    notif = Notification(
                        user_id=admin.id,
                        title="Alertă Resurse",
                        message=alert["message"],
                        type="urgent",
                        created_at=datetime.utcnow(),
                    )
                    self.db.add(notif)
            self.db.commit()

        result = {
            "alerts": alerts,
            "warnings": warnings,
            "maintenance_count": len(in_maintenance),
            "low_stock_count": len(low_stock),
            "bed_occupancy": f"{occupied}/{total_beds}" if total_beds > 0 else "N/A",
            "checked_at": datetime.utcnow().isoformat(),
        }

        self.log_action("monitoring_check", result)
        return result
