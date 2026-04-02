CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY,
    title TEXT
    description TEXT
    start_date DATETIME
    end_date DATETIME
    user_id INTEGER REFERENCES users
);
