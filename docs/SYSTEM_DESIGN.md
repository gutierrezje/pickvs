# PickVs (MVP) - System Design

## 1. System Architecture Overview

The system uses a **decoupled Hybrid Cloud Architecture** as defined in [ARCHITECTURE.md](ARCHITECTURE.md).

### Tier 1: Frontend (Client)

| Aspect | Details |
|--------|---------|
| **Technology** | React (Vercel/Netlify) |
| **Responsibility** | All user-facing rendering and interaction |

### Tier 2: Backend (Server)

| Aspect | Details |
|--------|---------|
| **Technology** | FastAPI on Render |
| **Responsibility** | Handles all business logic, user authentication, and database interactions. Serves JSON data to the frontend. |

### Tier 3: Database (Data Layer)

| Aspect | Details |
|--------|---------|
| **Technology** | Neon (PostgreSQL Serverless) |
| **Responsibility** | Provides persistent, managed storage for all application data |

### Component: Task Runner (Data Ingestion)

| Aspect | Details |
|--------|---------|
| **Technology** | AWS Lambda (Python) |
| **Responsibility** | Serverless functions to run our data ingestion scripts |

### Component: Scheduler

| Aspect | Details |
|--------|---------|
| **Technology** | Amazon EventBridge |
| **Responsibility** | The "cron" scheduler that triggers our Lambda functions |

---

## 2. Component Deep Dive

### 2.1. Frontend (React)

It just calls the API.

### 2.2. Backend (FastAPI on Render)

- **Framework**: FastAPI with all endpoints using `async def`
- **Data Validation**: Request and response bodies strictly defined using Pydantic models
  - Makes the API self-documenting and robust
- **Database Driver**: Uses `asyncpg` to connect to Neon (pooler endpoint)
  - Enables non-blocking, asynchronous database queries
  - Works seamlessly with FastAPI's event loop
- **Business Logic**: Enforces all application rules (e.g., "Has this game already started?")

### 2.3. Task Runner (AWS Lambda + EventBridge)

This is the system's engine for data ingestion.

#### fetch-odds-lambda

- **Trigger**: Amazon EventBridge rule `(0 5 * * *)` — runs daily at 5:00 AM
- **Runtime**: Python 3.10+
- **Actions**:
  - Makes 1 API call to The Odds API for all upcoming NBA games
  - Connects to the Neon database using asyncpg (pooler endpoint)
  - UPSERTs game data into the `Games` table
  - INSERTs new odds into the `Odds` table
- **Key Permissions** (IAM Role):
  - AWS Secrets Manager access (to retrieve DB credentials)
  - No VPC configuration needed (Neon pooler endpoint is publicly accessible)
- **Quota**: 1 request/day

#### process-results-lambda

- **Trigger**: Amazon EventBridge rule `(0 9 * * *)` — runs daily at 9:00 AM
- **Runtime**: Python 3.10+
- **Actions**:
  - Makes 1 API call to The Odds API scores endpoint
  - Updates `Games` table in Neon with final scores
  - Calls the `grade_all_pending_picks()` logic (part of this Lambda function)
- **Key Permissions** (IAM Role):
  - Same as `fetch-odds-lambda`
- **Quota**: 1 request/day

---

## 3. Key Processes & Logic

### 3.1. Pick Grading Logic (grade_all_pending_picks)

This logic is part of the `process-results-lambda` function.

**Process**:

1. Find all picks in Neon where `result_units IS NULL` and the associated game status is `'Finished'`
2. Loop through each pick (using async operations):
   - Apply grading logic for Moneyline, Spread, and Total bet types:
     - **Win**: `result_units = (odds_at_pick - 1.0) * stake_units`
     - **Loss**: `result_units = -1.0 * stake_units`
     - **Push**: `result_units = 0.0`
   - `UPDATE Picks SET result_units = ...`
3. After all picks are graded, call `update_leaderboard_stats()`

### 3.2. Leaderboard Calculation (update_leaderboard_stats)

This logic is also part of the `process-results-lambda` function.

**Process**:

- Aggregates all graded picks for each user into performance statistics:
  - `total_units`: Sum of all `result_units` across all picks
  - `total_wagered`: Count of all picks (each pick = 1 unit wagered)
  - `roi`: `(total_units / total_wagered) * 100` (percentage return on investment)
- Updates the `Users` table with these aggregated metrics
- Executes via `asyncpg` for non-blocking database operations

---

## 4. API Endpoint Definitions (FastAPI)

**Base URL**: `/api`

> **Note**: All request/response bodies are defined as Pydantic models in the FastAPI code, providing automatic data validation. The JSON structure remains the same as the "contract" with the frontend.

### Auth Endpoints

#### POST /auth/register

- **Body** (Pydantic Model): `{ "username", "email", "password" }`
- **Response** (201): `{ "token": "jwt_token_string" }`

#### POST /auth/login

- **Body** (Pydantic Model): `{ "email", "password" }`
- **Response** (200): `{ "token": "jwt_token_string" }`

### Game Endpoints (Read-Only)

#### GET /api/games/upcoming

- **Authentication**: Required (JWT token)
- **Response** (200):
  ```json
  [
    {
      "game_id": "uuid",
      "home_team": "Los Angeles Lakers",
      "away_team": "Golden State Warriors",
      "game_timestamp": "2024-11-20T22:30:00Z",
      "status": "Scheduled",
      "odds": [
        {
          "market_type": "moneyline",
          "home_odds": 1.91,
          "away_odds": 1.91
        },
        {
          "market_type": "spread",
          "spread_value": -6.5,
          "home_odds": 1.91,
          "away_odds": 1.91
        },
        {
          "market_type": "total",
          "spread_value": 220.5,
          "home_odds": 1.91,
          "away_odds": 1.91
        }
      ]
    }
  ]
  ```

### Pick Endpoints (Authenticated)

#### POST /api/picks

- **Authentication**: Required (JWT token)
- **Body** (Pydantic Model):
  ```json
  {
    "picks": [
      {
        "game_id": "uuid",
        "market_picked": "spread",
        "outcome_picked": "Los Angeles Lakers",
        "odds_at_pick": 1.91
      }
    ]
  }
  ```
- **Response** (201): `{ "status": "success", "picks_created": 1 }`

#### GET /api/picks/me

- **Authentication**: Required (JWT token)
- **Response** (200): A list of the user's picks

### Leaderboard Endpoints (Public)

#### GET /api/leaderboard

**Primary: Lifetime Rankings**

- **Query Parameters**:
  - `sort_by`: `'roi'` | `'total_units'` | `'accuracy'` (default: `'roi'`)
- **Response** (200):
  ```json
  {
    "type": "lifetime",
    "min_picks_required": 20,
    "leaderboard": [
      {
        "rank": 1,
        "username": "string",
        "total_units": number,
        "total_wagered": number,
        "roi": number (percentage),
        "accuracy": number (win_rate percentage),
        "picks_since_minimum": number (picks above the 20-pick threshold)
      }
    ]
  }
  ```
- **Notes**:
  - Only users with `total_wagered >= 20` are included
  - Sorted by ROI descending, then total_units descending
  - Represents long-term skill and consistency
  - Late starters see exactly how many picks they need to rank

#### GET /api/leaderboard?period=weekly

**Secondary: This Week's Leaders**

- **Query Parameters**:
  - `period`: `'weekly'` | `'lifetime'` (default: `'lifetime'`)
  - `days`: number (default: 7, overrides period parameter)
- **Response** (200):
  ```json
  {
    "type": "weekly",
    "period_days": 7,
    "leaderboard": [
      {
        "rank": 1,
        "username": "string",
        "total_units": number,
        "total_wagered": number,
        "roi": number (percentage),
        "accuracy": number (win_rate percentage)
      }
    ]
  }
  ```
- **Notes**:
  - No minimum picks requirement (fresh start weekly)
  - Shows momentum and current form
  - Encourages late starters and new users
  - Resets every 7 days

---

## 5. Database Schema & Deployment

The schema defined in [SCHEMA.md](SCHEMA.md) is deployed on **Neon PostgreSQL**.

### Database Details

- **Provider**: Neon (serverless PostgreSQL)
- **Connection Method**: Standard endpoint for development, Pooler endpoint for Lambda
- **Connection Pooling**: Built-in via PgBouncer (up to 10,000 concurrent connections)
- **Pricing**: Free tier (0.5 GB, 100 compute hours/month) + scale-to-zero in idle periods
- **Key Advantage**: No VPC configuration needed, automatic connection pooling for Lambda, easier to scale

See [ARCHITECTURE.md - Database Connection Details](ARCHITECTURE.md#5-database-connection-details-neon) for connection strings and environment variable setup.


## Related Documentation
- [BACKEND_REQUIREMENTS.md](BACKEND_REQUIREMENTS.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)

