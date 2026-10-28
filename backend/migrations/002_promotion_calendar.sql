CREATE TABLE promotion_calendar (
 restaurant_id INTEGER NOT NULL REFERENCES restaurants(id), timestamp TEXT NOT NULL,
 promotion REAL NOT NULL CHECK(promotion BETWEEN 0 AND 1), known_at TEXT NOT NULL,
 PRIMARY KEY(restaurant_id,timestamp), CHECK(known_at<=timestamp)
);
