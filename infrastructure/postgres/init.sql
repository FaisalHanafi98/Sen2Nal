-- PostgreSQL initialization script for Sen2Nal
-- This script runs automatically when the database is first created

-- Create database if not exists (Docker will create it via env vars)
-- CREATE DATABASE sen2nal;

-- Ensure user exists with password (development configuration)
ALTER USER sen2nal_user WITH PASSWORD 'sen2nal_password';

-- Create test database for local test runs
CREATE DATABASE sen2nal_test OWNER sen2nal_user;

-- Enable UUID extension (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom types (if needed in future)
-- CREATE TYPE signal_type AS ENUM ('STRONG_BUY', 'BUY', 'HOLD', 'AVOID');

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'Sen2Nal database initialized successfully';
END
$$;
