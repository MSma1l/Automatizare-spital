"""
Generate synthetic training data for all 7 AI agents.
Each agent gets 1000+ realistic examples.
"""
import csv
import json
import random
import os
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "training_data")
os.makedirs(DATA_DIR, exist_ok=True)

WARDS = [
    "Secția ATI", "Secția Chirurgie", "Secția Medicină Internă",
    "Secția Cardiologie", "Secția Pediatrie", "Secția Neurologie",
    "Secția Ortopedie", "Secția Ginecologie",
]

SPECIALTIES = [
    "Cardiologie", "Neurologie", "Ortopedie", "Pediatrie",
    "Dermatologie", "Chirurgie Generală", "Medicină Internă",
    "Ginecologie", "Urologie", "Oftalmologie", "ORL", "Psihiatrie",
]

MEDICATIONS = [
    "Paracetamol 500mg", "Ibuprofen 400mg", "Amoxicilină 500mg",
    "Metformin 850mg", "Enalapril 10mg", "Aspirină 100mg",
    "Omeprazol 20mg", "Atorvastatină 20mg", "Amlodipină 5mg",
    "Losartan 50mg", "Bisoprolol 5mg", "Clopidogrel 75mg",
    "Insulină Lantus", "Levotiroxină 50mcg", "Diazepam 5mg",
    "Tramadol 50mg", "Ciprofloxacin 500mg", "Dexametazonă 4mg",
    "Furosemid 40mg", "Spironolactonă 25mg",
]

EQUIPMENT = [
    "EKG portabil", "Ecograf", "Ventilator mecanic", "Defibrilator",
    "Monitor pacient", "Pompă infuzie", "Pulsoximetru",
    "Aparat RMN", "Aparat CT", "Aparat radiologie",
    "Laringoscop", "Electroencefalograf", "Spirometru",
]


# ═══════════════════════════════════════════════════════════════
# 1. RESOURCE ALLOCATION AGENT - bed occupancy data (1500 rows)
# ═══════════════════════════════════════════════════════════════
def generate_resource_data():
    print("Generating resource allocation data...")
    rows = []
    for _ in range(1500):
        day_of_week = random.randint(0, 6)
        hour = random.randint(0, 23)
        month = random.randint(1, 12)
        ward = random.choice(WARDS)
        total_beds = random.randint(10, 50)

        # Realistic occupancy patterns
        base_rate = 0.55
        if day_of_week in [0, 1]:  # Mon-Tue higher
            base_rate += 0.1
        if day_of_week in [5, 6]:  # Weekend lower
            base_rate -= 0.1
        if month in [11, 12, 1, 2]:  # Winter higher
            base_rate += 0.1
        if month in [6, 7, 8]:  # Summer lower
            base_rate -= 0.05
        if ward == "Secția ATI":
            base_rate += 0.15
        if hour >= 10 and hour <= 16:  # Business hours
            base_rate += 0.05

        occupancy_rate = min(1.0, max(0.1, base_rate + random.gauss(0, 0.12)))
        occupied = int(total_beds * occupancy_rate)
        free = total_beds - occupied

        # Target: needs_reallocation (1 = yes, 0 = no)
        needs_reallocation = 1 if occupancy_rate > 0.8 else 0
        # Urgency: 0=none, 1=low, 2=medium, 3=high
        urgency = 0
        if occupancy_rate > 0.95:
            urgency = 3
        elif occupancy_rate > 0.85:
            urgency = 2
        elif occupancy_rate > 0.75:
            urgency = 1

        rows.append({
            "day_of_week": day_of_week,
            "hour": hour,
            "month": month,
            "ward": ward,
            "total_beds": total_beds,
            "occupied_beds": occupied,
            "free_beds": free,
            "occupancy_rate": round(occupancy_rate, 3),
            "avg_stay_days": round(random.uniform(1, 14), 1),
            "admissions_today": random.randint(0, 8),
            "discharges_today": random.randint(0, 6),
            "needs_reallocation": needs_reallocation,
            "urgency_level": urgency,
        })

    path = os.path.join(DATA_DIR, "resource_allocation.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {len(rows)} rows saved to resource_allocation.csv")


# ═══════════════════════════════════════════════════════════════
# 2. SCHEDULING AGENT - appointment scheduling data (1200 rows)
# ═══════════════════════════════════════════════════════════════
def generate_scheduling_data():
    print("Generating scheduling data...")
    rows = []
    base_date = datetime(2025, 1, 1)

    for _ in range(1200):
        day_offset = random.randint(0, 365)
        appt_date = base_date + timedelta(days=day_offset)
        day_of_week = appt_date.weekday()
        hour = random.choices(
            list(range(8, 18)),
            weights=[5, 10, 12, 10, 8, 6, 8, 10, 8, 5],
        )[0]
        minute = random.choice([0, 30])

        doctor_id = random.randint(1, 20)
        patient_id = random.randint(1, 200)
        specialty = random.choice(SPECIALTIES)
        duration = random.choices([15, 30, 45, 60], weights=[10, 50, 25, 15])[0]
        appt_type = random.choices(
            ["consultation", "checkup", "emergency", "video"],
            weights=[45, 25, 10, 20],
        )[0]

        # Existing load for this doctor on this day
        doctor_daily_load = random.randint(0, 12)
        has_conflict = 1 if (doctor_daily_load > 8 or random.random() < 0.05) else 0

        # Wait time in days from booking to appointment
        wait_days = random.choices(
            [0, 1, 2, 3, 5, 7, 14, 21, 30],
            weights=[5, 10, 15, 15, 15, 15, 10, 10, 5],
        )[0]

        # Status outcome
        if has_conflict:
            status = random.choices(
                ["rescheduled", "cancelled", "completed"],
                weights=[50, 30, 20],
            )[0]
        else:
            status = random.choices(
                ["completed", "cancelled", "no_show"],
                weights=[75, 15, 10],
            )[0]

        # Optimal slot suggestion score (0-1)
        optimal_score = 1.0
        if doctor_daily_load > 6:
            optimal_score -= 0.3
        if hour < 9 or hour > 16:
            optimal_score -= 0.1
        if day_of_week >= 5:
            optimal_score -= 0.2
        optimal_score = max(0, min(1, optimal_score + random.gauss(0, 0.1)))

        rows.append({
            "date": appt_date.strftime("%Y-%m-%d"),
            "day_of_week": day_of_week,
            "hour": hour,
            "minute": minute,
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "specialty": specialty,
            "duration_minutes": duration,
            "appointment_type": appt_type,
            "doctor_daily_load": doctor_daily_load,
            "has_conflict": has_conflict,
            "wait_days": wait_days,
            "status": status,
            "optimal_score": round(optimal_score, 3),
        })

    path = os.path.join(DATA_DIR, "scheduling.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {len(rows)} rows saved to scheduling.csv")


# ═══════════════════════════════════════════════════════════════
# 3. MONITORING AGENT - resource monitoring data (1500 rows)
# ═══════════════════════════════════════════════════════════════
def generate_monitoring_data():
    print("Generating monitoring data...")
    rows = []

    for _ in range(1500):
        resource_type = random.choices(
            ["medication", "equipment", "supply", "bed"],
            weights=[35, 20, 25, 20],
        )[0]

        if resource_type == "medication":
            name = random.choice(MEDICATIONS)
            quantity = random.randint(0, 600)
            min_quantity = random.randint(20, 100)
            normal_range_low = min_quantity
            normal_range_high = min_quantity * 6
        elif resource_type == "equipment":
            name = random.choice(EQUIPMENT)
            quantity = random.randint(1, 15)
            min_quantity = random.randint(1, 3)
            normal_range_low = min_quantity
            normal_range_high = min_quantity * 5
        elif resource_type == "supply":
            name = random.choice(["Seringi 5ml", "Mănuși latex", "Bandaje sterile",
                                   "Comprese", "Ace vacutainer", "Soluție dezinfectant",
                                   "Catetere IV", "Tuburi colectare sânge"])
            quantity = random.randint(0, 3000)
            min_quantity = random.randint(100, 500)
            normal_range_low = min_quantity
            normal_range_high = min_quantity * 5
        else:  # bed
            name = f"Pat {random.choice(WARDS)}"
            quantity = random.randint(0, 1)
            min_quantity = 0
            normal_range_low = 0
            normal_range_high = 1

        usage_rate = round(random.uniform(0.01, 0.3), 3)  # daily usage rate
        days_until_empty = int(quantity / max(0.01, usage_rate * quantity)) if quantity > 0 else 0

        # Anomaly detection features
        is_anomaly = 0
        if quantity <= 0:
            is_anomaly = 1
        elif quantity < min_quantity * 0.5:
            is_anomaly = 1 if random.random() < 0.7 else 0
        elif quantity < min_quantity:
            is_anomaly = 1 if random.random() < 0.3 else 0
        # Random anomalies (equipment failure, unusual consumption)
        if random.random() < 0.03:
            is_anomaly = 1

        alert_level = "none"
        if is_anomaly:
            if quantity <= 0:
                alert_level = "critical"
            elif quantity < min_quantity * 0.5:
                alert_level = "high"
            else:
                alert_level = "medium"

        hour = random.randint(0, 23)
        day_of_week = random.randint(0, 6)
        temperature = round(random.gauss(22, 2), 1) if resource_type == "medication" else None
        humidity = round(random.gauss(45, 10), 1) if resource_type == "medication" else None

        rows.append({
            "resource_type": resource_type,
            "name": name,
            "quantity": quantity,
            "min_quantity": min_quantity,
            "normal_range_low": normal_range_low,
            "normal_range_high": normal_range_high,
            "usage_rate_daily": usage_rate,
            "days_until_empty": days_until_empty,
            "hour": hour,
            "day_of_week": day_of_week,
            "temperature": temperature,
            "humidity": humidity,
            "is_anomaly": is_anomaly,
            "alert_level": alert_level,
        })

    path = os.path.join(DATA_DIR, "monitoring.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {len(rows)} rows saved to monitoring.csv")


# ═══════════════════════════════════════════════════════════════
# 4. PREDICTIVE AGENT - time series data (1000 rows - daily)
# ═══════════════════════════════════════════════════════════════
def generate_predictive_data():
    print("Generating predictive time series data...")
    rows = []
    base_date = datetime(2023, 1, 1)

    for day_offset in range(1000):
        date = base_date + timedelta(days=day_offset)
        day_of_week = date.weekday()
        month = date.month
        is_holiday = 1 if (month == 12 and date.day in [25, 26, 31]) or \
                          (month == 1 and date.day == 1) or \
                          (month == 5 and date.day == 1) else 0

        # Base patient count with seasonality
        base = 45
        # Weekly pattern
        if day_of_week == 0:
            base += 8  # Monday peak
        elif day_of_week == 4:
            base += 5  # Friday
        elif day_of_week == 5:
            base -= 15  # Saturday
        elif day_of_week == 6:
            base -= 20  # Sunday

        # Monthly seasonality
        if month in [11, 12, 1, 2]:  # Winter - flu season
            base += 12
        elif month in [6, 7, 8]:  # Summer
            base -= 5

        # Holiday effect
        if is_holiday:
            base -= 25

        # Add noise
        patients = max(0, int(base + random.gauss(0, 6)))
        admissions = max(0, int(patients * random.uniform(0.1, 0.3)))
        discharges = max(0, int(patients * random.uniform(0.08, 0.25)))
        emergency = max(0, int(random.gauss(8, 3)))

        # Resource needs
        beds_needed = int(patients * 0.3 + random.gauss(0, 2))
        medication_units = int(patients * 2.5 + random.gauss(0, 10))
        staff_needed = max(5, int(patients * 0.4 + random.gauss(0, 2)))

        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "day_of_week": day_of_week,
            "month": month,
            "year": date.year,
            "is_holiday": is_holiday,
            "total_patients": patients,
            "new_admissions": admissions,
            "discharges": discharges,
            "emergency_visits": emergency,
            "beds_needed": max(0, beds_needed),
            "medication_units_used": max(0, medication_units),
            "staff_needed": staff_needed,
            "avg_wait_time_min": max(5, int(random.gauss(25, 10) + patients * 0.2)),
            "patient_satisfaction": round(min(5, max(1, 4.2 - patients * 0.01 + random.gauss(0, 0.3))), 2),
        })

    path = os.path.join(DATA_DIR, "predictive_timeseries.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {len(rows)} rows saved to predictive_timeseries.csv")


# ═══════════════════════════════════════════════════════════════
# 5. RECOMMENDATION AGENT - patient-doctor interaction data (1200 rows)
# ═══════════════════════════════════════════════════════════════
def generate_recommendation_data():
    print("Generating recommendation data...")
    rows = []

    CONDITIONS = [
        "Hipertensiune arterială", "Diabet zaharat tip 2", "Astm bronșic",
        "Boală coronariană", "Insuficiență cardiacă", "Fibrilație atrială",
        "BPOC", "Artrită reumatoidă", "Lombosciatică", "Migrenă cronică",
        "Epilepsie", "Hipotiroidism", "Anemie feriprivă", "Gastrita cronică",
        "Colecistită", "Hernie de disc", "Pneumonie", "Infecție urinară",
        "Depresie", "Anxietate generalizată",
    ]

    INVESTIGATIONS = [
        "Hemoleucogramă completă", "Profil lipidic", "Glicemie",
        "HbA1c", "TSH", "ECG", "Ecocardiografie", "Ecografie abdominală",
        "Radiografie toracică", "RMN cerebral", "CT toracic",
        "Spirometrie", "EEG", "Sumar urină", "Cultură urină",
        "Profil hepatic", "Funcție renală", "Ionogramă", "Coagulogramă",
    ]

    TREATMENTS = [
        "Regim alimentar", "Exerciții fizice regulate", "Fizioterapie",
        "Medicație orală", "Injecții subcutanate", "Terapie inhalatorie",
        "Intervenție chirurgicală", "Monitorizare ambulatorie",
        "Psihoterapie", "Terapie cu oxigen",
    ]

    for _ in range(1200):
        patient_id = random.randint(1, 300)
        doctor_id = random.randint(1, 30)
        age = random.randint(18, 85)
        gender = random.choice(["male", "female"])
        specialty = random.choice(SPECIALTIES)

        n_conditions = random.choices([1, 2, 3, 4], weights=[40, 30, 20, 10])[0]
        conditions = random.sample(CONDITIONS, min(n_conditions, len(CONDITIONS)))

        n_prev_visits = random.randint(0, 20)
        days_since_last = random.randint(0, 365)
        compliance_score = round(random.uniform(0.3, 1.0), 2)

        # Recommendations based on conditions
        suggested_investigations = random.sample(INVESTIGATIONS, random.randint(1, 4))
        suggested_treatments = random.sample(TREATMENTS, random.randint(1, 3))

        # Risk level
        risk_score = 0
        if age > 65:
            risk_score += 2
        if n_conditions >= 3:
            risk_score += 2
        if days_since_last > 180:
            risk_score += 1
        if compliance_score < 0.5:
            risk_score += 2
        risk_score += random.randint(0, 2)
        risk_level = "low" if risk_score < 3 else "medium" if risk_score < 5 else "high"

        needs_followup = 1 if (days_since_last > 90 or risk_level == "high") else 0
        needs_attention = 1 if (risk_level == "high" or compliance_score < 0.4) else 0

        rows.append({
            "patient_id": patient_id,
            "doctor_id": doctor_id,
            "age": age,
            "gender": gender,
            "specialty": specialty,
            "conditions": "|".join(conditions),
            "n_conditions": n_conditions,
            "n_previous_visits": n_prev_visits,
            "days_since_last_visit": days_since_last,
            "compliance_score": compliance_score,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "suggested_investigations": "|".join(suggested_investigations),
            "suggested_treatments": "|".join(suggested_treatments),
            "needs_followup": needs_followup,
            "needs_attention": needs_attention,
        })

    path = os.path.join(DATA_DIR, "recommendations.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {len(rows)} rows saved to recommendations.csv")


# ═══════════════════════════════════════════════════════════════
# 6. NOTIFICATION AGENT - notification priority data (1000 rows)
# ═══════════════════════════════════════════════════════════════
def generate_notification_data():
    print("Generating notification data...")
    rows = []

    NOTIFICATION_TYPES = [
        ("appointment_reminder", "Reminder programare cu Dr. {doctor} pe {date}"),
        ("appointment_confirmed", "Programarea cu Dr. {doctor} a fost confirmată"),
        ("appointment_cancelled", "Programarea cu {patient} a fost anulată"),
        ("appointment_pending", "Programare nouă de la {patient} - neconfirmată"),
        ("low_stock_warning", "Stoc scăzut: {resource} - {qty} unități rămase"),
        ("low_stock_critical", "CRITIC: {resource} - stoc epuizat!"),
        ("bed_occupancy_high", "Ocupare paturi {ward}: {rate}%"),
        ("equipment_maintenance", "Echipament {resource} necesită mentenanță"),
        ("patient_followup", "Pacientul {patient} necesită control la {days} zile"),
        ("lab_results", "Rezultate analize disponibile pentru {patient}"),
        ("shift_change", "Schimb de tură în {ward} la ora {time}"),
        ("emergency_alert", "URGENȚĂ: pacient critic în {ward}"),
        ("system_update", "Actualizare sistem programată la {time}"),
        ("message_received", "Mesaj nou de la {sender}"),
    ]

    DOCTORS = [f"Dr. {'Popescu Ionescu Popa Dumitrescu Stanescu Moldovan Radu Stoica'.split()[i]}"
               for i in range(8)]
    PATIENTS = ["Ion Vasile", "Ana Georgescu", "Mihai Radu", "Elena Constantinescu",
                "Dan Marinescu", "Cristina Preda", "George Tudor", "Laura Stoica"]

    for _ in range(1000):
        notif_type, template = random.choice(NOTIFICATION_TYPES)
        hour = random.randint(0, 23)
        day_of_week = random.randint(0, 6)

        # Priority rules
        if "critical" in notif_type or "emergency" in notif_type:
            priority = "urgent"
            priority_score = random.uniform(0.9, 1.0)
        elif "warning" in notif_type or "pending" in notif_type:
            priority = "high"
            priority_score = random.uniform(0.7, 0.9)
        elif "reminder" in notif_type or "followup" in notif_type:
            priority = "normal"
            priority_score = random.uniform(0.4, 0.7)
        else:
            priority = "low"
            priority_score = random.uniform(0.1, 0.4)

        # Time sensitivity (hours until irrelevant)
        if "reminder" in notif_type:
            time_sensitivity = random.choice([1, 2, 4, 8, 24])
        elif "emergency" in notif_type:
            time_sensitivity = 0.5
        elif "critical" in notif_type:
            time_sensitivity = 2
        else:
            time_sensitivity = random.choice([24, 48, 72, 168])

        user_role = random.choice(["admin", "doctor", "patient"])
        was_read = random.choices([0, 1], weights=[30, 70])[0]
        read_delay_min = random.randint(1, 1440) if was_read else None

        # Should send push notification?
        should_push = 1 if priority in ["urgent", "high"] else (1 if random.random() < 0.3 else 0)

        rows.append({
            "notification_type": notif_type,
            "priority": priority,
            "priority_score": round(priority_score, 3),
            "hour": hour,
            "day_of_week": day_of_week,
            "user_role": user_role,
            "time_sensitivity_hours": time_sensitivity,
            "should_push": should_push,
            "was_read": was_read,
            "read_delay_minutes": read_delay_min,
            "channel": random.choice(["in_app", "email", "both"]),
        })

    path = os.path.join(DATA_DIR, "notifications.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {len(rows)} rows saved to notifications.csv")


# ═══════════════════════════════════════════════════════════════
# 7. REGISTRATION AGENT - line-level field labels (RO + RU, 3000 rows)
# ═══════════════════════════════════════════════════════════════
FIRST_NAMES_M = ["Ion", "Mihai", "Andrei", "Alexandru", "Dan", "George", "Vlad", "Adrian",
                  "Radu", "Cristian", "Marius", "Paul", "Florin", "Cosmin", "Gabriel"]
FIRST_NAMES_F = ["Maria", "Ana", "Elena", "Cristina", "Ioana", "Andreea", "Laura",
                  "Mihaela", "Diana", "Raluca", "Oana", "Monica", "Simona", "Daniela"]
LAST_NAMES = ["Popescu", "Ionescu", "Popa", "Dumitrescu", "Stanescu", "Moldovan", "Radu",
              "Georgescu", "Constantinescu", "Marinescu", "Preda", "Tudor", "Stoica",
              "Florea", "Vasile", "Munteanu", "Ciobanu", "Enache"]
STREETS_RO = ["Str. Libertății", "Str. Mihai Eminescu", "Bd. Unirii", "Str. 1 Decembrie",
              "Str. Mihai Viteazul", "Str. Ștefan cel Mare", "Bd. Dacia", "Str. Florilor"]
CITIES_RO = ["București", "Cluj-Napoca", "Iași", "Timișoara", "Constanța", "Brașov",
             "Chișinău", "Bălți", "Galați", "Oradea"]


def _random_ro_text_for_field(field: str) -> str:
    """Generate the *value part* of a labeled line for a given field."""
    if field == "first_name":
        return random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
    if field == "last_name":
        return random.choice(LAST_NAMES)
    if field == "full_name":
        return f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES_M + FIRST_NAMES_F)}"
    if field == "birth_date":
        d = random.randint(1, 28)
        m = random.randint(1, 12)
        y = random.randint(1945, 2010)
        fmt = random.choice(["{d:02d}.{m:02d}.{y}", "{d}/{m}/{y}", "{y}-{m:02d}-{d:02d}"])
        return fmt.format(d=d, m=m, y=y)
    if field == "gender":
        return random.choice(["M", "F", "Masculin", "Feminin", "male", "female", "мужской", "женский"])
    if field == "phone":
        prefix = random.choice(["+40 7", "+373 7", "07", "+7 9"])
        return f"{prefix}{random.randint(10000000, 99999999)}"
    if field == "address":
        return f"{random.choice(STREETS_RO)} {random.randint(1, 200)}, {random.choice(CITIES_RO)}"
    if field == "insurance_number":
        kind = random.choice(["RO", "MD", "", "CNP "])
        return f"{kind}{random.randint(10**9, 10**15)}"
    if field == "email":
        fn = random.choice(FIRST_NAMES_M + FIRST_NAMES_F).lower()
        ln = random.choice(LAST_NAMES).lower()
        dom = random.choice(["gmail.com", "yahoo.com", "mail.md", "hospital.md"])
        return f"{fn}.{ln}@{dom}"
    return "other"


def generate_registration_data():
    print("Generating registration agent data...")
    # label keywords map per field (RO + RU)
    KEY_VARIANTS = {
        "first_name": ["Prenume", "prenumele", "Имя"],
        "last_name":  ["Nume", "Numele", "Nume de familie", "Фамилия"],
        "full_name":  ["Nume complet", "Nume și prenume", "Пациент"],
        "birth_date": ["Data nașterii", "Data nasterii", "Născut", "DOB", "Дата рождения"],
        "gender":     ["Sex", "Gen", "Пол"],
        "phone":      ["Telefon", "Tel", "Mobil", "Телефон"],
        "address":    ["Adresa", "Adresă", "Domiciliu", "Адрес"],
        "insurance_number": ["Asigurare", "Nr. asigurare", "CNP", "Polis", "Полис"],
        "email":      ["Email", "E-mail", "Mail", "Эл. почта"],
    }
    rows = []

    # labeled lines
    for field, keys in KEY_VARIANTS.items():
        for _ in range(200):  # 200 per field x 9 fields = 1800
            key = random.choice(keys)
            sep = random.choice([": ", " - ", " : ", ":  "])
            value = _random_ro_text_for_field(field)
            line = f"{key}{sep}{value}"
            rows.append({"text": line, "label": field})

    # free-text distractor lines (label "none")
    DISTRACTORS = [
        "Consultat astăzi la ora 10:00 de Dr. Popescu.",
        "Pacientul nu prezintă simptome acute.",
        "Investigații recomandate: analize sânge, ECG.",
        "Alergii cunoscute: penicilină.",
        "Fumător: Nu",
        "Diabet: Nu",
        "Ultima vizită: 2024-05-10",
        "Tratament curent: Paracetamol 500mg",
        "Recomandare: Revenire peste 7 zile.",
        "Grupa sanguină: A+",
        "Consult efectuat",
        "Observații: bun general",
        "Rețetă eliberată",
        "Notă: pacient colaborativ",
    ]
    for _ in range(600):
        rows.append({"text": random.choice(DISTRACTORS), "label": "none"})

    # Unlabeled lines with ONLY the value (e.g., scanned OCR with no keys) — hardest case
    for field in ["phone", "email", "birth_date", "insurance_number", "full_name", "address"]:
        for _ in range(100):
            rows.append({"text": _random_ro_text_for_field(field), "label": field})

    # ── Moldovan ID card samples ──────────────────────────────
    # Realistic layout: label and bilingual header on one line, value on next.
    # Adds ~800 rows that directly mirror what OCR produces on MD ID cards.
    md_last_names = ["GISCA", "POPESCU", "IONESCU", "MOLDOVANU", "ROSCA", "CEBAN",
                     "RUSU", "STIRBATI", "CHIRIAC", "BOTNARU", "VIERU", "URSU",
                     "CARAMAN", "MUNTEANU", "TOFAN", "GRECU", "LUPU"]
    md_first_names = ["VLAD", "ION", "ANDREI", "MIHAI", "STEFAN", "ALEXANDRU",
                      "DANIEL", "VICTOR", "NICOLAE", "DUMITRU", "PETRU", "SERGIU",
                      "MARIA", "ANA", "ELENA", "DANIELA", "CRISTINA", "IRINA"]

    for _ in range(100):
        # Labels (appear alone as their own line in OCR output)
        rows.append({"text": "Numele/Фамилия", "label": "last_name"})
        rows.append({"text": "Prenumele/Имя", "label": "first_name"})
        rows.append({"text": "Data nașterii/Дата рождения", "label": "birth_date"})
        rows.append({"text": "Data nasterii/Data nasterii", "label": "birth_date"})
        rows.append({"text": "Sex/Пол", "label": "gender"})
        rows.append({"text": "Cetățenia/Гражданство", "label": "none"})
        rows.append({"text": "Data emiterii/Дата выдачи", "label": "none"})
        rows.append({"text": "Data expirării/Действителен до", "label": "none"})

    for _ in range(80):
        # Name values (all caps, alone on a line)
        rows.append({"text": random.choice(md_last_names), "label": "last_name"})
        rows.append({"text": random.choice(md_first_names), "label": "first_name"})

    for _ in range(80):
        # Date values in MD ID format: "10 12 2004"
        d = random.randint(1, 28); m = random.randint(1, 12); y = random.randint(1950, 2015)
        rows.append({"text": f"{d:02d} {m:02d} {y}", "label": "birth_date"})

    for _ in range(40):
        # Gender
        rows.append({"text": random.choice(["M", "F"]), "label": "gender"})

    # Noise from ID card (should be labeled "none")
    for _ in range(80):
        rows.append({"text": "REPUBLICA MOLDOVA", "label": "none"})
        rows.append({"text": "BULETIN DE IDENTITATE", "label": "none"})
        rows.append({"text": "AGENTIA SERVICII PUBLICE", "label": "none"})
        rows.append({"text": "MDA", "label": "none"})
        rows.append({"text": f"B{random.randint(10000000, 99999999)}", "label": "insurance_number"})

    random.shuffle(rows)

    path = os.path.join(DATA_DIR, "registration.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "label"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> {len(rows)} rows saved to registration.csv")


# ═══════════════════════════════════════════════════════════════
# RUN ALL GENERATORS
# ═══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("Generating synthetic training data for Hospital DSS AI")
    print("=" * 60)
    generate_resource_data()
    generate_scheduling_data()
    generate_monitoring_data()
    generate_predictive_data()
    generate_recommendation_data()
    generate_notification_data()
    generate_registration_data()
    print("=" * 60)
    print("Help Agent Q&A data is in help_agent_qa.json (separate file)")
    print("All training data generated successfully!")
    print("=" * 60)
