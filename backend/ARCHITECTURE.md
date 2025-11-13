PickVs (MVP) - System Architecture

Status: Draft 2.0 (AWS Hybrid)
Related Document: product_requirements.md

1. Overview

This document outlines the system architecture for the AlgoRank MVP. The design is a Hybrid Cloud Architecture that combines Platform-as-a-Service (PaaS) for the API with serverless AWS services for the database and data ingestion.

This decoupled design is critical to meeting the non-functional requirement (N-4.1) of staying within The Odds API's 500 requests/month free tier. The user-facing web application will not call The Odds API directly.

2. Core Components & Technology

Layer

Component

Technology

Purpose

Frontend

Client-Side Web App

React (or Next.js)

Provides the User Interface (UI). Deployed on Vercel/Netlify.

Backend

Server-Side API

Python (FastAPI)

The "brain" that handles auth and business logic. Deployed on Render.

Database

Data Layer

Amazon RDS (PostgreSQL)

The persistent data store. This is a managed, scalable AWS service.

Task Runner

Data Ingestion Engine

AWS Lambda

Serverless functions that run our Python scripts (fetch_odds, process_results).

Scheduler

Cron Service

Amazon EventBridge

The "cron" scheduler that triggers our Lambda functions on a daily schedule.

3. Architecture Diagram

The system operates on two distinct data flows:

User Interaction Flow (Blue Arrow): A user interacts with the React App (Vercel), which only communicates with our FastAPI Backend (Render). The API reads/writes to our Amazon RDS Database.

Data Ingestion Flow (Green Arrow): Amazon EventBridge (the scheduler) triggers two AWS Lambda Functions. These functions call the external Odds API, then write the fetched data directly into our Amazon RDS Database.

4. Data Flows

4.1. Data Ingestion Flow (Scheduled Task via AWS)

This flow is the most critical part of the architecture, designed to use only 2 API requests per day.

Process (Triggered by EventBridge):

Task 1: Fetch Odds (Runs 1x daily, e.g., 5:00 AM)

An Amazon EventBridge rule triggers the fetch-odds-lambda Lambda function.

The Lambda function makes 1 API call to The Odds API for basketball_nba.

It parses the JSON and writes the data to the Amazon RDS database (Games and Odds tables).

Quota Used: 1 Request

Task 2: Fetch Results (Runs 1x daily, e.g., 9:00 AM next day)

An Amazon EventBridge rule triggers the process-results-lambda Lambda function.

The Lambda function makes 1 API call to The Odds API scores endpoint.

It updates the Games table in RDS with final scores.

Quota Used: 1 Request

Task 3: Grade Picks (Runs immediately after Task 2)

This logic is part of the process-results-lambda.

This makes 0 external API calls.

It queries the RDS database for all Picks where the game_id is now Finished.

It calculates result_units and updates the Picks table.

It then aggregates these new results into the Users table, updating total_units, total_wagered, and roi.

Total API Usage: ~60 requests/month, safely within the 500-request free limit.

4.2. User Interaction Flow (Web API on Render)

This flow never calls The Odds API. It only interacts with our Amazon RDS database via our FastAPI backend.

User Registers/Logs In (POST /auth/register)

Frontend sends email, password.

Backend (FastAPI) validates the request, hashes the password, creates a new Users record in RDS, and returns a JWT.

User Views Games to Pick (GET /api/games/upcoming)

Frontend (with JWT) requests games.

Backend (FastAPI) queries the RDS database for scheduled games and their odds.

Backend returns a JSON list of games.

User Submits Picks (POST /api/picks)

Frontend sends JWT and a list of picks.

Backend (FastAPI) validates that the game in RDS is still 'Scheduled'.

Backend saves the new records to the Picks table in RDS.

User Views Leaderboard (GET /api/leaderboard)

Frontend requests leaderboard data.

Backend (FastAPI) queries the RDS database (SELECT username, total_units...).

Backend returns a simple JSON array of the ranked users.

5. Core Database Schema

(No changes. The schema defined in database_design.md is sound.)