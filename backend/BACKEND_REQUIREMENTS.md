# PickVs (MVP) - Product Requirements Document

Status: Draft
Owner: Product
Last Updated: November 10, 2025

## 1. Overview & Vision

### 1.1. Product Vision

To become the premier, transparent, and data-driven platform for verifiably ranking the performance of sports betting models and "sharps" (skilled bettors).

### 1.2. Problem Statement

The sports betting analysis industry is filled with "experts" and models making performance claims that are impossible to verify. There is no public, objective system that ingests a standard set of data (odds and results) and holds models accountable for their past performance. This makes it difficult for data-savvy bettors to find truly valuable, high-performing predictive models.

### 1.3. Target Audience

Data Scientists / Hobbyists: Individuals who build their own ML models for sports betting and want to test them, track their performance, and (eventually) compete against others.

Data-Driven Bettors: Bettors who are skeptical of "expert" picks and are looking for a provably profitable model or user to follow.

## 2. MVP Goals & Scope

### 2.1. Primary Goals

The goal of this MVP is to validate the core user loop:

Will users sign up for a platform to submit their predictions?

Can the system successfully ingest, process, and grade these predictions against a reliable, third-party data source?

Will a public leaderboard showing performance metrics (ROI, Net Units) drive user engagement?

### 2.2. In-Scope Features

User registration, login, and authentication (email/password).

A basic user profile page showing their key performance stats.

A page to view upcoming NBA games (sourced from the API).

A mechanism for users to submit their "picks" (predictions) for NBA games before they start.

Automated, backend ingestion of NBA game schedules, odds, and final results.

A public leaderboard ranking all users based on performance.

Only NBA games will be supported.

Only Moneyline, Point Spread, and Totals (Over/Under) markets will be supported.

### 2.3. Out-of-Scope (Future Releases)

All other sports (NFL, MLB, Soccer, etc.).

Any paid API usage. The system must operate entirely within The Odds API free tier.

Player prop bets or any other complex markets.

Uploading model files. Users submit picks (the model's output), not their proprietary model code.

Real-time odds or live betting. All odds are fetched pre-game, and all results are processed post-game.

Social features (following, commenting, sharing).

Monetization (subscriptions, ad revenue, etc.).

## 3. Functional Requirements (User Stories)

### Epic 1: User Account Management

U-1.1: As a new user, I want to create a secure account with my email and a password so I can participate in the leaderboard.

U-1.2: As a returning user, I want to log in to my account so I can submit my daily picks.

U-1.3: As a logged-in user, I want to view my own basic profile page that shows my Net Units, ROI, Accuracy, and Total Bets (Volume).

### Epic 2: Pick Submission

U-2.1: As a logged-in user, I want to see a list of all upcoming NBA games for the current day.

U-2.2: For each game, I want to see the official odds (Moneyline, Spread, Total) that the system has ingested.

U-2.3: As a user, I want to be able to select a pick for any of these markets (e.g., "Lakers -6.5") and submit it.

U-2.4: All picks must be submitted before the game's scheduled start time. The system must "lock" picks at game time.

U-2.5: All submitted picks will be considered a "1 Unit" stake to standardize all calculations.

### Epic 3: Data Ingestion (System Requirement)

S-3.1: The system must automatically fetch all upcoming NBA games and their odds (ML, Spread, Total) from The Odds API once per day to stay within the free-tier limit.

S-3.2: The system must store these games and their associated odds in the database.

S-3.3: The system must automatically fetch the final scores for all completed games from The Odds API once per day.

Epic 4: Performance Calculation (System Requirement)

S-4.1: When a game's final score is ingested, the system must automatically "grade" all user picks for that game (e.g., Win, Loss, or Push).

S-4.2: The system must calculate the profit/loss for each graded pick based on the 1 Unit stake and the odds stored in the database.

Example 1 (Win): Pick on odds of -110 (1.91 decimal) = +0.91 Units.

Example 2 (Win): Pick on odds of +150 (2.50 decimal) = +1.50 Units.

Example 3 (Loss): Pick on any odds = -1.00 Units.

S-4.3: The system must automatically update the Users table with their new aggregate stats (total_units, total_wagered, roi).

### Epic 5: Public Leaderboard

U-5.1: As any user (logged-in or a visitor), I want to view a public leaderboard page.

U-5.2: The leaderboard must rank all users.

U-5.3: The leaderboard must be sortable by the primary metrics: Net Units, ROI, and Total Bets (Volume).

## 4. Non-Functional Requirements

| Category | Requirement |
| Performance | The public leaderboard page must load in under 3 seconds. |
| Security | All user passwords must be hashed (e.g., using bcrypt). All communication must use HTTPS. |
| Reliability | The automated data ingestion scripts must have a 99%+ daily success rate. |
| Constraint | (CRITICAL) All external API calls to The Odds API must not exceed 500 requests per month. This constraint dictates the entire data ingestion architecture (i.e., one fetch for odds, one for results per day). |

## 5. Success Metrics (KPIs)

How we will measure the success of the MVP:

Activation Rate: % of new users who sign up and submit at least one pick within their first week.

Weekly Active Users: % of users who submit at least one pick per week.

Retention: % of users who are still active after one month.

System Health: 100% adherence to the API free tier limit (zero overage charges).