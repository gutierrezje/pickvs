-- Drop and Recreate Database (Safe since no user data exists yet)
-- This script drops all tables and recreates them with the updated schema

-- Drop tables in reverse dependency order (child tables first)
DROP TABLE IF EXISTS Picks CASCADE;
DROP TABLE IF EXISTS Odds CASCADE;
DROP TABLE IF EXISTS Games CASCADE;
DROP TABLE IF EXISTS Users CASCADE;

-- Recreate from schema.sql
-- Run this immediately after: psql $DATABASE_URL -f backend/sql/schema.sql
