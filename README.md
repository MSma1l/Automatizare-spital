# Hospital DSS - Sistem Inteligent de Sprijin Decizional

Aplicație web completă pentru gestionarea resurselor spitalicești cu 3 roluri (Administrator, Medic, Pacient) și 7 agenți AI autonomi.

## Pornire rapidă

```bash
docker-compose up --build
```

Aplicația va fi disponibilă la: **http://localhost**

## Conturi Demo

| Rol | Email | Parolă |
|-----|-------|--------|
| Administrator | admin@hospital.md | Admin123! |
| Medic | doctor@hospital.md | Doctor123! |
| Pacient | patient@hospital.md | Patient123! |

## Stack Tehnologic

### Backend
- Python 3.11 + FastAPI + Uvicorn
- PostgreSQL 15 (baza de date principală)
- Redis 7 (cache și sesiuni)
- SQLAlchemy ORM + Alembic (migrări)
- JWT (autentificare) + Bcrypt (parole)
- Socket.IO (chat real-time + video signaling)
- WebRTC (comunicare video peer-to-peer)

### Frontend
- React 18 + TypeScript
- TailwindCSS + componente custom
- Axios (API calls) + Socket.io-client
- Recharts (grafice și vizualizări)
- Lucide React (iconițe)
- React Big Calendar (calendar programări)

### AI/Agenți
- scikit-learn (RandomForest, GradientBoosting, IsolationForest, LogisticRegression)
- TF-IDF + Cosine Similarity (recomandări + Q&A)
- pandas + numpy (procesare date)
- APScheduler (execuție periodică agenți)
- Date de antrenare sintetice (1000+ per agent)
- Q&A medical bilingv (română + rusă, 40+ perechi extensibile)

### DevOps
- Docker + Docker Compose (6 servicii)
- Nginx (reverse proxy + rate limiting + security headers)

## Structura Proiectului

```
├── docker-compose.yml          # Orchestrare 6 servicii
├── nginx/
│   └── nginx.conf              # Reverse proxy + rate limiting
├── backend/
│   ├── Dockerfile
│   ├── entrypoint.sh           # Seed DB + start server
│   ├── requirements.txt
│   ├── seed_data.py            # Date demo (medici, pacienți, programări)
│   ├── alembic.ini
│   ├── migrations/
│   └── app/
│       ├── main.py             # FastAPI app + Socket.IO
│       ├── config.py           # Configurare (env vars)
│       ├── database.py         # SQLAlchemy engine + sessions
│       ├── schemas.py          # Pydantic schemas (validare)
│       ├── models/             # 11 modele SQLAlchemy
│       ├── routes/             # 8 routere API
│       ├── services/           # Auth, notificări, email
│       ├── security/           # Sanitizare, rate limiting, validări
│       └── websocket/          # Chat + Video handlers
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx             # Routing + protected routes
│       ├── contexts/           # AuthContext (JWT + state)
│       ├── services/           # API client + Socket.IO
│       ├── components/         # Layout, Sidebar, Notifications
│       └── pages/
│           ├── auth/           # Login + Register
│           ├── admin/          # Dashboard, Medici, Pacienți, Resurse, Paturi, Rapoarte
│           ├── doctor/         # Dashboard, Programări, Pacienți, Chat
│           └── patient/        # Dashboard, Programare, Istoric, Chat
└── ai/
    ├── Dockerfile
    ├── entrypoint.sh           # Generate data + train + start server
    ├── requirements.txt
    ├── agents/                 # 7 agenți AI
    │   ├── base_agent.py
    │   ├── resource_agent.py   # Agent 1: Alocare resurse
    │   ├── scheduling_agent.py # Agent 2: Optimizare programări
    │   ├── monitoring_agent.py # Agent 3: Monitorizare resurse
    │   ├── predictive_agent.py # Agent 4: Predicții cerere
    │   ├── recommendation_agent.py # Agent 5: Recomandări medici
    │   ├── notification_agent.py   # Agent 6: Gestionare notificări
    │   └── help_agent.py       # Agent 7: Asistent FAQ medical (RO+RU)
    ├── models/
    │   ├── db.py               # Modele DB pentru AI service
    │   ├── generate_training_data.py  # Generator date sintetice
    │   ├── train_agents.py     # Script complet antrenare
    │   ├── saved_models/       # Modele pickle salvate
    │   ├── reports/            # Rapoarte evaluare JSON
    │   └── training_data/      # CSV + JSON date antrenare
    │       └── help_agent_qa.json  # 40+ Q&A bilingv (RO+RU)
    └── api/
        └── agent_api.py        # FastAPI endpoints pentru agenți
```

## Agenți AI - Detalii

### Agent 1: Resource Allocation
- **Model:** RandomForestClassifier + GradientBoostingClassifier
- **Date:** 1500 exemple ocupare paturi (sezonalitate, secții, ore)
- **Funcție:** Detectează nevoia de realocare, calculează urgența, sugerează pat optim

### Agent 2: Scheduling
- **Model:** GradientBoosting (conflicte) + RandomForestRegressor (scoring sloturi)
- **Date:** 1200 programări cu conflict detection
- **Funcție:** Detectează conflicte, identifică medici suprasolicitați, scoring sloturi optime

### Agent 3: Monitoring
- **Model:** IsolationForest (anomalii) + RandomForest (nivel alertă)
- **Date:** 1500 înregistrări resurse cu anomalii
- **Funcție:** Detectează stoc scăzut, echipamente defecte, anomalii consum

### Agent 4: Predictive
- **Model:** GradientBoostingRegressor cu lag features + rolling means
- **Date:** 1000 zile time series (sezonalitate, weekend, sărbători)
- **Funcție:** Prezice pacienți/zi, cerere paturi, tendințe

### Agent 5: Recommendation
- **Model:** TF-IDF + Cosine Similarity + RandomForest (risc) + LogisticRegression (follow-up)
- **Date:** 1200 interacțiuni pacient-medic cu condiții, investigații, tratamente
- **Funcție:** Recomandări follow-up, clasificare risc pacienți, similaritate pacienți

### Agent 6: Notification
- **Model:** GradientBoosting (prioritate) + LogisticRegression (push/nu)
- **Date:** 1000 notificări cu tipuri, priorități, canale
- **Funcție:** Clasificare prioritate, decizie canal notificare, reminders automate

### Agent 7: Help (FAQ Medical)
- **Model:** TF-IDF + Cosine Similarity + LinearSVC (categorie)
- **Date:** 40+ perechi Q&A bilingve (română + rusă)
- **Funcție:** Răspunde la întrebări medicale, triaj simptome, ghidare urgențe
- **Limbi:** Română + Rusă (detectare automată)

## Antrenare manuală agenți

```bash
# Intră în containerul AI
docker exec -it automatizare-spital-ai-1 bash

# Generează doar datele
cd /app/models && python generate_training_data.py

# Antrenează toți agenții
python train_agents.py

# Antrenează un agent specific
python train_agents.py --agent help
python train_agents.py --agent resource

# Rapoartele sunt în /app/models/reports/
# Modelele sunt în /app/models/saved_models/
```

## Securitate

- JWT access tokens (1h) + refresh tokens (7 zile)
- Bcrypt hashing parole
- Rate limiting: 30 req/s API, 5 req/min auth, 10 req/min upload
- Sanitizare XSS (bleach) pe toate input-urile
- Validare fișiere upload (tip MIME, magic bytes, dimensiune max 5MB)
- SQL injection protection prin SQLAlchemy ORM parametrizat
- Security headers Nginx (X-Frame-Options, X-Content-Type-Options, XSS-Protection)
- CORS configurat

## API Endpoints

### Auth
- `POST /api/auth/login` - Autentificare
- `POST /api/auth/register` - Înregistrare pacient
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Profil curent

### Admin
- `GET /api/admin/stats` - Statistici dashboard
- `GET/POST /api/admin/doctors` - Lista / creare medici
- `PUT /api/admin/doctors/:id` - Editare medic
- `GET/POST /api/admin/patients` - Lista / editare pacienți
- `GET/POST/PUT/DELETE /api/admin/resources` - CRUD resurse
- `GET/POST/PUT /api/admin/beds` - CRUD paturi
- `GET /api/admin/reports/*` - Rapoarte (ocupare, programări, performanță)

### Doctor
- `GET /api/doctor/stats` - Statistici personale
- `GET /api/doctor/appointments` - Programări cu filtre
- `PUT /api/doctor/appointments/:id` - Confirmare/refuz/finalizare
- `GET /api/doctor/patients` - Pacienți proprii

### Patient
- `GET /api/patient/stats` - Statistici personale
- `GET /api/patient/doctors` - Medici disponibili
- `GET /api/patient/doctors/:id/available-slots` - Sloturi libere
- `POST /api/patient/appointments` - Creare programare
- `GET /api/patient/history` - Istoric medical

### Chat & Notifications
- `GET /api/chat/conversations` - Lista conversații
- `GET /api/chat/conversations/:id/messages` - Mesaje
- `GET /api/notifications` - Notificări

### AI Agents
- `GET /ai:8001/agents/resources` - Agent alocare resurse
- `GET /ai:8001/agents/scheduling` - Agent programări
- `GET /ai:8001/agents/monitoring` - Agent monitorizare
- `GET /ai:8001/agents/predictions` - Agent predictiv
- `GET /ai:8001/agents/recommendations` - Agent recomandări
- `POST /ai:8001/agents/help/ask` - Agent FAQ medical
- `POST /ai:8001/agents/run-all` - Rulează toți agenții

## Baza de Date

13 tabele PostgreSQL: users, doctors, doctor_schedules, patients, appointments, resources, beds, conversations, messages, notifications, reviews, agent_logs, agent_recommendations
