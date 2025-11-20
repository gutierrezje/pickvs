# PickVs MVP - Project Plan & To-Do List

This document breaks down the entire MVP development into logical sprints and actionable tasks. It has been updated to use FastAPI and key AWS services.

## Data Sourcing Strategy

**Important Context**: The Odds API free tier does not provide historical odds, only current/future odds. For MVP development, we will use historical NBA data from Kaggle. Here are the three phases:

| Phase | Timing | Data Source | Purpose |
|-------|--------|-------------|---------|
| **Phase 1: MVP Development** | Current | Kaggle historical NBA dataset | Test pick submission, grading logic, and leaderboard calculations with known game results |
| **Phase 2: Pre-Launch Validation** | Optional (1 month before launch) | Paid Odds API tier | Validate system behavior with real-time odds and live game results |
| **Phase 3: Production** | After launch | The Odds API free tier (2 calls/day) | Ongoing operations with cost constraint of ~60 API calls/month |

**Why This Approach**: Phase 1 is to develop and test the entire system offline without API costs or quota concerns. Phase 3 will work because by then, the system only needs to ingest *new* games going forward (not historical data). The 2 calls/day (fetch-odds + process-results) = ~60 calls/month, well within the 500-request free limit.

---

## Sprint 0: Project Setup & Foundation (The "Sandbox")

**Goal**: Get tools and cloud infrastructure ready.

### Task: Set up Local Environment

**Deliverables**:
- Postgres GUI (DBeaver or pgAdmin)
- Python development environment (with virtual env)
- Node.js for frontend development

**Learning**: How to install and manage a local database for development (you will use RDS for production).

---

### Task: Provision Cloud Database (Neon PostgreSQL)

**Deliverables**:
- Create a Neon account and project at [neon.tech](https://neon.tech)
- Generate a project and get both connection strings:
  - **Standard endpoint**: For long-lived connections (Render API)
  - **Pooler endpoint**: For Lambda functions (with `-pooler` suffix)
- Store connection strings securely:
  - `.env` file locally for development
  - Render environment variables for FastAPI deployment
  - AWS Secrets Manager for Lambda functions
- Execute the SQL script from SCHEMA.md on the Neon database

**Testing**:
- Can you connect to Neon from your local GUI (DBeaver/pgAdmin) using the standard endpoint?
- Can you query test data after connection?

**Learning**:
- Neon project creation and management
- Understanding pooler vs standard endpoints
- Connection pooling with PgBouncer (transparent to you)
- Managing secrets for both Render and AWS Lambda

---

### Task: Initialize Project Repositories

**Deliverables**:
- Git repository with `/backend` and `/frontend` folders
- `backend/requirements.txt` updated with fastapi, uvicorn, asyncpg, and boto3
- `frontend/package.json` with React, axios, and other dependencies

**Testing**:
- `pip install -r requirements.txt` completes successfully
- `npm install` in frontend folder completes successfully

**Learning**:
- Monorepo structure
- Python virtual environments
- Node package management

---

### Task: Source and Prepare Kaggle Historical NBA Dataset

**Deliverables**:
- Download a Kaggle historical NBA dataset (e.g., "NBA Games Data" with scores and dates)
- Create a Python script in `backend/scripts/import_kaggle_data.py` that:
  - Parses the CSV/JSON file from Kaggle
  - Maps Kaggle columns to PickVs schema (Games, Odds tables)
  - Inserts sample games with realistic odds (can use pre-game closing lines if available, or estimate from standard sportsbook formats)
  - Inserts a small number of sample Picks for testing user_ids
  - Populates the Users table with sample user data for leaderboard testing

**Testing**:
- Run the import script against your local Postgres database
- Query the Games, Odds, Picks, and Users tables to confirm data integrity
- Verify that the sample data covers at least 20+ games (to test leaderboard 20-pick minimum)

**Learning**:
- Python data transformation and ETL patterns
- Working with Kaggle datasets
- Bulk data insertion into PostgreSQL

**Note**: This script will only be used during MVP development. In Phase 3 (production), live data will come from The Odds API via fetch-odds-lambda.

---

## Sprint 1: Backend - Data Ingestion Engine (AWS Lambda)

**Goal**: Build the serverless data pipeline. This sprint has 0 API endpoints.

### Task: Build fetch-odds-lambda

**Deliverables**:
- An AWS Lambda function (written in Python) that:
  - Loads env vars/secrets (API_KEY, DATABASE_URL_POOLER from AWS Secrets Manager)
  - Connects to Neon database using the pooler endpoint (using asyncpg)
  - Makes 1 call to The Odds API for basketball_nba
  - Parses the JSON and UPSERTs games/odds into the Neon database tables

**MVP Development Note (Phase 1)**: For now, this function can be stubbed or skipped since you're using Kaggle data. The logic is correct; you're just not calling it yet.

**Phase 3 Note (Production Transition)**: When moving to live data, this function will activate and run on schedule (e.g., 5 AM daily) to fetch odds for the day's games.

**Testing**:
- Test 1 (Local): Run the function locally, pointing to your local Postgres DB (or Neon standard endpoint for testing)
- Test 2 (Cloud): Deploy the Lambda and use the "Test" button in the AWS console (can use mock data in Phase 1)
- Check your Neon database: Would the Games and Odds tables be populated if you had real API data?

**Learning**:
- How to write, package, and deploy an AWS Lambda function
- Storing secrets for Lambda (AWS Secrets Manager)
- Connecting a Lambda to Neon using the pooler endpoint (no VPC configuration needed!)
- Understanding connection pooling benefits with Neon
- Reading CloudWatch Logs for debugging
- Building functions that are agnostic to data source (API vs. mock data)

---

### Task: Build process-results-lambda

**Deliverables**:
- An AWS Lambda function that:
  - Makes 1 call to The Odds API scores endpoint
  - Updates Games table in Neon with final scores
  - Includes the Pick Grading Logic (from SYSTEM_DESIGN.md)
  - Includes the Leaderboard Update Logic (from SYSTEM_DESIGN.md)
  - Uses Neon pooler endpoint for database connection

**MVP Development Note (Phase 1)**: The Kaggle dataset already has final scores. You can either stub this function or build it now and test it against your Kaggle data by manually marking games as "Finished" in the Games table.

**Phase 3 Note (Production Transition)**: This function will run post-game (e.g., 9 PM daily) to fetch final scores, grade all picks, and update user stats.

**Testing**:
- CRITICAL TEST (Phase 1): Manually add fake picks in your Neon database (use Kaggle data with known results)
- Run the Lambda test event (or invoke locally)
- Check your Neon database: Are the Picks graded correctly? Are the Users stats updated correctly?

**Learning**:
- Combining multiple logical steps into one serverless function
- Writing complex, transactional database logic in a Lambda
- Testing grading logic offline before going live
- Benefits of connection pooling for concurrent Lambda invocations

---

### Task: Configure EventBridge (Scheduler)

**Deliverables**:
- An Amazon EventBridge rule that triggers fetch-odds-lambda on schedule (e.g., `0 5 * * *`)
- An Amazon EventBridge rule that triggers process-results-lambda on schedule (e.g., `0 9 * * *`)

**MVP Development Note (Phase 1)**: These rules are optional during development. You can skip or disable them since your data comes from Kaggle. Build the infrastructure now so it's ready for Phase 3.

**Phase 3 Note (Production Transition)**: Enable both rules to activate the live data pipeline.

**Testing**:
- (Phase 1): Create the EventBridge rules but leave them disabled. Verify they are syntactically correct
- (Optional): Manually trigger either rule "in 5 minutes" as a dry-run and check CloudWatch Logs to confirm execution

**Learning**:
- AWS EventBridge as a serverless cron scheduler
- Understanding cron expression syntax

---

## Sprint 2: Backend - API Server (FastAPI)

**Goal**: Build the "contract" for the frontend using FastAPI.

### Task: Build Auth Endpoints (FastAPI)

**Deliverables**:
- `POST /auth/register` (using async def and Pydantic models)
- `POST /auth/login` (using async def and Pydantic models)

**Testing**:
- Run the FastAPI server locally (`uvicorn main:app --reload`)
- Test endpoints with Postman or the built-in (/docs) Swagger UI

**Learning**:
- FastAPI: Routing, Pydantic models, async/await
- bcrypt and PyJWT in an async context

---

### Task: Build Leaderboard & Game Endpoints (FastAPI)

**Deliverables**:
- `GET /api/leaderboard` (publicly accessible)
- `GET /api/games/upcoming` (requires JWT auth)

**Testing**:
- Test with Postman, both with and without the JWT auth token

**Learning**:
- FastAPI dependency injection for handling authentication
- Writing complex, read-only SQL queries with asyncpg

---

### Task: Build Pick Endpoints (FastAPI)

**Deliverables**:
- `POST /api/picks` (requires auth, validates with Pydantic)
- `GET /api/picks/me` (requires auth)

**Testing**:
- Postman: Can you submit a pick?
- Postman: Does it fail if the game_id is bad (Pydantic validation)?
- Postman: Does it fail if the game has already started (business logic)?

**Learning**:
- Handling POST request bodies with Pydantic
- Combining Pydantic validation with database-driven business logic

---

## Sprint 3 & 4: Frontend (React)

**No change**: These sprints are identical to the previous plan. The frontend doesn't care if the backend is Flask or FastAPI, as long as the API "contract" (the JSON payloads and endpoint paths) remains the same, which it does.

---

## Sprint 5: Deployment & Go-Live

### Task: Deploy Backend API (Render)

**Deliverables**:
- FastAPI app deployed to a Render Web Service
- Production environment variables are set (e.g., DATABASE_URL for Amazon RDS, JWT_SECRET_KEY, API_KEY)

**Testing**:
- Can you hit your live Render URL (`...onrender.com/api/leaderboard`) with Postman?
- Fixing CORS: You will need to configure FastAPI's CORSMiddleware to allow requests from your Vercel domain

**Learning**:
- Deploying a FastAPI application (vs. Flask)
- Configuring CORS in FastAPI
- Managing production secrets for a PaaS service

---

### Task: Deploy Frontend (Vercel/Netlify)

**No change**: This task is identical to the previous plan.

---

### Task: Configure Production Cron Job

**Deliverable**:
- The EventBridge rules are enabled and pointed at the production Lambda functions

**Testing**:
- Wait 24 hours. Check CloudWatch Logs to confirm execution
- Check the live RDS database to confirm new games/results are present

**Learning**:
- Finalizing and monitoring a serverless production system
