# Hospital DSS - Sistem Inteligent de Sprijin Decizional

Aplicație web completă pentru gestionarea resurselor spitalicești cu 3 roluri (Administrator, Medic, Pacient) și 7 agenți AI.

## Quick Start

```bash
docker-compose up --build
```

Aplicația va fi disponibilă la: **http://localhost**

## Conturi Demo

| Rol | Email | Parolă |
|-----|-------|--------|
| Administrator | admin@spital.ro | admin123 |
| Medic | dr.popescu@spital.ro | doctor123 |
| Pacient | ion.vasile@email.ro | pacient123 |

## Stack Tehnologic

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + PostgreSQL 15 + Redis
- **Frontend**: React 18 + TypeScript + TailwindCSS
- **AI**: scikit-learn + transformers + 7 agenți autonomi
- **Infra**: Docker Compose + Nginx

## Structura Proiectului

```
├── docker-compose.yml
├── nginx/nginx.conf
├── backend/          # FastAPI + PostgreSQL + Redis
├── frontend/         # React + TypeScript + TailwindCSS
└── ai/               # AI Agents Service
```

## Agenți AI

1. **Resource Allocation** - Optimizare alocarea paturilor
2. **Scheduling** - Optimizare programări
3. **Monitoring** - Monitorizare resurse în timp real
4. **Predictive** - Predicție cerere viitoare
5. **Recommendation** - Recomandări personalizate medici
6. **Notification** - Gestionare notificări
7. **Help** - Asistent virtual medical FAQ
