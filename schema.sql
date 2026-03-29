CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE reservations (
    id INTEGER PRIMARY KEY,
    title TEXT
    description TEXT
    start_date DATE
    end_date DATE
    user_id INTEGER REFERENCES users
);
