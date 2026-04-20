"""Comprehensive E2E test suite for Hospital DSS.
Runs against live stack on http://localhost.
"""
import json
import sys
import time
import urllib.request
import urllib.error

BASE = "http://localhost"

passed = 0
failed = 0
failures = []

def req(method, path, *, token=None, body=None, expected_status=None):
    url = f"{BASE}{path}"
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    r = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        resp = urllib.request.urlopen(r, timeout=30)
        code = resp.status
        payload = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        code = e.code
        try:
            payload = e.read().decode("utf-8")
        except Exception:
            payload = ""
    try:
        data_json = json.loads(payload) if payload else {}
    except json.JSONDecodeError:
        data_json = {"_raw": payload[:200]}
    return code, data_json

def expect(name, code, ok_codes=(200, 201)):
    global passed, failed
    if code in ok_codes:
        print(f"  PASS  {name}  [HTTP {code}]")
        passed += 1
        return True
    print(f"  FAIL  {name}  [HTTP {code}]")
    failed += 1
    failures.append(name)
    return False

def section(title):
    print(f"\n=== {title} ===")

# ─── AUTH ──────────────────────────────────────────────────
section("AUTH")
code, data = req("POST", "/api/auth/login",
                 body={"email": "admin@hospital.md", "password": "Admin123!"})
expect("admin login", code)
admin_token = data.get("access_token")

code, data = req("POST", "/api/auth/login",
                 body={"email": "doctor@hospital.md", "password": "Doctor123!"})
expect("doctor login", code)
doctor_token = data.get("access_token")

code, data = req("POST", "/api/auth/login",
                 body={"email": "patient@hospital.md", "password": "Patient123!"})
expect("patient login", code)
patient_token = data.get("access_token")

# Refresh token
refresh = data.get("refresh_token")
code, _ = req("POST", "/api/auth/refresh", body={"refresh_token": refresh})
expect("token refresh", code)

# /me
code, _ = req("GET", "/api/auth/me", token=admin_token)
expect("admin GET /me", code)
code, _ = req("GET", "/api/auth/me", token=doctor_token)
expect("doctor GET /me", code)
code, _ = req("GET", "/api/auth/me", token=patient_token)
expect("patient GET /me", code)

# /api/auth/register should be GONE
code, _ = req("POST", "/api/auth/register",
              body={"email": "x@y.ro", "password": "Aaaa1234",
                    "first_name": "X", "last_name": "Y"})
if code == 404:
    print(f"  PASS  public /auth/register removed  [HTTP 404]"); passed += 1
else:
    print(f"  FAIL  public /auth/register still present  [HTTP {code}]")
    failed += 1; failures.append("register not removed")

# Wrong password (use valid length to pass pydantic validation)
code, _ = req("POST", "/api/auth/login",
              body={"email": "admin@hospital.md", "password": "wrongbutlong"})
if code == 401:
    print(f"  PASS  wrong password rejected  [HTTP 401]"); passed += 1
else:
    print(f"  FAIL  wrong password  [HTTP {code}]")
    failed += 1; failures.append("wrong password not rejected")

# ─── ADMIN ─────────────────────────────────────────────────
section("ADMIN")
code, _ = req("GET", "/api/admin/stats", token=admin_token)
expect("admin stats", code)

code, data = req("GET", "/api/admin/doctors", token=admin_token)
expect("list doctors", code)
doctors_before = len(data) if isinstance(data, list) else 0

# Create doctor
code, data = req("POST", "/api/admin/doctors", token=admin_token,
                 body={"email": f"test.doctor.{int(time.time())}@hospital.md",
                       "password": "TestDoctor1234",
                       "first_name": "TestFN", "last_name": "TestLN",
                       "specialty": "Cardiologie",
                       "experience_years": 5,
                       "schedules": [{"day_of_week": 0, "start_time": "09:00:00", "end_time": "17:00:00"}]})
expect("create doctor (admin)", code)
new_doctor_id = data.get("doctor_id") if isinstance(data, dict) else None

# Update doctor
if new_doctor_id:
    code, _ = req("PUT", f"/api/admin/doctors/{new_doctor_id}", token=admin_token,
                  body={"bio": "Updated bio", "experience_years": 6})
    expect("update doctor", code)
    code, _ = req("PUT", f"/api/admin/doctors/{new_doctor_id}/toggle-active", token=admin_token)
    expect("toggle doctor active", code)
    # toggle back
    req("PUT", f"/api/admin/doctors/{new_doctor_id}/toggle-active", token=admin_token)

# Patients admin
code, data = req("GET", "/api/admin/patients", token=admin_token)
expect("list patients", code)

code, data = req("POST", "/api/admin/patients", token=admin_token,
                 body={"email": f"test.patient.{int(time.time())}@hospital.md",
                       "password": "TestPatient1234",
                       "first_name": "Admin", "last_name": "CreatedPatient",
                       "phone": "+40700111222", "gender": "male"})
expect("create patient (admin)", code)
admin_patient_id = data.get("patient_id") if isinstance(data, dict) else None

if admin_patient_id:
    code, _ = req("GET", f"/api/admin/patients/{admin_patient_id}", token=admin_token)
    expect("get patient detail", code)
    code, _ = req("PUT", f"/api/admin/patients/{admin_patient_id}", token=admin_token,
                  body={"address": "Str Test 1, Cluj"})
    expect("update patient", code)

# Resources
code, data = req("GET", "/api/admin/resources", token=admin_token)
expect("list resources", code)
code, data = req("POST", "/api/admin/resources", token=admin_token,
                 body={"name": "Test Resource", "type": "supply",
                       "quantity": 100, "min_quantity": 10})
expect("create resource", code)
res_id = data.get("id") if isinstance(data, dict) else None
if res_id:
    code, _ = req("PUT", f"/api/admin/resources/{res_id}", token=admin_token,
                  body={"quantity": 150})
    expect("update resource", code)
    code, _ = req("DELETE", f"/api/admin/resources/{res_id}", token=admin_token)
    expect("delete resource", code)

# Beds
code, _ = req("GET", "/api/admin/beds", token=admin_token)
expect("list beds", code)

# Reports
code, _ = req("GET", "/api/admin/reports/occupancy", token=admin_token)
expect("report occupancy", code)
code, _ = req("GET", "/api/admin/reports/doctors-performance", token=admin_token)
expect("report doctor performance", code)
code, _ = req("GET", "/api/admin/reports/appointments", token=admin_token)
expect("report appointments", code)

# Admin should NOT access doctor endpoints
code, _ = req("GET", "/api/doctor/stats", token=admin_token)
if code == 403:
    print(f"  PASS  admin blocked from doctor endpoints  [HTTP 403]"); passed += 1
else:
    print(f"  FAIL  admin not blocked  [HTTP {code}]"); failed += 1

# ─── DOCTOR ────────────────────────────────────────────────
section("DOCTOR")
code, _ = req("GET", "/api/doctor/stats", token=doctor_token)
expect("doctor stats", code)
code, _ = req("GET", "/api/doctor/profile", token=doctor_token)
expect("doctor profile", code)
code, data = req("GET", "/api/doctor/appointments", token=doctor_token)
expect("doctor appointments list", code)
code, _ = req("GET", "/api/doctor/patients", token=doctor_token)
expect("doctor patients list", code)

code, data = req("POST", "/api/doctor/patients", token=doctor_token,
                 body={"email": f"doc.created.{int(time.time())}@hospital.md",
                       "password": "DocCreated1234",
                       "first_name": "Doctor", "last_name": "CreatedPatient",
                       "gender": "female"})
expect("doctor creates patient", code)

# Doctor blocked from admin
code, _ = req("GET", "/api/admin/stats", token=doctor_token)
if code == 403:
    print(f"  PASS  doctor blocked from admin endpoints  [HTTP 403]"); passed += 1
else:
    print(f"  FAIL  doctor not blocked  [HTTP {code}]"); failed += 1

# ─── PATIENT ───────────────────────────────────────────────
section("PATIENT")
code, _ = req("GET", "/api/patient/stats", token=patient_token)
expect("patient stats", code)
code, data = req("GET", "/api/patient/doctors", token=patient_token)
expect("patient list doctors", code)
first_doctor_id = data[0]["id"] if isinstance(data, list) and data else None

if first_doctor_id:
    code, _ = req("GET", f"/api/patient/doctors/{first_doctor_id}", token=patient_token)
    expect("patient get doctor detail", code)
    # Get slots for next Monday
    from datetime import date, timedelta
    today = date.today()
    next_mon = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    code, slots = req("GET", f"/api/patient/doctors/{first_doctor_id}/available-slots?date_str={next_mon}",
                      token=patient_token)
    expect("patient get available slots", code)

code, _ = req("GET", "/api/patient/appointments", token=patient_token)
expect("patient appointments list", code)
code, _ = req("GET", "/api/patient/history", token=patient_token)
expect("patient history", code)
code, _ = req("GET", "/api/patient/profile", token=patient_token)
expect("patient profile", code)

code, _ = req("GET", "/api/appointments/specialties", token=patient_token)
expect("list specialties", code)

# Patient blocked from admin
code, _ = req("GET", "/api/admin/stats", token=patient_token)
if code == 403:
    print(f"  PASS  patient blocked from admin  [HTTP 403]"); passed += 1
else:
    print(f"  FAIL  patient not blocked  [HTTP {code}]"); failed += 1

# Patient blocked from /doctor
code, _ = req("GET", "/api/doctor/stats", token=patient_token)
if code == 403:
    print(f"  PASS  patient blocked from doctor  [HTTP 403]"); passed += 1
else:
    print(f"  FAIL  patient not blocked from doctor  [HTTP {code}]"); failed += 1

# ─── ME (any role) ─────────────────────────────────────────
section("ME")
code, _ = req("GET", "/api/me", token=patient_token)
expect("GET /me (patient)", code)

# ─── NOTIFICATIONS ─────────────────────────────────────────
section("NOTIFICATIONS")
code, _ = req("GET", "/api/notifications", token=admin_token)
expect("notifications list", code)
code, _ = req("PUT", "/api/notifications/read-all", token=admin_token)
expect("mark all read", code)

# ─── CHAT ──────────────────────────────────────────────────
section("CHAT")
code, _ = req("GET", "/api/chat/conversations", token=doctor_token)
expect("doctor conversations", code)
code, _ = req("GET", "/api/chat/conversations", token=patient_token)
expect("patient conversations", code)

# ─── AI AGENTS (via backend proxy) ─────────────────────────
section("AI AGENTS (backend proxy)")
code, _ = req("GET", "/api/ai/agents", token=admin_token)
expect("AI agents metadata list", code)
code, _ = req("GET", "/api/ai/health", token=admin_token)
expect("AI health", code)

# Help agent — all roles
for role, tok in [("admin", admin_token), ("doctor", doctor_token), ("patient", patient_token)]:
    code, _ = req("POST", "/api/ai/help/ask", token=tok,
                  body={"question": "Ce să fac dacă am febră mare?"})
    expect(f"help agent ask ({role})", code)
    code, _ = req("POST", "/api/ai/help/ask", token=tok,
                  body={"question": "Что делать при высокой температуре?"})
    expect(f"help agent ask russian ({role})", code)

code, _ = req("GET", "/api/ai/help/faq", token=admin_token)
expect("help agent faq", code)

# Admin-only agents
code, _ = req("GET", "/api/ai/monitoring", token=admin_token)
expect("monitoring agent", code)
code, _ = req("GET", "/api/ai/predictions", token=admin_token)
expect("predictive agent", code)
code, _ = req("GET", "/api/ai/resources", token=admin_token)
expect("resource agent", code)
code, _ = req("GET", "/api/ai/scheduling", token=admin_token)
expect("scheduling agent (global)", code)
code, _ = req("GET", "/api/ai/recommendations-all", token=admin_token)
expect("recommendations all", code)
code, _ = req("GET", "/api/ai/notifications-status", token=admin_token)
expect("notification agent", code)

# Doctor-specific
code, _ = req("GET", "/api/ai/recommendations", token=doctor_token)
expect("doctor personalized recommendations", code)

# Scheduling slot suggestion
if first_doctor_id:
    from datetime import date
    code, _ = req("GET", f"/api/ai/scheduling/suggest-slots?doctor_id={first_doctor_id}&date={date.today()}",
                  token=patient_token)
    expect("AI slot suggestion", code)

# Registration agent (admin + doctor)
sample = """Nume: Popescu Ion
Data nașterii: 15.03.1985
Telefon: +40722111222
Adresă: Str. Libertății 12, București
Asigurare: RO9988776655
Email: popescu.ion@gmail.com
Sex: M"""

for role, tok in [("admin", admin_token), ("doctor", doctor_token)]:
    code, data = req("POST", "/api/ai/registration/parse", token=tok,
                     body={"text": sample})
    if expect(f"registration parse ({role})", code):
        ext = data.get("extracted", {}) if isinstance(data, dict) else {}
        method = data.get("method", "?") if isinstance(data, dict) else "?"
        print(f"         method={method}  fields={len(ext)}  confidence={data.get('confidence')}")

# Patient blocked from registration
code, _ = req("POST", "/api/ai/registration/parse", token=patient_token,
              body={"text": sample})
if code == 403:
    print(f"  PASS  patient blocked from /ai/registration  [HTTP 403]"); passed += 1
else:
    print(f"  FAIL  patient not blocked  [HTTP {code}]"); failed += 1

# ─── SECURITY ──────────────────────────────────────────────
section("SECURITY")
# No token
code, _ = req("GET", "/api/admin/stats")
if code in (401, 403):
    print(f"  PASS  no-token request rejected  [HTTP {code}]"); passed += 1
else:
    print(f"  FAIL  no-token accepted  [HTTP {code}]"); failed += 1

# Bogus token
code, _ = req("GET", "/api/admin/stats", token="bogus.token.here")
if code in (401, 403):
    print(f"  PASS  bogus token rejected  [HTTP {code}]"); passed += 1
else:
    print(f"  FAIL  bogus token accepted  [HTTP {code}]"); failed += 1

# ─── SUMMARY ───────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"PASSED: {passed}    FAILED: {failed}")
if failures:
    print("Failures:")
    for f in failures:
        print(f"  - {f}")
print("=" * 60)
sys.exit(0 if failed == 0 else 1)
