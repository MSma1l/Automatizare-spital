"""Seed script to populate the database with demo data."""
import sys
import os
import random
from datetime import datetime, timedelta, time

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.appointment import Appointment, AppointmentStatus, AppointmentType
from app.models.resource import Resource, ResourceType, ResourceStatus
from app.models.bed import Bed, BedStatus
from app.models.notification import Notification, NotificationType
from app.services.auth_service import hash_password

# Create all tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

print("Seeding database...")

# ─── Admin ──────────────────────────────────────────────────
admin_user = db.query(User).filter(User.email == "admin@spital.ro").first()
if not admin_user:
    admin_user = User(email="admin@spital.ro", password_hash=hash_password("admin123"), role=UserRole.ADMIN)
    db.add(admin_user)
    db.flush()
    print("  Admin created: admin@spital.ro / admin123")

# ─── Doctors ────────────────────────────────────────────────
DOCTORS_DATA = [
    {"first_name": "Alexandru", "last_name": "Popescu", "specialty": "Cardiologie", "experience": 15, "bio": "Specialist în cardiologie intervențională cu peste 15 ani experiență.", "cabinet": "C201", "phone": "+40721000001"},
    {"first_name": "Maria", "last_name": "Ionescu", "specialty": "Neurologie", "experience": 12, "bio": "Expert în boli neurodegenerative și epilepsie.", "cabinet": "C302", "phone": "+40721000002"},
    {"first_name": "Andrei", "last_name": "Popa", "specialty": "Ortopedie", "experience": 10, "bio": "Specialist în chirurgie ortopedică și traumatologie.", "cabinet": "C103", "phone": "+40721000003"},
    {"first_name": "Elena", "last_name": "Dumitrescu", "specialty": "Pediatrie", "experience": 20, "bio": "Pediatru cu experiență vastă în neonatologie.", "cabinet": "C404", "phone": "+40721000004"},
    {"first_name": "Mihai", "last_name": "Stanescu", "specialty": "Chirurgie Generală", "experience": 18, "bio": "Chirurg cu specializare în chirurgie minim invazivă.", "cabinet": "C105", "phone": "+40721000005"},
    {"first_name": "Ana", "last_name": "Moldovan", "specialty": "Dermatologie", "experience": 8, "bio": "Specialist în dermatologie estetică și clinică.", "cabinet": "C206", "phone": "+40721000006"},
]

doctors = []
for i, dd in enumerate(DOCTORS_DATA):
    email = f"dr.{dd['last_name'].lower()}@spital.ro"
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        doctor = db.query(Doctor).filter(Doctor.user_id == existing.id).first()
        if doctor:
            doctors.append(doctor)
        continue

    user = User(email=email, password_hash=hash_password("doctor123"), role=UserRole.DOCTOR)
    db.add(user)
    db.flush()

    doctor = Doctor(
        user_id=user.id,
        first_name=dd["first_name"], last_name=dd["last_name"],
        specialty=dd["specialty"], experience_years=dd["experience"],
        bio=dd["bio"], phone=dd["phone"], cabinet=dd["cabinet"],
    )
    db.add(doctor)
    db.flush()

    # Schedule: Mon-Fri 8-16
    for day in range(5):
        schedule = DoctorSchedule(
            doctor_id=doctor.id, day_of_week=day,
            start_time=time(8, 0), end_time=time(16, 0),
        )
        db.add(schedule)

    doctors.append(doctor)
    print(f"  Doctor created: {email} / doctor123")

db.commit()

# ─── Patients ───────────────────────────────────────────────
PATIENTS_DATA = [
    {"first_name": "Ion", "last_name": "Vasile", "gender": "male", "phone": "+40722000001", "insurance": "RO1234567890"},
    {"first_name": "Ana", "last_name": "Georgescu", "gender": "female", "phone": "+40722000002", "insurance": "RO1234567891"},
    {"first_name": "Mihai", "last_name": "Radu", "gender": "male", "phone": "+40722000003", "insurance": "RO1234567892"},
    {"first_name": "Elena", "last_name": "Constantinescu", "gender": "female", "phone": "+40722000004", "insurance": "RO1234567893"},
    {"first_name": "Dan", "last_name": "Marinescu", "gender": "male", "phone": "+40722000005", "insurance": "RO1234567894"},
    {"first_name": "Cristina", "last_name": "Preda", "gender": "female", "phone": "+40722000006", "insurance": "RO1234567895"},
    {"first_name": "George", "last_name": "Tudor", "gender": "male", "phone": "+40722000007", "insurance": "RO1234567896"},
    {"first_name": "Laura", "last_name": "Stoica", "gender": "female", "phone": "+40722000008", "insurance": "RO1234567897"},
    {"first_name": "Adrian", "last_name": "Florea", "gender": "male", "phone": "+40722000009", "insurance": "RO1234567898"},
    {"first_name": "Andreea", "last_name": "Mihai", "gender": "female", "phone": "+40722000010", "insurance": "RO1234567899"},
]

patients = []
for pd in PATIENTS_DATA:
    email = f"{pd['first_name'].lower()}.{pd['last_name'].lower()}@email.ro"
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        patient = db.query(Patient).filter(Patient.user_id == existing.id).first()
        if patient:
            patients.append(patient)
        continue

    user = User(email=email, password_hash=hash_password("pacient123"), role=UserRole.PATIENT)
    db.add(user)
    db.flush()

    birth_year = random.randint(1960, 2000)
    patient = Patient(
        user_id=user.id,
        first_name=pd["first_name"], last_name=pd["last_name"],
        birth_date=datetime(birth_year, random.randint(1, 12), random.randint(1, 28)).date(),
        gender=pd["gender"], phone=pd["phone"],
        address=f"Str. Exemplu {random.randint(1, 100)}, București",
        insurance_number=pd["insurance"],
    )
    db.add(patient)
    db.flush()
    patients.append(patient)
    print(f"  Patient created: {email} / pacient123")

db.commit()

# ─── Appointments ───────────────────────────────────────────
if db.query(Appointment).count() == 0:
    now = datetime.utcnow()
    statuses = [AppointmentStatus.COMPLETED, AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]

    for i in range(60):
        doctor = random.choice(doctors)
        patient = random.choice(patients)
        days_offset = random.randint(-30, 14)
        hour = random.randint(8, 15)

        appt_date = now + timedelta(days=days_offset, hours=hour - now.hour)
        status = AppointmentStatus.COMPLETED if days_offset < 0 else random.choice(statuses)

        appt = Appointment(
            doctor_id=doctor.id, patient_id=patient.id,
            date_time=appt_date, duration_minutes=30,
            status=status,
            type=random.choice([AppointmentType.CONSULTATION, AppointmentType.CHECKUP, AppointmentType.VIDEO]),
            notes="Consultație de rutină." if status == AppointmentStatus.COMPLETED else None,
        )
        db.add(appt)

    db.commit()
    print(f"  60 appointments created")

# ─── Resources ──────────────────────────────────────────────
if db.query(Resource).count() == 0:
    RESOURCES = [
        ("Paracetamol 500mg", "medication", 500, 100, "Farmacie"),
        ("Ibuprofen 400mg", "medication", 200, 50, "Farmacie"),
        ("Amoxicilină 500mg", "medication", 150, 30, "Farmacie"),
        ("Seringi 5ml", "supply", 1000, 200, "Depozit"),
        ("Mănuși latex M", "supply", 2000, 500, "Depozit"),
        ("EKG portabil", "equipment", 5, 0, "Secția Cardiologie"),
        ("Ecograf", "equipment", 3, 0, "Secția Radiologie"),
        ("Ventilator mecanic", "equipment", 10, 2, "Secția ATI"),
        ("Sală consultații 1", "room", 1, 0, "Etaj 1"),
        ("Sală consultații 2", "room", 1, 0, "Etaj 2"),
        ("Bandaje sterile", "supply", 800, 150, "Depozit"),
        ("Aspirină 100mg", "medication", 30, 50, "Farmacie"),  # Intentionally low
    ]
    for name, rtype, qty, min_qty, loc in RESOURCES:
        status = ResourceStatus.OUT_OF_STOCK if qty == 0 else ResourceStatus.AVAILABLE
        r = Resource(name=name, type=rtype, quantity=qty, min_quantity=min_qty, location=loc, status=status)
        db.add(r)
    db.commit()
    print(f"  {len(RESOURCES)} resources created")

# ─── Beds ───────────────────────────────────────────────────
if db.query(Bed).count() == 0:
    WARDS = ["Secția ATI", "Secția Chirurgie", "Secția Medicină Internă", "Secția Cardiologie", "Secția Pediatrie"]
    bed_id = 0
    for ward in WARDS:
        for room in range(1, 7):
            bed_id += 1
            status = random.choices(
                [BedStatus.FREE, BedStatus.OCCUPIED, BedStatus.MAINTENANCE],
                weights=[50, 40, 10],
            )[0]
            patient_id = None
            admitted = None
            if status == BedStatus.OCCUPIED and patients:
                patient_id = random.choice(patients).id
                admitted = datetime.utcnow() - timedelta(days=random.randint(1, 10))

            bed = Bed(
                room_number=f"{WARDS.index(ward)+1}{room:02d}",
                ward=ward, status=status,
                patient_id=patient_id, admitted_at=admitted,
            )
            db.add(bed)
    db.commit()
    print(f"  30 beds created across {len(WARDS)} wards")

# ─── Notifications ──────────────────────────────────────────
if db.query(Notification).count() == 0:
    notif = Notification(
        user_id=admin_user.id,
        title="Bine ați venit!",
        message="Sistemul Hospital DSS a fost inițializat cu succes. Datele demo au fost încărcate.",
        type=NotificationType.SYSTEM,
    )
    db.add(notif)
    db.commit()
    print("  Welcome notification created")

db.close()
print("\nSeed complete! Demo accounts:")
print("  Admin:   admin@spital.ro / admin123")
print("  Doctor:  dr.popescu@spital.ro / doctor123")
print("  Patient: ion.vasile@email.ro / pacient123")
