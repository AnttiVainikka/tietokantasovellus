CREATE TABLE Works (id SERIAL PRIMARY KEY, name TEXT, type TEXT, year INT, language TEXT);
CREATE TABLE Users (id SERIAL PRIMARY KEY, username TEXT, moderator INT, password TEXT);
CREATE TABLE Reviews (work_id INTEGER REFERENCES Works, user_id INTEGER REFERENCES Users, review TEXT, score INT);
