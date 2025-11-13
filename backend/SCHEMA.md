PickVs (MVP) - Database Design & Schema

Owner: Engineering
Status: Ready for Implementation
Related Document: system_design.md

1. Overview

This document provides the concrete SQL Data Definition Language (DDL) required to create the PostgreSQL database as specified in the system design.

2. Entity-Relationship Diagram (ERD)

The diagram below visualizes the relationships between the four core tables.

Users has a one-to-many relationship with Picks.

Games has a one-to-many relationship with Odds.

Games has a one-to-many relationship with Picks.

This creates a "fan trap" where Users and Games are linked through the Picks table, which is the core of the application.

3. SQL Schema (PostgreSQL DDL)

This is the runnable SQL code to create your database. You will need to enable the uuid-ossp extension to use uuid_generate_v4().

-- Enable the UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ---
-- Table: Users
-- Stores user account info and their aggregate performance
-- ---
CREATE TABLE Users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    total_units DECIMAL(10, 2) DEFAULT 0.00,
    total_wagered DECIMAL(10, 2) DEFAULT 0.00,
    roi DECIMAL(5, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---
-- Table: Games
-- Stores a record for every game we fetch from the API
-- ---
CREATE TABLE Games (
    game_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_game_id VARCHAR(100) NOT NULL UNIQUE,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    game_timestamp TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Scheduled', -- 'Scheduled' or 'Finished'
    home_score INTEGER,
    away_score INTEGER,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

-- ---
-- Table: Odds
-- Stores the odds for each game, separate from the game itself
-- ---
CREATE TABLE Odds (
    odd_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES Games(game_id) ON DELETE CASCADE,
    market_type VARCHAR(20) NOT NULL, -- 'moneyline', 'spread', 'total'
    home_odds DECIMAL(7, 2) NOT NULL,
    away_odds DECIMAL(7, 2) NOT NULL,
    spread_value DECIMAL(4, 1), -- For spreads (e.g., -6.5) and totals (e.g., 220.5)
    UNIQUE(game_id, market_type) -- Ensures only one of each market type per game
);

-- ---
-- Table: Picks
-- Stores every pick made by every user
-- ---
CREATE TABLE Picks (
    pick_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    game_id UUID NOT NULL REFERENCES Games(game_id) ON DELETE CASCADE,
    market_picked VARCHAR(20) NOT NULL,
    team_picked VARCHAR(100) NOT NULL, -- e.g., 'Los Angeles Lakers' or 'Over'
    stake_units DECIMAL(3, 1) NOT NULL DEFAULT 1.0,
    odds_at_pick DECIMAL(7, 2) NOT NULL, -- The decimal odds at the time of the pick
    result_units DECIMAL(5, 2), -- Nullable. Updated after grading
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, game_id, market_picked) -- Prevents user from picking same market twice
);
