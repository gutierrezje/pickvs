AlgoRank MVP - Project Plan & To-Do List

This document breaks down the entire MVP development into logical sprints and actionable tasks. It has been updated to use FastAPI and key AWS services.

Sprint 0: Project Setup & Foundation (The "Sandbox")

Goal: Get your tools and cloud infrastructure ready.

$$$$

 Task: Set up Local Environment

(Deliverables are the same: Postgres GUI, Python, Node)

Learning: How to install and manage a local database for development (you will use RDS for production).

$$$$

 Task: Provision Cloud Database (AWS RDS)

Deliverable:

$$$$

 An Amazon RDS (PostgreSQL) instance is created (use the free tier).

$$$$

 The instance is configured to be accessible from your local IP (for testing) and from your Render/Lambda IPs (for production).

$$$$

 The SQL script from database_design.md is executed on the RDS instance.

Testing:

$$$$

 Can you connect to your remote RDS database from your local GUI (DBeaver/pgAdmin)?

Learning:

AWS Console: Navigating RDS.

AWS Security Groups: How to configure IP-based access rules.

AWS IAM: Creating a user with the correct permissions.

How to use remote database connection strings.

$$$$

 Task: Initialize Project Repositories

Deliverable:

$$$$

 (Same as before: Git repo, backend folder, frontend folder).

$$$$

 backend/requirements.txt is updated with fastapi, uvicorn, asyncpg, and boto3.

Testing:

$$$$

 pip install -r requirements.txt completes successfully.

Learning:

Monorepo structure.

Python virtual environments.

Sprint 1: Backend - Data Ingestion Engine (AWS Lambda)

Goal: Build the serverless data pipeline. This sprint has 0 API endpoints.

$$$$

 Task: Build fetch-odds-lambda

Deliverable:

$$$$

 An AWS Lambda function (written in Python) that:

Loads env vars/secrets (API_KEY, DB_URL).

Connects to your Amazon RDS DB (using asyncpg).

Makes 1 call to The Odds API for basketball_nba.

Parses the JSON and UPSERTs games/odds into the RDS tables.

Testing:

$$$$

 Test 1 (Local): Run the function locally, pointing to your local Postgres DB.

$$$$

 Test 2 (Cloud): Deploy the Lambda and use the "Test" button in the AWS console.

$$$$

 Check your RDS database: Are the Games and Odds tables populated?

Learning:

How to write, package, and deploy an AWS Lambda function.

Storing secrets for Lambda (AWS Secrets Manager).

Connecting a Lambda to an RDS instance (requires VPC configuration).

Reading CloudWatch Logs for debugging.

$$$$

 Task: Build process-results-lambda

Deliverable:

$$$$

 An AWS Lambda function that:

Makes 1 call to The Odds API scores endpoint.

Updates Games table in RDS with final scores.

Includes the Pick Grading Logic (from system_design.md).

Includes the Leaderboard Update Logic (from system_design.md).

Testing:

$$$$

 CRITICAL TEST: Manually add fake picks in your RDS database.

$$$$

 Run the Lambda test event.

$$$$

 Check your RDS database: Are the Picks graded? Are the Users stats updated?

Learning:

Combining multiple logical steps into one serverless function.

Writing complex, transactional database logic in a Lambda.

$$$$

 Task: Configure EventBridge (Scheduler)

Deliverable:

$$$$

 An Amazon EventBridge rule that triggers fetch-odds-lambda on schedule (e.g., 0 5 * * *).

$$$$

 An Amazon EventBridge rule that triggers process-results-lambda on schedule (e.g., 0 9 * * *).

Testing:

$$$$

 Manually set the trigger to run "in 5 minutes" and check CloudWatch Logs to confirm it executed.

Learning:

AWS EventBridge as a serverless cron scheduler.

Sprint 2: Backend - API Server (FastAPI)

Goal: Build the "contract" for the frontend using FastAPI.

$$$$

 Task: Build Auth Endpoints (FastAPI)

Deliverable:

$$$$

 POST /auth/register (using async def and Pydantic models).

$$$$

 POST /auth/login (using async def and Pydantic models).

Testing:

$$$$

 Run the FastAPI server locally (uvicorn main:app --reload).

$$$$

 Test endpoints with Postman or the built-in (/docs) Swagger UI.

Learning:

FastAPI: Routing, Pydantic models, async/await.

bcrypt and PyJWT in an async context.

$$$$

 Task: Build Leaderboard & Game Endpoints (FastAPI)

Deliverable:

$$$$

 GET /api/leaderboard (publicly accessible).

$$$$

 GET /api/games/upcoming (requires JWT auth).

Testing:

$$$$

 Test with Postman, both with and without the JWT auth token.

Learning:

FastAPI dependency injection for handling authentication.

Writing complex, read-only SQL queries with asyncpg.

$$$$

 Task: Build Pick Endpoints (FastAPI)

Deliverable:

$$$$

 POST /api/picks (requires auth, validates with Pydantic).

$$$$

 GET /api/picks/me (requires auth).

Testing:

$$$$

 Postman: Can you submit a pick?

$$$$

 Postman: Does it fail if the game_id is bad (Pydantic validation)?

$$$$

 Postman: Does it fail if the game has already started (business logic)?

Learning:

Handling POST request bodies with Pydantic.

Combining Pydantic validation with database-driven business logic.

Sprint 3 & 4: Frontend (React)

(No change) These sprints are identical to the previous plan. The frontend doesn't care if the backend is Flask or FastAPI, as long as the API "contract" (the JSON payloads and endpoint paths) remains the same, which it does.

Sprint 5: Deployment & Go-Live

$$$$

 Task: Deploy Database

(This task is now in Sprint 0).

$$$$

 Task: Deploy Backend API (Render)

Deliverable:

$$$$

 FastAPI app deployed to a Render Web Service.

$$$$

 Production environment variables are set (e.g., DATABASE_URL for Amazon RDS, JWT_SECRET_KEY, API_KEY).

Testing:

$$$$

 Can you hit your live Render URL (...onrender.com/api/leaderboard) with Postman?

$$$$

 Fixing CORS: You will need to configure FastAPI's CORSMiddleware to allow requests from your Vercel domain.

Learning:

Deploying a FastAPI application (vs. Flask).

Configuring CORS in FastAPI.

Managing production secrets for a PaaS service.

$$$$

 Task: Deploy Frontend (Vercel/Netlify)

(No change) This task is identical to the previous plan.

$$$$

 Task: Configure Production Cron Job

(This task is now in Sprint 1).

Deliverable:

$$$$

 The EventBridge rules are enabled and pointed at the production Lambda functions.

Testing:

$$$$

 Wait 24 hours. Check CloudWatch Logs to confirm execution. Check the live RDS database to confirm new games/results are present.

Learning:

Finalizing and monitoring a serverless production system.