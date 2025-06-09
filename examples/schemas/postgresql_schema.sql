-- Sample PostgreSQL schema for SQLAlchemy-ViewORM examples
-- These statements show the underlying SQL that would be used

-- Create a table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    score NUMERIC(10, 2) DEFAULT 0
);

-- Create a simple view
CREATE VIEW active_users_view AS
SELECT
    id,
    name,
    email
FROM
    users
WHERE
    active = TRUE;

-- Create a materialized view
CREATE MATERIALIZED VIEW user_scores_view AS
SELECT
    id,
    name,
    score
FROM
    users
WHERE
    score > 0;

-- Create a view with options
CREATE VIEW user_email_view
WITH (security_barrier = true)
AS
SELECT
    id,
    email
FROM
    users;

-- Refresh a materialized view
REFRESH MATERIALIZED VIEW user_scores_view;

-- Refresh a materialized view concurrently
-- Requires an index that can satisfy a unique constraint
CREATE UNIQUE INDEX user_scores_view_id_idx ON user_scores_view (id);
REFRESH MATERIALIZED VIEW CONCURRENTLY user_scores_view;

-- Drop views
DROP VIEW IF EXISTS active_users_view;
DROP MATERIALIZED VIEW IF EXISTS user_scores_view;
