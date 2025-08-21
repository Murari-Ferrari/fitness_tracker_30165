CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    weight DECIMAL(5,2)
);

--
-- Table structure for `workouts`
--
CREATE TABLE workouts (
    workout_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    workout_date DATE NOT NULL,
    duration_minutes INT NOT NULL
);

--
-- Table structure for `exercises`
--
CREATE TABLE exercises (
    exercise_id SERIAL PRIMARY KEY,
    workout_id INT REFERENCES workouts(workout_id) ON DELETE CASCADE,
    exercise_name VARCHAR(255) NOT NULL,
    sets INT,
    reps INT,
    weight DECIMAL(6,2)
);

--
-- Table structure for `friends`
--
CREATE TABLE friends (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    friend_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE (user_id, friend_id)
);

--
-- Table structure for `goals`
--
CREATE TABLE goals (
    goal_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    goal_description TEXT NOT NULL,
    target_value INT,
    progress_value INT DEFAULT 0
);