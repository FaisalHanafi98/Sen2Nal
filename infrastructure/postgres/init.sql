-- PostgreSQL initialization script for Sen2Nal
-- This script runs automatically when the database is first created

-- Create database if not exists (Docker will create it via env vars)
-- CREATE DATABASE sen2nal;

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
