import psycopg2
from datetime import datetime, date

# Database connection function
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="midterm",
            user="postgres",
            password="99Mur@ri99"
        )
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# --- User Profile CRUD Operations ---

def create_user(name, email, weight):
    """Adds a new user to the users table."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (name, email, weight) VALUES (%s, %s, %s) RETURNING user_id;",
                    (name, email, weight)
                )
                user_id = cur.fetchone()[0]
                conn.commit()
                return user_id
        except psycopg2.IntegrityError as e:
            conn.rollback()
            print(f"Error: A user with this email already exists. {e}")
            return None
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()

def get_user(user_id):
    """Retrieves a single user's profile."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, name, email, weight FROM users WHERE user_id = %s;", (user_id,))
                user_data = cur.fetchone()
                return user_data
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()
    return None

def get_all_users():
    """Retrieves all users from the users table."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, name, email, weight FROM users;")
                users = cur.fetchall()
                return users
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()
    return None

def update_user(user_id, name, email, weight):
    """Updates an existing user's profile."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET name = %s, email = %s, weight = %s WHERE user_id = %s;",
                    (name, email, weight, user_id)
                )
                conn.commit()
                return True
        except psycopg2.IntegrityError as e:
            conn.rollback()
            print(f"Error: A user with this email already exists. {e}")
            return False
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

def delete_user(user_id):
    """Deletes a user and all their related data (workouts, exercises, goals, friends)."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Delete related records first to avoid foreign key constraints
                cur.execute("DELETE FROM exercises WHERE workout_id IN (SELECT workout_id FROM workouts WHERE user_id = %s);", (user_id,))
                cur.execute("DELETE FROM workouts WHERE user_id = %s;", (user_id,))
                cur.execute("DELETE FROM goals WHERE user_id = %s;", (user_id,))
                cur.execute("DELETE FROM friends WHERE user_id = %s OR friend_id = %s;", (user_id, user_id))
                cur.execute("DELETE FROM users WHERE user_id = %s;", (user_id,))
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

# --- Friends CRUD Operations ---

def add_friend(user_id, friend_id):
    """Adds a friend connection. Checks for existing connections and prevents self-friending."""
    conn = get_db_connection()
    if conn:
        if user_id == friend_id:
            return False, "Cannot add yourself as a friend."
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM friends WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s);",
                    (user_id, friend_id, friend_id, user_id)
                )
                if cur.fetchone():
                    return False, "Friend connection already exists."
                
                # Add a one-way connection. A symmetric connection can be added, but this is a simple approach.
                cur.execute("INSERT INTO friends (user_id, friend_id) VALUES (%s, %s);", (user_id, friend_id))
                conn.commit()
                return True, "Friend added successfully."
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False, f"Database error: {e}"
        finally:
            conn.close()

def remove_friend(user_id, friend_id):
    """Removes a friend connection."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM friends WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s);",
                            (user_id, friend_id, friend_id, user_id))
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

def get_friends_list(user_id):
    """Retrieves a list of a user's friends."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT u.user_id, u.name
                    FROM friends f
                    JOIN users u ON u.user_id = f.friend_id
                    WHERE f.user_id = %s
                    UNION
                    SELECT u.user_id, u.name
                    FROM friends f
                    JOIN users u ON u.user_id = f.user_id
                    WHERE f.friend_id = %s;
                """, (user_id, user_id))
                friends = cur.fetchall()
                return friends
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()

# --- Workout & Exercises CRUD Operations ---

def create_workout_with_exercises(user_id, workout_date, duration_minutes, exercises):
    """Logs a new workout and its associated exercises in a single transaction."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Start a transaction to ensure atomicity
                cur.execute(
                    "INSERT INTO workouts (user_id, workout_date, duration_minutes) VALUES (%s, %s, %s) RETURNING workout_id;",
                    (user_id, workout_date, duration_minutes)
                )
                workout_id = cur.fetchone()[0]

                for exercise in exercises:
                    cur.execute(
                        "INSERT INTO exercises (workout_id, exercise_name, sets, reps, weight) VALUES (%s, %s, %s, %s, %s);",
                        (workout_id, exercise['name'], exercise['sets'], exercise['reps'], exercise['weight'])
                    )
                
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

def get_all_workouts_for_user(user_id):
    """Retrieves all workouts for a specific user."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT workout_id, workout_date, duration_minutes FROM workouts WHERE user_id = %s ORDER BY workout_date DESC;", (user_id,))
                workouts = cur.fetchall()
                return workouts
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()

def get_exercises_for_workout(workout_id):
    """Retrieves all exercises for a specific workout."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT exercise_name, sets, reps, weight FROM exercises WHERE workout_id = %s;", (workout_id,))
                exercises = cur.fetchall()
                return exercises
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()

# --- Goals CRUD Operations ---

def create_goal(user_id, description, target_value):
    """Creates a new goal for a user."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO goals (user_id, goal_description, target_value) VALUES (%s, %s, %s);",
                    (user_id, description, target_value)
                )
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

def get_goals(user_id):
    """Retrieves all goals for a user."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT goal_id, goal_description, target_value, progress_value FROM goals WHERE user_id = %s;", (user_id,))
                goals = cur.fetchall()
                return goals
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()

def update_goal_progress(goal_id, new_progress):
    """Updates the progress of a specific goal."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("UPDATE goals SET progress_value = %s WHERE goal_id = %s;", (new_progress, goal_id))
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

def delete_goal(goal_id):
    """Deletes a goal."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM goals WHERE goal_id = %s;", (goal_id,))
                conn.commit()
                return True
        except psycopg2.Error as e:
            conn.rollback()
            print(f"Database error: {e}")
            return False
        finally:
            conn.close()

# --- Business Insights & Leaderboard Queries ---

def get_business_insights(user_id):
    """
    Retrieves aggregate business insights for a user.
    Uses COUNT, SUM, AVG, MIN, MAX.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        COUNT(workout_id) as total_workouts,
                        COALESCE(SUM(duration_minutes), 0) as total_duration,
                        COALESCE(AVG(duration_minutes), 0) as avg_duration,
                        COALESCE(MIN(duration_minutes), 0) as min_duration,
                        COALESCE(MAX(duration_minutes), 0) as max_duration
                    FROM workouts
                    WHERE user_id = %s;
                """, (user_id,))
                insights = cur.fetchone()
                # Use a dictionary for cleaner access
                return {
                    'total_workouts': insights[0],
                    'total_duration': insights[1],
                    'avg_duration': insights[2],
                    'min_duration': insights[3],
                    'max_duration': insights[4]
                }
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()

def get_leaderboard_data(metric, user_id):
    """
    Retrieves leaderboard data for a user and their friends based on a selected metric.
    The metric is expected to be a valid SQL column/function to order by.
    """
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Find the user's friends (including the user themselves for ranking)
                cur.execute("""
                    SELECT user_id FROM friends WHERE friend_id = %s
                    UNION
                    SELECT friend_id FROM friends WHERE user_id = %s
                    UNION
                    SELECT %s;
                """, (user_id, user_id, user_id))
                friend_ids = [row[0] for row in cur.fetchall()]

                # Handle different metrics for ranking
                if metric == 'total_workouts_last_30_days':
                    query = f"""
                        SELECT u.name, COUNT(w.workout_id) AS metric_value
                        FROM users u
                        LEFT JOIN workouts w ON u.user_id = w.user_id AND w.workout_date >= CURRENT_DATE - INTERVAL '30 days'
                        WHERE u.user_id IN %s
                        GROUP BY u.name
                        ORDER BY metric_value DESC, u.name ASC;
                    """
                elif metric == 'total_duration_last_30_days':
                    query = f"""
                        SELECT u.name, COALESCE(SUM(w.duration_minutes), 0) AS metric_value
                        FROM users u
                        LEFT JOIN workouts w ON u.user_id = w.user_id AND w.workout_date >= CURRENT_DATE - INTERVAL '30 days'
                        WHERE u.user_id IN %s
                        GROUP BY u.name
                        ORDER BY metric_value DESC, u.name ASC;
                    """
                elif metric == 'avg_duration_all_time':
                     query = f"""
                        SELECT u.name, COALESCE(AVG(w.duration_minutes), 0) AS metric_value
                        FROM users u
                        LEFT JOIN workouts w ON u.user_id = w.user_id
                        WHERE u.user_id IN %s
                        GROUP BY u.name
                        ORDER BY metric_value DESC, u.name ASC;
                    """
                else: # Default to total duration
                    query = f"""
                        SELECT u.name, COALESCE(SUM(w.duration_minutes), 0) AS metric_value
                        FROM users u
                        LEFT JOIN workouts w ON u.user_id = w.user_id
                        WHERE u.user_id IN %s
                        GROUP BY u.name
                        ORDER BY metric_value DESC, u.name ASC;
                    """
                
                # Use `psycopg2.extras.execute_values` for safe IN clause usage
                # Note: `psycopg2` can't directly use a list with the %s placeholder for IN.
                # A common workaround is to format the query or use a custom function.
                # Here, we will use a simple, but safe, IN clause with a tuple.
                cur.execute(query, (tuple(friend_ids),))
                leaderboard_data = cur.fetchall()
                
                return leaderboard_data
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            return None
        finally:
            conn.close()