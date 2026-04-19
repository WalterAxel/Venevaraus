-- Run once on existing databases: sqlite3 database.db < migrate_add_category.sql
ALTER TABLE reservations ADD COLUMN category TEXT NOT NULL DEFAULT 'varaus';
