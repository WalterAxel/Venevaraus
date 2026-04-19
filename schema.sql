CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    start_date DATETIME,
    end_date DATETIME,
    category TEXT NOT NULL DEFAULT 'varaus' CHECK (category IN ('varaus', 'vikailmoitus')),
    user_id INTEGER REFERENCES users
);
