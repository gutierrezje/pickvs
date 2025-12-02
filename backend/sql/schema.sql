-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
-- NOTE: total_picks is denormalized for performance (leaderboard queries).
-- TRADEOFF: Could be calculated as COUNT(*) from Picks table to save storage
-- and ensure accuracy, but denormalization avoids JOIN overhead on leaderboard.
-- TODO: Benchmark query performance to determine if denormalization is necessary.
CREATE TABLE IF NOT EXISTS Users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    total_units DECIMAL(10, 2) DEFAULT 0.00,    -- Net units won/lost
    total_picks DECIMAL(10, 2) DEFAULT 0.00,    -- Number of picks (denormalized from Picks table)
    roi DECIMAL(5, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS Games (
    game_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    api_game_id VARCHAR(100) UNIQUE NOT NULL,
    home_team VARCHAR(100) NOT NULL,
    away_team VARCHAR(100) NOT NULL,
    game_timestamp TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Scheduled',
    home_score INT,
    away_score INT,
    fetched_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS Odds (
    odd_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    game_id UUID NOT NULL REFERENCES Games(game_id) ON DELETE CASCADE,
    market_type VARCHAR(20) NOT NULL,       -- 'moneyline', 'spread', 'total', etc.
    home_odds DECIMAL(7, 2) NOT NULL,
    away_odds DECIMAL(7, 2) NOT NULL,
    line_value DECIMAL(4, 1),             -- spread amount (e.g., -6.5) or total (e.g., 220.5)
    UNIQUE(game_id, market_type)
);

CREATE TABLE IF NOT EXISTS Picks (
    pick_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES Users(user_id) ON DELETE CASCADE,
    game_id UUID NOT NULL REFERENCES Games(game_id) ON DELETE CASCADE,
    market_picked VARCHAR(20) NOT NULL,           -- 'moneyline', 'spread', 'total', etc.
    outcome_picked VARCHAR(100) NOT NULL,
    stake_units DECIMAL(3, 1) NOT NULL DEFAULT 1.0,
    odds_at_pick DECIMAL(7, 2) NOT NULL,
    result_units DECIMAL(5, 2),                 -- 'win', 'lose', 'push'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, game_id, market_picked)       -- Ensure one pick per market per user
);

-- ============================================================================
-- INDEXES (Phase 1 - Critical for performance)
-- ============================================================================

-- Index for fetching scheduled/upcoming games ordered by time
-- Used by: GET /api/games
CREATE INDEX IF NOT EXISTS idx_games_status_timestamp
ON Games(status, game_timestamp)
WHERE status IN ('Scheduled', 'InProgress');

-- Index for looking up odds for a specific game
-- Used by: GET /api/games/:id
CREATE INDEX IF NOT EXISTS idx_odds_game_market
ON Odds(game_id, market_type);

-- Index for fetching a user's pick history
-- Used by: GET /api/picks/me
CREATE INDEX IF NOT EXISTS idx_picks_user_created
ON Picks(user_id, created_at DESC);

-- Index for username lookups during authentication
-- Used by: POST /api/auth/login
CREATE INDEX IF NOT EXISTS idx_users_username
ON Users(username);
