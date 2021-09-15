-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS text;
DROP TABLE IF EXISTS sentence;
DROP TABLE IF EXISTS user;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE text (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  body TEXT UNIQUE NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (user_id) REFERENCES user (id),
  unique (name)
);

CREATE TABLE sentence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT UNIQUE NOT NULL,
  tree TEXT UNIQUE NOT NULL,
  text_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  FOREIGN KEY (text_id) REFERENCES text (id),
  FOREIGN KEY (user_id) REFERENCES user (id),
  unique (name)
);