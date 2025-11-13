AlgoRank (MVP) - System Design

Owner: Engineering
Status: Draft 2.0 (AWS Hybrid)
Related Documents: product_requirements.md, architecture.md

1. System Architecture Overview

As defined in architecture.md, the system uses a decoupled Hybrid Cloud Architecture.

Tier 1: Frontend (Client)

Technology: React (Vercel/Netlify)

Responsibility: All user-facing rendering and interaction.

Tier 2: Backend (Server)

Technology: FastAPI on Render

Responsibility: Handles all business logic, user authentication, and database interactions. It serves JSON data to the frontend.

Tier 3: Database (Data Layer)

Technology: Amazon RDS (PostgreSQL)

Responsibility: Provides persistent, managed storage for all application data.

Component: Task Runner (Data Ingestion)

Technology: AWS Lambda (Python)

Responsibility: Serverless functions to run our data ingestion scripts.

Component: Scheduler

Technology: Amazon EventBridge

Responsibility: The "cron" scheduler that triggers our Lambda functions.

2. Component Deep Dive

2.1. Frontend (React)

(No changes from previous design. It just calls the API.)

2.2. Backend (FastAPI on Render)

Framework: FastAPI. All endpoints will be async def.

Data Validation: Request and Response bodies will be strictly defined using Pydantic models. This makes the API self-documenting and robust.

Database Driver: Will use asyncpg to connect to the Amazon RDS instance, allowing for non-blocking, asynchronous database queries that work with FastAPI's event loop.

Business Logic: Enforces all application rules (e.g., "Has this game already started?").

2.3. Task Runner (AWS Lambda + EventBridge)

This is the system's engine.

fetch-odds-lambda:

Trigger: Amazon EventBridge rule (0 5 * * *).

Runtime: Python 3.10+.

Action:

Makes 1 API call to The Odds API for all upcoming NBA games.

Connects to the Amazon RDS database (using asyncpg).

UPSERTs game data into the Games table.

INSERTs new odds into the Odds table.

Key Permissions (IAM Role): Needs Secrets Manager access (to get DB credentials) and VPC access (to connect to RDS).

Quota: 1 request/day.

process-results-lambda:

Trigger: Amazon EventBridge rule (0 9 * * *).

Runtime: Python 3.10+.

Action:

Makes 1 API call to The Odds API scores endpoint.

Updates Games table in RDS with final scores.

Calls the grade_all_pending_picks() logic (which is part of this same Lambda function).

Key Permissions (IAM Role): Same as the other Lambda.

Quota: 1 request/day.

3. Key Processes & Logic

3.1. Pick Grading Logic (grade_all_pending_picks)

This logic is now part of the process-results-lambda.

Find all picks in RDS where result_units IS NULL and the associated game status='Finished'.

Loop through each pick (in an async fashion):

(Grading logic for ML, Spread, Total remains identical to the previous design).

UPDATE Picks SET result_units = ...

After all picks are graded, call update_leaderboard_stats().

3.2. Leaderboard Calculation (update_leaderboard_stats)

This logic is also part of the process-results-lambda. The SQL remains identical to the previous design, just executed via asyncpg.

4. API Endpoint Definitions (FastAPI)

Base URL: /api

Note: All request/response bodies will be defined as Pydantic models in the FastAPI code, which provides automatic data validation. The JSON structure remains the same as the "contract" with the frontend.

Auth Endpoints

POST /auth/register

Body (Pydantic Model): { "username", "email", "password" }

Response (201): { "token": "jwt_token_string" }

POST /auth/login

Body (Pydantic Model): { "email", "password" }

Response (200): { "token": "jwt_token_string" }

Game Endpoints (Read-Only)

GET /api/games/upcoming (Requires Auth)

Response (200): (JSON structure is identical to the previous design)

Pick Endpoints (Authenticated)

POST /api/picks (Requires Auth)

Body (Pydantic Model): (JSON structure is identical to the previous design)

Response (201): { "status": "success", "picks_created": 1 }

GET /api/picks/me (Requires Auth)

Response (200): (A list of the user's picks)

Leaderboard Endpoint (Public)

GET /api/leaderboard

Response (200): (JSON structure is identical to the previous design)

5. Database Schema

(No changes. The schema defined in database_design.md is hosted on Amazon RDS.)