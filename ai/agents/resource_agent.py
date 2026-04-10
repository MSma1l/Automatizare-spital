"""Agent 1: Resource Allocation Agent
Optimizes bed and equipment allocation using RandomForest + business rules.
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from agents.base_agent import BaseAgent
from models.db import Bed, BedStatus, Resource, User, UserRole


class ResourceAllocationAgent(BaseAgent):
    name = "resource_allocation"
    description = "Optimizes bed and equipment allocation"

    def __init__(self, db):
        super().__init__(db)
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)
        self._is_trained = False

    def train(self, historical_data: list[dict] = None):
        """Train on historical occupancy data."""
        if not historical_data or len(historical_data) < 10:
            # Generate synthetic training data
            np.random.seed(42)
            n = 200
            X = np.column_stack([
                np.random.randint(0, 7, n),      # day_of_week
                np.random.randint(0, 24, n),      # hour
                np.random.randint(1, 12, n),      # month
                np.random.uniform(0.3, 1.0, n),   # occupancy_rate
            ])
            # Label: 1 = need more beds, 0 = ok
            y = (X[:, 3] > 0.8).astype(int)
            self.model.fit(X, y)
            self._is_trained = True
            self.log_action("trained", {"samples": n, "synthetic": True})
        else:
            X = np.array([[d["day"], d["hour"], d["month"], d["rate"]] for d in historical_data])
            y = np.array([d["needs_allocation"] for d in historical_data])
            self.model.fit(X, y)
            self._is_trained = True
            self.log_action("trained", {"samples": len(historical_data), "synthetic": False})

    def run(self) -> dict:
        """Analyze current resource allocation."""
        beds = self.db.query(Bed).all()
        total = len(beds)
        occupied = sum(1 for b in beds if b.status == BedStatus.OCCUPIED)
        free = sum(1 for b in beds if b.status == BedStatus.FREE)
        occupancy_rate = occupied / total if total > 0 else 0

        # Group by ward
        wards = {}
        for bed in beds:
            if bed.ward not in wards:
                wards[bed.ward] = {"total": 0, "occupied": 0, "free": 0}
            wards[bed.ward]["total"] += 1
            if bed.status == BedStatus.OCCUPIED:
                wards[bed.ward]["occupied"] += 1
            elif bed.status == BedStatus.FREE:
                wards[bed.ward]["free"] += 1

        # Find critical wards
        critical_wards = []
        for ward, stats in wards.items():
            ward_rate = stats["occupied"] / stats["total"] if stats["total"] > 0 else 0
            if ward_rate > 0.8:
                critical_wards.append({"ward": ward, "rate": round(ward_rate * 100, 1)})

        suggestions = []
        if occupancy_rate > 0.8:
            suggestions.append("Ocuparea generală depășește 80%. Se recomandă activarea paturilor suplimentare.")
        for cw in critical_wards:
            suggestions.append(f"Secția {cw['ward']} are ocupare de {cw['rate']}%. Transferați pacienți dacă posibil.")

        # Suggest best bed for new patient
        best_ward = min(wards.items(), key=lambda x: x[1]["occupied"] / x[1]["total"] if x[1]["total"] > 0 else 1)[0] if wards else None
        free_bed = self.db.query(Bed).filter(Bed.status == BedStatus.FREE, Bed.ward == best_ward).first() if best_ward else None

        result = {
            "total_beds": total,
            "occupied": occupied,
            "free": free,
            "occupancy_rate": round(occupancy_rate * 100, 1),
            "critical_wards": critical_wards,
            "suggestions": suggestions,
            "recommended_bed": {"id": free_bed.id, "room": free_bed.room_number, "ward": free_bed.ward} if free_bed else None,
        }

        # Alert admins if critical
        if occupancy_rate > 0.8:
            admins = self.db.query(User).filter(User.role == UserRole.ADMIN).all()
            for admin in admins:
                self.create_recommendation(
                    admin.id,
                    f"Ocuparea paturilor este de {round(occupancy_rate * 100)}%. Acțiune necesară!",
                    priority="high",
                    data=result,
                )

        self.log_action("analysis_complete", result)
        return result

    def suggest_bed(self, ward_preference: str = None) -> dict | None:
        """Suggest the best available bed."""
        query = self.db.query(Bed).filter(Bed.status == BedStatus.FREE)
        if ward_preference:
            query = query.filter(Bed.ward == ward_preference)
        bed = query.first()
        if bed:
            return {"id": bed.id, "room": bed.room_number, "ward": bed.ward}
        return None
