-- Sample SQLite schema for SQLAlchemy-ViewORM examples
-- These statements show the underlying SQL that would be used
-- Note: SQLite does not support materialized views natively

-- Create a table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    active BOOLEAN DEFAULT 1,
    score REAL DEFAULT 0
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
    active = 1;

-- Create a table to simulate a materialized view
-- Since SQLite doesn't support materialized views, we use a table
CREATE TABLE user_scores_view AS
SELECT
    id,
    name,
    score
FROM
    users
WHERE
    score > 0;

-- "Refresh" a table-simulated materialized view
-- This is a two-step process: delete all rows, then insert from the source query
DELETE FROM user_scores_view;
INSERT INTO user_scores_view (id, name, score)
SELECT
    id,
    name,
    score
FROM
    users
WHERE
    score > 0;

-- Drop objects
DROP VIEW IF EXISTS active_users_view;
DROP TABLE IF EXISTS user_scores_view;
