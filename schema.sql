CREATE TABLE Works (id SERIAL PRIMARY KEY, name TEXT, type TEXT, year INT, language TEXT);
CREATE TABLE Users (id SERIAL PRIMARY KEY, username TEXT, moderator INT, password TEXT);
CREATE TABLE Reviews (id SERIAL PRIMARY KEY, work_id INTEGER REFERENCES Works, user_id INTEGER REFERENCES Users, review TEXT, score INT);
CREATE TABLE Comments (id SERIAL PRIMARY KEY, review_id INTEGER REFERENCES Reviews, user_id INTEGER REFERENCES Users, writing TEXT);
CREATE TABLE Replies (id SERIAL PRIMARY KEY, comment_id INTEGER REFERENCES Comments, user_id INTEGER REFERENCES Users, writing TEXT);
CREATE TABLE Likes (review_id INTEGER REFERENCES Reviews, comment_id INTEGER REFERENCES Comments, reply_id INTEGER REFERENCES Replies, user_id INTEGER REFERENCES Users);
CREATE TABLE Dislikes (review_id INTEGER REFERENCES Reviews, comment_id INTEGER REFERENCES Comments, reply_id INTEGER REFERENCES Replies, user_id INTEGER REFERENCES Users);
CREATE TABLE Reports (work_id INTEGER REFERENCES Works, review_id INTEGER REFERENCES Reviews, comment_id INTEGER REFERENCES Comments, reply_id INTEGER REFERENCES Replies, user_id INTEGER REFERENCES Users, report TEXT);
