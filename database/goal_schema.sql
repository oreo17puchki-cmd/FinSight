-- ============================================================
-- FinSight Financial Goal Planning Module - Database Schema
-- Database Engine: PostgreSQL
-- File: goal_schema.sql
-- ============================================================

-- Drop goals table if it already exists (useful for clean reinstalls)
DROP TABLE IF EXISTS goals CASCADE;

-- Create main GOALS table
CREATE TABLE goals (
    goal_id SERIAL PRIMARY KEY,
    goal_name VARCHAR(150) NOT NULL,
    description TEXT,
    goal_type VARCHAR(50) NOT NULL CHECK (goal_type IN ('Short Term', 'Medium Term', 'Long Term')),
    target_amount NUMERIC(15, 2) NOT NULL CHECK (target_amount > 0),
    current_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (current_amount >= 0),
    remaining_amount NUMERIC(15, 2) NOT NULL DEFAULT 0.00 CHECK (remaining_amount >= 0),
    target_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL CHECK (category IN ('Education', 'Travel', 'Emergency', 'Personal', 'Shopping', 'Health', 'Family', 'Other')),
    priority VARCHAR(20) NOT NULL CHECK (priority IN ('Low', 'Medium', 'High')),
    status VARCHAR(20) NOT NULL CHECK (status IN ('In Progress', 'Completed', 'Overdue')),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexing for high-performance search, sorting, and filter queries
-- Why Indexes Are Used:
-- 1. idx_goals_name: Accelerates real-time ILIKE pattern searches on goal names.
-- 2. idx_goals_category: Optimizes filtered queries when viewing goals by category (e.g. Education, Travel).
-- 3. idx_goals_type: Speed up filtering by Short, Medium, or Long Term goals.
-- 4. idx_goals_priority: Facilitates quick ordering and filtering by Low, Medium, or High priority.
-- 5. idx_goals_status: Optimizes active vs completed goal dashboard summary counts.
-- 6. idx_goals_target_date: Speeds up sorting by nearest or furthest target dates.

CREATE INDEX idx_goals_name ON goals(goal_name);
CREATE INDEX idx_goals_category ON goals(category);
CREATE INDEX idx_goals_type ON goals(goal_type);
CREATE INDEX idx_goals_priority ON goals(priority);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_target_date ON goals(target_date);

-- Trigger Function to automatically update the updated_at timestamp on record updates
CREATE OR REPLACE FUNCTION update_goals_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to goals table
DROP TRIGGER IF EXISTS trigger_update_goals_timestamp ON goals;
CREATE TRIGGER trigger_update_goals_timestamp
BEFORE UPDATE ON goals
FOR EACH ROW
EXECUTE FUNCTION update_goals_timestamp();
