-- Migrates reservation category values from Finnish to English and applies
-- the CHECK constraint used in schema.sql. Run:
--   sqlite3 database.db < migrate_categories_to_english.sql
-- Backup the database file first.

PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

CREATE TABLE reservations_new (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    start_date DATETIME,
    end_date DATETIME,
    category TEXT NOT NULL DEFAULT 'booking' CHECK (category IN ('booking', 'fault_report')),
    user_id INTEGER REFERENCES users
);

INSERT INTO reservations_new (id, title, description, start_date, end_date, category, user_id)
SELECT
    id,
    title,
    description,
    start_date,
    end_date,
    CASE category
        WHEN 'varaus' THEN 'booking'
        WHEN 'vikailmoitus' THEN 'fault_report'
        WHEN 'booking' THEN 'booking'
        WHEN 'fault_report' THEN 'fault_report'
        ELSE 'booking'
    END,
    user_id
FROM reservations;

DROP TABLE reservations;
ALTER TABLE reservations_new RENAME TO reservations;

COMMIT;
PRAGMA foreign_keys = ON;
