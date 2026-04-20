# Hospital DSS — Sistem Inteligent de Sprijin Decizional

Aplicație web pentru gestionarea unui spital cu **3 roluri** (Administrator, Medic, Pacient) și **8 agenți AI autonomi** (inclusiv NLP pentru întrebări medicale RO+RU și extragerea automată a datelor pacientului din documente).

---

## 1. Pornire rapidă (one-command)

```bash
docker compose up -d --build
```

După ~2-3 minute (prima rulare: build + antrenare modele AI), aplicația este accesibilă la:

- **Aplicația web:** http://localhost
- **Documentație API (Swagger):** http://localhost/docs
- **Documentație API (ReDoc):** http://localhost/redoc

Ulterior, `docker compose up -d` pornește tot stack-ul în ~10 secunde (imaginile sunt deja construite).

### Conturi demo (create automat de `seed_data.py` la pornire)

| Rol | Email | Parolă |
|---|---|---|
| Administrator | `admin@hospital.md` | `Admin123!` |
| Medic | `doctor@hospital.md` | `Doctor123!` |
| Pacient | `patient@hospital.md` | `Patient123!` |

**Intrare unică pentru toți**: pagina `/login`. Nu există înregistrare publică — conturile de pacient sunt create de administrator sau de medic.

---

## 2. Arhitectura (6 containere Docker)

```
       ┌────────────┐
 USER  │   NGINX    │ :80  ← reverse proxy + rate-limit + security headers
 ◄───► │ (alpine)   │
       └─────┬──────┘
             │
    ┌────────┴─────────┐
    │                  │
┌───▼────────┐   ┌─────▼──────┐
│  FRONTEND  │   │  BACKEND   │ :8000
│ React 18   │   │  FastAPI   │───────► PostgreSQL 15
│ TypeScript │   │  Socket.IO │  \
│ Tailwind   │   │  JWT auth  │   └──► Redis 7
└────────────┘   └─────┬──────┘
                       │ HTTP proxy
                       ▼
                 ┌──────────────┐
                 │  AI SERVICE  │ :8001
                 │  FastAPI     │
                 │  8 agenți    │
                 │  scikit-learn│
                 │  APScheduler │
                 └──────────────┘
```

**Dependencies**: `nginx` așteaptă `frontend` + `backend`; `backend` și `ai` așteaptă `postgres` + `redis` să fie `healthy`. Backend-ul rulează `seed_data.py` la pornire (creează admin, 6 medici, 10 pacienți, 60 programări, 30 paturi, 12 resurse). AI service-ul generează datele de antrenare și antrenează modelele la boot.

---

## 3. Stack tehnologic

| Componentă | Tehnologii |
|---|---|
| **Backend** | Python 3.11 · FastAPI · SQLAlchemy 2 · Pydantic 2 · Socket.IO · JWT · Bcrypt · Bleach (sanitizare) · SlowAPI (rate limit) |
| **Frontend** | React 18 · TypeScript 4 · Tailwind CSS · React Router v6 · Axios · socket.io-client · Recharts · Lucide React · simple-peer (WebRTC) |
| **AI / ML / NLP** | scikit-learn (RandomForest, GradientBoosting, IsolationForest, LogisticRegression, LinearSVC) · TF-IDF · Cosine Similarity · pandas · numpy · APScheduler |
| **Infra** | PostgreSQL 15 · Redis 7 · Nginx alpine · Docker Compose |

---

## 4. Fluxuri complete (ce face fiecare rol pas cu pas)

Toate fluxurile încep de la pagina unică **`/login`**. După autentificare, backend-ul returnează un JWT în care este codat rolul; frontend-ul redirecționează către dashboard-ul corespunzător rolului.

### 4.1 Flux Administrator (`/admin/*`)

```
LOGIN (admin@hospital.md)
   │
   ▼
/admin  ── Dashboard cu statistici live:
   │         • total paturi / ocupate / libere
   │         • nr. medici activi / totali
   │         • nr. pacienți
   │         • programări azi
   │         • resurse cu stoc scăzut
   │
   ├─► /admin/doctors
   │       • listă medici cu foto, specialitate, program, email, status
   │       • [Adaugă Medic] → modal cu:
   │              email, parolă, nume, prenume, specialitate,
   │              experiență, bio, telefon, cabinet, program săptămânal
   │       • [Editare] / [Upload foto] / [Activează ⇄ Dezactivează]
   │
   ├─► /admin/patients
   │       • listă pacienți cu email, telefon, asigurare, status
   │       • [Adaugă Pacient] → formular manual
   │       • [Adaugă cu AI] → ★ flux NLP descris în secțiunea 5.8
   │       • [Vedere detalii] → istoric programări
   │       • [Editează] / [Activează ⇄ Dezactivează]
   │
   ├─► /admin/resources    CRUD resurse (medicamente, echipamente, săli, consumabile)
   ├─► /admin/beds         Management paturi pe secții, asignare pacient ⇄ pat
   │
   ├─► /admin/reports      Rapoarte agregate:
   │       • ocupare paturi pe secții (%)
   │       • programări pe status/tip
   │       • performanță medici (rate completare, rating mediu)
   │
   ├─► /admin/ai-agents    ★ Panou AI:
   │       • vizualizare output toți agenții
   │       • run-all → execuție orchestrată
   │       • monitor live (alerte stoc, ocupare critică)
   │       • predicții (pacienți/paturi viitori)
   │
   └─► /admin/profile      Gestionare cont (nume, email, parolă, fotografie)
```

### 4.2 Flux Medic (`/doctor/*`)

```
LOGIN (doctor@hospital.md)
   │
   ▼
/doctor ── Dashboard:
   │         • programări azi
   │         • nr. pacienți proprii
   │         • mesaje necitite
   │         • programări în așteptare
   │         • AI: recomandări follow-up (agent 5)
   │
   ├─► /doctor/appointments
   │       • listă programări (filtre: status, dată)
   │       • [Confirmă] / [Refuză] → notifică pacientul automat
   │       • [Finalizează consultație] → adaugă note + creează conversație chat
   │
   ├─► /doctor/patients
   │       • grid carduri pacienți (cei care au avut programări)
   │       • [Pacient Nou] → modal creare directă (email, parolă, nume, etc.)
   │       • [Adaugă cu AI] → ★ flux NLP (secțiunea 5.8)
   │       • [Mesaj] → deschide chat cu pacient
   │
   ├─► /doctor/chat        Chat real-time (Socket.IO) cu pacienți:
   │       • mesaje text + upload fișiere
   │       • apel video (WebRTC peer-to-peer, semnalizare prin Socket.IO)
   │
   └─► /doctor/profile     Editare profil medical (bio, specialitate, telefon, program)
```

### 4.3 Flux Pacient (`/patient/*`)

```
LOGIN (patient@hospital.md)
   │
   ▼
/patient ── Dashboard:
   │         • următoarea programare
   │         • programări în total
   │         • mesaje necitite
   │         • acces rapid la AI Assistant (agent 7)
   │
   ├─► /patient/book
   │       1. căutare medic (filtru specialitate, rating, nume)
   │       2. selectare medic → vizualizare profil, recenzii
   │       3. selectare dată → ★ AI Scheduling Agent (agent 2)
   │          sugerează sloturile optime (score 0-1) din program
   │       4. alegere slot → creare programare status=PENDING
   │       5. notificare automată către medic
   │
   ├─► /patient/history    Istoric programări + posibilitate recenzie (1-5★)
   │
   ├─► /patient/chat       Chat real-time cu medicii cu care a avut programări
   │                       (conversațiile sunt auto-create la confirmarea programării)
   │
   ├─► /patient/ai         ★ Asistent Medical AI (agent 7 — NLP RO+RU)
   │       Răspunde la întrebări medicale: simptome, prim-ajutor, urgențe
   │
   └─► /patient/profile    Editare date personale, fotografie, parolă
```

---

## 5. Agenții AI — detalii și cum funcționează NLP

Serviciul AI rulează separat (`ai/api/agent_api.py`, port 8001). Backend-ul proxy-ează cererile frontend-ului către el prin endpoint-urile `/api/ai/*` (cu verificare rol). Modelele se antrenează la pornire (entrypoint.sh → `train_agents.py`) și se încarcă la runtime din fișiere pickle.

Detalii fiecărui model (acuratețe, F1, cross-validation) sunt salvate în `ai/models/reports/*.json`.

### 5.1 Resource Allocation Agent
- **Algoritm:** `RandomForestClassifier` (decizie realocare) + `GradientBoostingClassifier` (nivel urgență)
- **Date:** 1 500 exemple ocupare paturi (zi, oră, lună, secție, rată ocupare, zi internări)
- **Utilizare:** Admin `/api/ai/resources`, sugerare pat `/api/ai/resources/suggest-bed?ward=...`

### 5.2 Scheduling Agent
- **Algoritm:** `GradientBoostingClassifier` (detectare conflict) + `RandomForestRegressor` (scoring slot optim 0-1)
- **Date:** 1 200 programări sintetice cu etichete conflict
- **Utilizare:** pacientul cere sloturi pentru un medic → agent scorează fiecare slot disponibil după încărcare doctor, ora zilei, tip specialitate → frontend le afișează sortate.

### 5.3 Monitoring Agent
- **Algoritm:** `IsolationForest` (detectare anomalii consum) + `RandomForestClassifier` (nivel alertă)
- **Date:** 1 500 exemple stoc/rată consum/anomalii
- **Rulare:** automată la fiecare **10 min** via APScheduler. Crează notificări tip `urgent` pentru admini când: stoc < min, pat ocupat > 90%, echipament în mentenanță.

### 5.4 Predictive Agent (time-series)
- **Algoritm:** `GradientBoostingRegressor` cu lag features (t-1, t-7) + rolling means (7, 30 zile)
- **Date:** 1 000 zile cu sezonalitate (iarnă +30% pacienți, weekend -20%, sărbători)
- **Rulare:** automată la fiecare **1 oră**. Prezice nr. pacienți și paturi necesare pentru ziua următoare.

### 5.5 Recommendation Agent (hybrid)
- **Algoritm:** `TF-IDF` + `CosineSimilarity` pe condiții medicale (similaritate pacienți) + `RandomForestClassifier` (clasificare risc) + `LogisticRegression` (decizie follow-up)
- **Date:** 1 200 interacțiuni pacient-medic
- **Utilizare:** medic `/api/ai/recommendations` → listă pacienți cu risc înalt și propuneri follow-up.

### 5.6 Notification Agent
- **Algoritm:** `GradientBoostingClassifier` (prioritate) + `LogisticRegression` (canal push da/nu)
- **Date:** 1 000 notificări cu meta (tip, oră, rol, sensibilitate timp)
- **Rulare:** automată la fiecare **15 min**. Trimite reminder-uri cu 24h înainte de programare.

### 5.7 Help Agent — NLP pentru întrebări medicale (RO + RU)
Acesta este **primul agent NLP** al sistemului: răspunde la întrebări medicale în limbaj natural.

**Pipeline NLP:**
```
        întrebare (RO sau RU)
                 │
                 ▼
   ┌─────────────────────────────┐
   │ 1. Detectare limbă          │  ratio caractere chirilice >30% → RU, altfel RO
   └─────────────┬───────────────┘
                 ▼
   ┌─────────────────────────────┐
   │ 2. Vectorizare TF-IDF       │  n-grame (1-3), 500 features, sublinear TF
   │    (antrenat pe corpusul    │  corpus = 220+ perechi RO+RU + keywords
   │     multilingv)             │
   └─────────────┬───────────────┘
                 ▼
   ┌─────────────────────────────┐
   │ 3. Cosine Similarity        │  găsește cele mai similare top-5 perechi din corpus
   │    cu matricea corpus       │
   └─────────────┬───────────────┘
                 ▼
   ┌─────────────────────────────┐
   │ 4. Prag încredere 0.05      │  sub prag → mesaj fallback (sună 112)
   └─────────────┬───────────────┘
                 ▼
   ┌─────────────────────────────┐
   │ 5. LinearSVC                │  clasifică răspunsul pe categorie
   │    clasificare categorie    │  (simptome / urgență / prevenție / medicamente)
   └─────────────┬───────────────┘
                 ▼
      răspuns în limba întrebării
      + categorie + confidence + top-3 întrebări similare
```

**Metrici:** acuratețe retrieval RO ~95 %, RU ~90 % (vezi `ai/models/reports/help_agent_report.json`).

**Utilizare:** toți utilizatorii, via `POST /api/ai/help/ask` cu body `{"question": "..."}`. Frontend: pagina Patient AI Assistant.

### 5.8 Registration Agent — NLP pentru înregistrarea pacientului din documente (★ nou)

Acesta e **al doilea agent NLP** — extrage automat datele pacientului din text liber (buletin, card asigurare, fișă intake) și pre-completează formularul de creare cont.

**Pipeline hibrid (reguli + ML):**
```
         text intrare (RO sau RU, structurat sau liber)
                    │
                    ▼
   ┌────────────────────────────────────────┐
   │ PASS 1 — Extragere bazată pe reguli    │
   │                                        │
   │  a) Parsing "Cheie: valoare"           │
   │     dict de cuvinte-cheie RO+RU        │
   │     (Nume, Prenume, Data nașterii,     │
   │      Dată, Tel, Tel., Mobil,           │
   │      Телефон, Адрес, Полис, CNP, etc.) │
   │                                        │
   │  b) Regex:                             │
   │     • EMAIL = [\w.+-]+@[\w-]+\.[\w-]+ │
   │     • PHONE = +?\d{1,3}... grupuri 3-4 │
   │     • DATE  = DD.MM.YYYY | YYYY-MM-DD  │
   │     • INSURANCE = (RO|MD|CNP)?\d{10-16}│
   │                                        │
   │  c) Normalizări:                       │
   │     • data → ISO 8601                  │
   │     • telefon → doar +digits           │
   │     • gen (M/F/masculin/муж) → male/female │
   │     • "Nume: X Y" cu 2 cuvinte → split │
   │       last_name / first_name           │
   └────────────────┬───────────────────────┘
                    ▼
   ┌────────────────────────────────────────┐
   │ PASS 2 — ML pentru câmpurile lipsă     │
   │                                        │
   │  Pentru fiecare linie fără etichetă:   │
   │   1. TF-IDF char_wb n-gram (1-2)       │
   │      (char_wb = funcționează pentru    │
   │       RO + RU Cyrillic + diacritice)   │
   │   2. LogisticRegression multi-clasă    │
   │      prezice eticheta (first_name,     │
   │      last_name, phone, address,        │
   │      birth_date, insurance, email,     │
   │      gender, none)                     │
   │   3. Dacă probabilitate > 0.4:         │
   │      atribuie valoarea câmpului lipsă  │
   └────────────────┬───────────────────────┘
                    ▼
   ┌────────────────────────────────────────┐
   │ PASS 3 — Post-procesare                │
   │   • deduplicare (phone ≠ insurance)    │
   │   • propune email: nume.prenume@...    │
   │     dacă lipsește, din numele extrase  │
   │   • calculează confidence = coverage   │
   │     pe 5 câmpuri importante            │
   └────────────────┬───────────────────────┘
                    ▼
       JSON: {extracted: {...}, confidence: 0-1,
              fields_found: N, method: "rules"|"hybrid"}
```

**Antrenare model:**
- 3 000 linii sintetice generate de `generate_registration_data()` (200/câmp × 9 câmpuri etichetate + 600 distractori + 600 linii libere fără cheie)
- TF-IDF char_wb(1-2), 640 features, sublinear TF
- LogisticRegression multi-class
- **Acuratețe: 99.83 %**, F1-weighted: 0.9983, CV (5-fold): 0.9993 ± 0.0013

**Utilizare:**
- Admin: `/admin/patients` → buton **"Adaugă cu AI"** → textarea → AI parsează → formularul apare pre-completat → admin validează și salvează
- Medic: identic pe `/doctor/patients`
- Pacient: blocat (403) — doar admin+doctor pot înregistra pacienți
- Backend proxy: `POST /api/ai/registration/parse` cu body `{"text": "..."}`

**Exemplu real** (testat end-to-end pe stack-ul live):
```json
// INPUT:
{"text":"Nume: Popescu Ion\nData nașterii: 15.03.1985\nTelefon: +40722111222\nAdresă: Str. Libertății 12, București\nAsigurare: RO9988776655\nEmail: popescu.ion@gmail.com\nSex: M"}

// OUTPUT:
{
  "extracted": {
    "last_name": "Popescu",
    "first_name": "Ion",
    "birth_date": "1985-03-15",
    "phone": "+40722111222",
    "address": "Str. Libertății 12, București",
    "insurance_number": "RO9988776655",
    "email": "popescu.ion@gmail.com",
    "gender": "male"
  },
  "confidence": 1.0,
  "fields_found": 8,
  "method": "hybrid"
}
```

Funcționează și pe text **nestructurat** (fără etichete):
```
Popescu Ion
popescu.ion@yahoo.com
+40722333444
12.04.1990
Str. Florilor 7, Cluj
RO1234567890
```
→ extrage corect toate 7 câmpurile (method="hybrid").

---

## 6. API Endpoints (complete)

### Autentificare (`/api/auth`)
| Metodă | Path | Rol |
|---|---|---|
| POST | `/login` | public |
| POST | `/refresh` | public (cu refresh token) |
| GET | `/me` | orice autentificat |

> **Notă:** `POST /api/auth/register` a fost **eliminat intenționat**. Nu există înregistrare publică.

### Profil propriu (`/api/me`)
`GET / PUT /api/me` · `PUT /api/me/email` · `PUT /api/me/password` · `POST /api/me/photo` · `DELETE /api/me/photo`

### Admin (`/api/admin`) — rol ADMIN
- `GET /stats`
- `GET/POST /doctors` · `PUT /doctors/{id}` · `POST /doctors/{id}/photo` · `PUT /doctors/{id}/toggle-active`
- `GET/POST /patients` · `GET/PUT /patients/{id}` · `PUT /patients/{id}/toggle-active`
- `GET/POST /resources` · `PUT/DELETE /resources/{id}`
- `GET/POST /beds` · `PUT /beds/{id}`
- `GET /reports/{occupancy,appointments,doctors-performance}`

### Medic (`/api/doctor`) — rol DOCTOR
- `GET /stats` · `GET /profile` · `GET /appointments` · `PUT /appointments/{id}`
- `GET /patients` · `POST /patients` ★ nou

### Pacient (`/api/patient`) — rol PATIENT
- `GET /stats` · `GET/PUT /profile`
- `GET /doctors` · `GET /doctors/{id}` · `GET /doctors/{id}/available-slots?date_str=YYYY-MM-DD`
- `GET/POST /appointments` · `PUT /appointments/{id}/cancel`
- `GET /history` · `POST /reviews`
- `POST /chat-with-doctor/{doctor_id}`

### Chat & Notificări
- `GET/POST /api/chat/conversations` · `GET /api/chat/conversations/{id}/messages` · `POST /api/chat/conversations/{id}/upload`
- `GET /api/notifications` · `PUT /api/notifications/read-all` · `PUT /api/notifications/{id}/read`

### Agenți AI (`/api/ai`) — backend proxy către serviciul AI
| Endpoint | Rol | Agent |
|---|---|---|
| `GET /agents` | orice | metadata toți agenții |
| `GET /health` | orice | health-check serviciu AI |
| `POST /help/ask` · `GET /help/faq` | toți | 7 — NLP FAQ |
| `POST /registration/parse` · `GET /registration/info` | admin+doctor | 8 — NLP extragere date ★ |
| `GET /recommendations` | doctor | 5 — follow-up personalizat |
| `GET /scheduling/suggest-slots` | toți | 2 — sloturi optime |
| `GET /monitoring` · `/predictions` · `/resources` · `/scheduling` · `/recommendations-all` · `/notifications-status` · `/resources/suggest-bed` | admin | 1, 2, 3, 4, 5, 6 |

### Socket.IO (chat + video semnalizare)
Conexiune la `/socket.io/` cu JWT în query. Evenimente: `join_conversation`, `send_message`, `message`, `typing`, `video_offer`, `video_answer`, `ice_candidate`, `call_end`.

---

## 7. Modele de date (PostgreSQL — 13 tabele)

`users`, `doctors`, `doctor_schedules`, `patients`, `appointments`, `resources`, `beds`, `conversations`, `messages`, `notifications`, `reviews`, `agent_logs`, `agent_recommendations`.

Enum-urile Postgres stochează **numele** enum (uppercase: `AVAILABLE`, `CONFIRMED`, etc.), nu valorile lowercase — relevant dacă scrieți query-uri directe.

---

## 8. Securitate

| Protecție | Implementare |
|---|---|
| Autentificare | JWT access token (1h) + refresh token (7 zile) |
| Parole | Bcrypt (cost 12) |
| Autorizare | Role-guard FastAPI dependency (`require_role(ADMIN)` etc.) |
| Rate limit Nginx | 30 req/s general, 20 req/min auth, 10 req/min upload |
| XSS | Bleach sanitize pe toate textele user-input (sanitize_string) |
| SQL Injection | SQLAlchemy parametrizat (niciun string concat) |
| Upload fișiere | Validare MIME + magic bytes + dimensiune ≤ 5 MB |
| Security headers | `X-Frame-Options`, `X-Content-Type-Options`, `X-XSS-Protection`, `Referrer-Policy` |
| Path traversal | `/api/uploads/{path}` verifică `realpath` este în UPLOAD_DIR |

---

## 9. Antrenare manuală agenți AI

```bash
# Intră în containerul AI
docker exec -it automatizare-spital-ai-1 bash

# Generează doar datele sintetice (toți agenții)
cd /app/models && python generate_training_data.py

# Antrenează toți cei 8 agenți
python train_agents.py

# Un agent specific
python train_agents.py --agent registration   # ★ nou
python train_agents.py --agent help
python train_agents.py --agent resource

# Rapoartele sunt salvate în /app/models/reports/*.json
# Modelele pickle în /app/models/saved_models/*_latest.pkl
```

---

## 10. Testare

Suita completă de teste E2E (`tests/e2e_smoke.py`) rulează 70 de verificări acoperind:
- Autentificare toți 3 rolurile + refresh token + /me
- Verificare că `/api/auth/register` este eliminat (404)
- 16 operațiuni CRUD admin (medici, pacienți, resurse, paturi, rapoarte)
- 6 operațiuni doctor (stats, profile, appointments, pacienți, creare pacient, blocare cross-role)
- 9 operațiuni pacient (doctori, sloturi, programări, istoric, specialități, blocări)
- Chat + notificări
- Toți **8 agenți AI** (inclusiv întrebări RO + RU)
- Autorizare: tokens invalide, lipsă token, acces cross-role

Rulare (cu stack-ul pornit):
```bash
python tests/e2e_smoke.py
```
Rezultat actual: **70/70 PASSED**.

---

## 11. Structura proiectului

```
├── docker-compose.yml           # 6 servicii cu healthcheck-uri
├── nginx/nginx.conf             # reverse proxy + rate limit
├── backend/
│   ├── Dockerfile · entrypoint.sh · requirements.txt
│   ├── seed_data.py             # admin/6 medici/10 pacienți/60 programări/30 paturi
│   └── app/
│       ├── main.py              # FastAPI + Socket.IO
│       ├── config.py · database.py · schemas.py
│       ├── models/              # 11 modele SQLAlchemy
│       ├── routes/              # auth, admin, doctor, patient, ai, chat, video, me, notifications, resources, appointments
│       ├── services/            # auth, email, patient (shared creation), notification
│       ├── security/            # sanitizer, validators, rate_limiter
│       └── websocket/           # chat_handler.py + video_handler.py
├── frontend/
│   ├── Dockerfile · package.json · tsconfig.json · tailwind.config.js
│   └── src/
│       ├── App.tsx              # routing + ProtectedRoute per rol
│       ├── contexts/AuthContext.tsx
│       ├── services/            # api.ts (Axios + interceptor refresh) + socket.ts
│       ├── components/          # DashboardLayout, Sidebar, Chat/, Video/, UI/
│       └── pages/
│           ├── auth/LoginPage.tsx          # intrare unică
│           ├── admin/{Dashboard,Doctors,Patients,Resources,Beds,Reports,AIAgents}.tsx
│           ├── doctor/{Dashboard,Appointments,Patients,Chat}.tsx
│           ├── patient/{Dashboard,BookAppointment,History,Chat,AIAssistant}.tsx
│           └── Profile.tsx
└── ai/
    ├── Dockerfile · entrypoint.sh · requirements.txt
    ├── agents/                  # 8 agenți (inclusiv registration_agent.py ★)
    ├── api/agent_api.py         # FastAPI expune toți agenții
    └── models/
        ├── db.py                # modele read-only pentru citire DB principală
        ├── generate_training_data.py
        ├── train_agents.py      # antrenare + versionare + rapoarte
        ├── training_data/
        └── saved_models/        # .pkl versionate + _latest.pkl
```

---

## 12. Checklist portabilitate (pornire pe alt calculator)

1. Instalează Docker Desktop (Windows/Mac) sau docker + docker-compose (Linux)
2. `git clone <repo>` și `cd Automatizare-spital`
3. `docker compose up -d --build`
4. Deschide http://localhost și autentifică-te cu `admin@hospital.md / Admin123!`

Singurul prerequisit în afara Docker: **portul 80 liber**. Toate celelalte servicii (Postgres, Redis, Python, Node) rulează în containere — nimic nu trebuie instalat pe host.
