# PickVs (MVP) - System Architecture

## 1. Overview

This document outlines the system architecture for the PickVS  MVP. The design is a Hybrid Cloud Architecture that combines Platform-as-a-Service (PaaS) for the API with serverless AWS services for the database and data ingestion.

This decoupled design is critical to meeting the non-functional requirement (N-4.1) of staying within The Odds API's 500 requests/month free tier. The user-facing web application will not call The Odds API directly.

## 2. Core Components & Technology

| Layer | Component | Technology | Purpose |
|-------|-----------|-----------|---------|
| Frontend | Client-Side Web App | React | Provides the User Interface (UI). Deployed on Vercel/Netlify. |
| Backend | Server-Side API | Python (FastAPI) | The "brain" that handles auth and business logic. Deployed on Render. |
| Database | Data Layer | Neon (PostgreSQL Serverless) | Serverless PostgreSQL with built-in connection pooling. Zero cold starts, scale-to-zero pricing. |
| Task Runner | Data Ingestion Engine | AWS Lambda | Serverless functions that run our Python scripts (fetch_odds, process_results). |
| Scheduler | Cron Service | Amazon EventBridge | The "cron" scheduler that triggers our Lambda functions on a daily schedule. |

## 3. Architecture Diagram

The system operates on two distinct data flows:

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PICKVS ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────┘

USER INTERACTION FLOW
══════════════════════════════════

    React App              FastAPI Backend            Neon Database
   (Vercel)    ───────→      (Render)       ───────→  (Serverless PG)
     [UI]     ← ─ ─ ─ ─     [Auth, API]     ← ─ ─ ─   [Tables]
   Browser                  Business Logic            Games
                                                      Odds
                                                      Picks
                                                      Users


DATA INGESTION FLOW
═════════════════════════════════

  Amazon EventBridge              AWS Lambda Functions            Neon Database
    (Scheduler)                    (Serverless)                   (Serverless PG)
       │
       ├──(Daily 5 AM)───→  fetch-odds-lambda    ───→  Odds API
       │                        ↓                       │
       │                    Parse & Format              │
       │                        ↓ ──────────────────→ [Games & Odds]
       │
       └──(Daily 9 AM)───→  process-results-lambda ──→  Odds API
                               ↓                        │
                          Fetch Results                 │
                               ↓ ──────────────────→ [Games]
                          Grade Picks                [Picks]
                               ↓ ──────────────────→ [Users]
                          Update Leaderboard
```

**User Interaction Flow**: A user interacts with the React App (Vercel), which only communicates with our FastAPI Backend (Render). The API reads/writes to our Neon Database.

**Data Ingestion Flow**: Amazon EventBridge (the scheduler) triggers two AWS Lambda Functions. These functions call the external Odds API, then write the fetched data directly into our Neon Database.

## 4. Data Flows

### 4.1. Data Ingestion Flow (Scheduled Task via AWS)

This flow is the most critical part of the architecture, designed to use only 2 API requests per day.

**Task 1: Fetch Odds** (Runs 1x daily, e.g., 5:00 AM)
- Amazon EventBridge rule triggers `fetch-odds-lambda`
- Lambda makes 1 API call to The Odds API for `basketball_nba`
- Parses JSON and writes to Neon (`Games` and `Odds` tables)
- **Quota Used**: 1 Request

**Task 2: Fetch Results** (Runs 1x daily, e.g., 9:00 AM next day)
- Amazon EventBridge rule triggers `process-results-lambda`
- Lambda makes 1 API call to The Odds API scores endpoint
- Updates `Games` table in Neon with final scores
- **Quota Used**: 1 Request

**Task 3: Grade Picks** (Runs immediately after Task 2)
- Logic is part of `process-results-lambda`
- **API Calls**: 0 (internal database operations only)
- Queries Neon for all `Picks` where game status is `Finished`
- Calculates `result_units` and updates `Picks` table
- Aggregates results into `Users` table (updates `total_units`, `total_wagered`, `roi`)

**Total API Usage**: ~60 requests/month, safely within the 500-request free limit ✓

---

### 4.2. User Interaction Flow (Web API on Render)

This flow never calls The Odds API. It only interacts with Neon via the FastAPI backend.

**User Registers/Logs In** → `POST /auth/register`
- Frontend sends: email, password
- Backend (FastAPI) validates request, hashes password, creates `Users` record in Neon
- Backend returns: JWT token

**User Views Games to Pick** → `GET /api/games/upcoming`
- Frontend sends: JWT token
- Backend (FastAPI) queries Neon for scheduled games and their odds
- Backend returns: JSON list of games with odds

**User Submits Picks** → `POST /api/picks`
- Frontend sends: JWT token + list of picks
- Backend (FastAPI) validates that game status is `'Scheduled'`
- Backend saves new records to `Picks` table in Neon
- Backend returns: confirmation

**User Views Leaderboard** → `GET /api/leaderboard`
- Frontend requests leaderboard data (no auth required)
- Backend (FastAPI) queries Neon (username, total_units, roi, etc.)
- Backend returns: JSON array of ranked users

## 5. Database Connection Details (Neon)

### Connection Configuration

All components (Render FastAPI backend, AWS Lambda functions) connect to Neon using the **pooler endpoint** with connection pooling enabled:

**Standard Endpoint** (for long-lived connections):
```
postgresql://user:password@[project-id].us-east-1.postgres.neon.tech:5432/pickvs
```

**Pooler Endpoint** (for Lambda & short-lived connections - RECOMMENDED):
```
postgresql://user:password@[project-id]-pooler.us-east-1.postgres.neon.tech:5432/pickvs
```

**Why use the pooler endpoint?**
- Automatically manages connection pooling via PgBouncer
- Critical for AWS Lambda (prevents connection limit errors)
- Render FastAPI backend can use either endpoint
- Supports up to 10,000 concurrent connections

### Environment Variables

Store in `.env` (local development) and platform secrets:

```bash
# Neon Connection (Pooler - for Lambda)
DATABASE_URL_POOLER=postgresql://[user]:[password]@[project-id]-pooler.us-east-1.postgres.neon.tech:5432/pickvs

# Neon Connection (Standard - for Render API if preferred)
DATABASE_URL=postgresql://[user]:[password]@[project-id].us-east-1.postgres.neon.tech:5432/pickvs

# AWS Secrets Manager (for Lambda)
AWS_SECRET_NAME=pickvs/database-url-pooler
```

### asyncpg Connection String Example (Python/Lambda)

```python
import asyncpg

# For Lambda functions (use pooler endpoint)
DATABASE_URL = "postgresql://user:password@[project-id]-pooler.us-east-1.postgres.neon.tech:5432/pickvs"

async def connect_db():
    conn = await asyncpg.connect(DATABASE_URL)
    return conn
```

## 6. Core Database Schema

(The schema defined in [SCHEMA.md](SCHEMA.md) - deployed on Neon PostgreSQL)

## Related Document
- [BACKEND_REQUIREMENTS.md](BACKEND_REQUIREMENTS.md)