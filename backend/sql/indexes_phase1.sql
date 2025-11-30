-- Phase 1 Database Indexes (CRITICAL - Apply Before Launch)
--
-- These are the essential indexes for core application functionality.
-- Apply these BEFORE building the API and frontend.
--
-- Expected performance improvement: 10-50x for indexed queries
-- Cost: Minimal write overhead (indexes are small relative to data)
--
-- Run this file with:
--   psql $DATABASE_URL -f backend/sql/indexes_phase1.sql

-- ============================================================================
-- Games Table Indexes
-- ============================================================================

-- Index for fetching scheduled/upcoming games ordered by time
-- Used by: GET /api/games (main endpoint for user to see available games)
-- Query pattern: WHERE status = 'Scheduled' ORDER BY game_timestamp
CREATE INDEX IF NOT EXISTS idx_games_status_timestamp
ON Games(status, game_timestamp)
WHERE status IN ('Scheduled', 'InProgress');

-- Explanation:
-- - Composite index on (status, game_timestamp) allows filtering + sorting in one pass
-- - Partial index (WHERE clause) excludes completed games, making index smaller
-- - This is THE most important index for the app (used on every page load)


-- ============================================================================
-- Odds Table Indexes
-- ============================================================================

-- Index for looking up odds for a specific game
-- Used by: GET /api/games/:id (game detail page showing all odds)
-- Query pattern: WHERE game_id = ? ORDER BY market_type
CREATE INDEX IF NOT EXISTS idx_odds_game_market
ON Odds(game_id, market_type);

-- Explanation:
-- - Composite index allows lookup by game_id + sorting by market_type
-- - Unique constraint on (game_id, market_type) already exists, but we add market_type
--   to the index to avoid a separate sort operation


-- ============================================================================
-- Picks Table Indexes
-- ============================================================================

-- Index for fetching a user's pick history
-- Used by: GET /api/picks/user/:id (user's picks page)
-- Query pattern: WHERE user_id = ? ORDER BY created_at DESC
CREATE INDEX IF NOT EXISTS idx_picks_user_created
ON Picks(user_id, created_at DESC);

-- Explanation:
-- - Composite index with DESC on created_at matches ORDER BY direction
-- - Allows efficient "my recent picks" queries without table scan
-- - Critical for user experience (every user wants to see their history)


-- ============================================================================
-- Users Table Indexes
-- ============================================================================

-- Index for username lookups during authentication
-- Used by: POST /api/auth/login (login endpoint)
-- Query pattern: WHERE username = ?
CREATE INDEX IF NOT EXISTS idx_users_username
ON Users(username);

-- Explanation:
-- - Simple index for login lookups
-- - Username is already UNIQUE, but explicit index ensures fast lookups
-- - Critical for authentication performance


-- ============================================================================
-- Verification
-- ============================================================================

-- After running this file, verify indexes were created:
--
--   SELECT
--     schemaname,
--     tablename,
--     indexname,
--     indexdef
--   FROM pg_indexes
--   WHERE schemaname = 'public'
--   ORDER BY tablename, indexname;
--
-- You should see:
--   - idx_games_status_timestamp
--   - idx_odds_game_market
--   - idx_picks_user_created
--   - idx_users_username
--
-- Test that indexes are being used:
--
--   EXPLAIN ANALYZE
--   SELECT * FROM Games
--   WHERE status = 'Scheduled'
--   ORDER BY game_timestamp
--   LIMIT 20;
--
-- Look for "Index Scan using idx_games_status_timestamp" in the output.
-- The query cost should be very low (< 10.00 for small datasets).
