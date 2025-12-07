# PickVs (MVP) - Database Design & Schema

## 1. Overview

This document provides the concrete SQL Data Definition Language (DDL) required to create the PostgreSQL database as specified in the system design.

## 2. Entity-Relationship Diagram (ERD)

The diagram below visualizes the relationships between the four core tables.

Users has a one-to-many relationship with Picks.

Games has a one-to-many relationship with Odds.

Games has a one-to-many relationship with Picks.

This creates a "fan trap" where Users and Games are linked through the Picks table, which is the core of the application.

## 3. SQL Schema (PostgreSQL DDL)

**Prerequisites**: You will need to enable the uuid-ossp extension to use `uuid_generate_v4()`.

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

---

### 3.1 Users Table
**Purpose**: Store user account info and their aggregate performance stats

```sql
CREATE TABLE Users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    total_units DECIMAL(10, 2) DEFAULT 0.00,       -- Net profit/loss
    total_picks INT DEFAULT 0,                     -- Number of picks
    roi DECIMAL(5, 2) DEFAULT 0.00,                -- Return on investment %
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

| Column | Type | Notes |
|--------|------|-------|
| user_id | UUID | Auto-generated primary key |
| username | VARCHAR | Unique display name |
| email | VARCHAR | Unique email address |
| password_hash | VARCHAR | Hashed password (bcrypt) |
| total_units | DECIMAL | Updated by process-results-lambda |
| total_picks | INT | Updated by process-results-lambda |
| roi | DECIMAL | Updated by process-results-lambda |
| created_at | TIMESTAMPTZ | Auto-set on insert |

---

### 3.2 Games Table
**Purpose**: Store a record for every game fetched from The Odds API

```sql
CREATE TABLE Games (
    game_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_game_id VARCHAR(100) NOT NULL UNIQUE,      -- Unique ID from Odds API
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    game_timestamp TIMESTAMPTZ NOT NULL,           -- Scheduled start time
    status VARCHAR(20) NOT NULL DEFAULT 'Scheduled',  -- 'Scheduled' or 'Finished'
    home_score INTEGER,                            -- NULL until game finishes
    away_score INTEGER,                            -- NULL until game finishes
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);
```

| Column | Type | Notes |
|--------|------|-------|
| game_id | UUID | Auto-generated primary key |
| api_game_id | VARCHAR | External ID from The Odds API |
| home_team | VARCHAR | Team name (e.g., 'Los Angeles Lakers') |
| away_team | VARCHAR | Team name (e.g., 'Golden State Warriors') |
| game_timestamp | TIMESTAMPTZ | When the game starts |
| status | VARCHAR | 'Scheduled' (pre-game) or 'Finished' (post-game) |
| home_score | INTEGER | Final score for home team (or NULL) |
| away_score | INTEGER | Final score for away team (or NULL) |
| fetched_at | TIMESTAMPTZ | When this record was last updated |

---

### 3.3 Odds Table
**Purpose**: Store odds for each game, separate from game itself (to allow odds updates)

```sql
CREATE TABLE Odds (
    odd_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES Games(game_id) ON DELETE CASCADE,
    market_type VARCHAR(20) NOT NULL,              -- 'moneyline', 'spread', 'total'
    home_odds DECIMAL(7, 2) NOT NULL,             -- Decimal odds (e.g., 1.91, 2.50)
    away_odds DECIMAL(7, 2) NOT NULL,
    line_value DECIMAL(4, 1),                    -- Spread amount (e.g., -6.5) or Total (e.g., 220.5)
    UNIQUE(game_id, market_type)                   -- Only one of each market type per game
);
```

| Column | Type | Notes |
|--------|------|-------|
| odd_id | UUID | Auto-generated primary key |
| game_id | UUID | Foreign key to Games table |
| market_type | VARCHAR | 'moneyline' \| 'spread' \| 'total' |
| home_odds | DECIMAL | Decimal format (e.g., 1.91 = -110 in American) |
| away_odds | DECIMAL | For spreads/totals: odds for "over" or "away" team |
| line_value | DECIMAL | -6.5 for spread, 220.5 for totals (NULL for ML) |

---

### 3.4 Picks Table
**Purpose**: Store every pick made by every user

```sql
CREATE TABLE Picks (
    pick_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    game_id UUID NOT NULL REFERENCES Games(game_id) ON DELETE CASCADE,
    market_picked VARCHAR(20) NOT NULL,            -- 'moneyline', 'spread', 'total'
    outcome_picked VARCHAR(100) NOT NULL,          -- e.g., 'Los Angeles Lakers' or 'Over'
    stake_units DECIMAL(3, 1) NOT NULL DEFAULT 1.0,  -- Always 1 unit per pick
    odds_at_pick DECIMAL(7, 2) NOT NULL,          -- Decimal odds at time of pick
    result_units DECIMAL(5, 2),                    -- NULL until graded, then -1/0/+1.xx
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, game_id, market_picked)       -- User can't pick same market twice
);
```

| Column | Type | Notes |
|--------|------|-------|
| pick_id | UUID | Auto-generated primary key |
| user_id | UUID | Foreign key to Users table |
| game_id | UUID | Foreign key to Games table |
| market_picked | VARCHAR | 'moneyline' \| 'spread' \| 'total' |
| outcome_picked | VARCHAR | Selected outcome (e.g., 'Lakers', 'Warriors', 'Over', 'Under') |
| stake_units | DECIMAL | Always 1.0 (standardized) |
| odds_at_pick | DECIMAL | The odds when user submitted the pick |
| result_units | DECIMAL | Win: +0.91 (ML) or +1.50 (Odds), Loss: -1.0, NULL (pending) |
| created_at | TIMESTAMPTZ | When the pick was submitted |


## Related Documentation
  - [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md)
