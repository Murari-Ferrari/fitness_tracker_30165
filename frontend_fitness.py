import streamlit as st
import pandas as pd
from datetime import date
from backend_fitness import (
    create_user, get_user, get_all_users, update_user, delete_user,
    add_friend, remove_friend, get_friends_list,
    create_workout_with_exercises, get_all_workouts_for_user, get_exercises_for_workout,
    create_goal, get_goals, update_goal_progress, delete_goal,
    get_business_insights, get_leaderboard_data
)

# Initialize session state for user ID
if 'user_id' not in st.session_state:
    st.session_state.user_id = None

st.set_page_config(layout="wide")
st.title("Sai Mohan Murari Pupala_30165_🏋️ Personal Fitness Tracker")

# User selection or creation in the sidebar
st.sidebar.header("User Management")
users = get_all_users()
if users:
    user_names = {user[1]: user[0] for user in users}
    user_selection = st.sidebar.selectbox("Select User", ["- Create New User -"] + list(user_names.keys()))
    if user_selection == "- Create New User -":
        with st.sidebar.form("new_user_form"):
            st.subheader("Create New User")
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
            new_weight = st.number_input("Weight (kg)", min_value=0.0, format="%.2f")
            submitted = st.form_submit_button("Create User")
            if submitted:
                new_id = create_user(new_name, new_email, new_weight)
                if new_id:
                    st.success(f"User '{new_name}' created successfully with ID: {new_id}")
                    st.session_state.user_id = new_id
                    st.rerun()
                else:
                    st.error("Failed to create user. Email may already be in use.")
    else:
        st.session_state.user_id = user_names[user_selection]
        st.sidebar.write(f"Logged in as: **{user_selection}**")
        
        if st.sidebar.button("Log out"):
            st.session_state.user_id = None
            st.rerun()
else:
    st.sidebar.info("No users found. Please create a new user.")
    with st.sidebar.form("new_user_form"):
        st.subheader("Create New User")
        new_name = st.text_input("Name")
        new_email = st.text_input("Email")
        new_weight = st.number_input("Weight (kg)", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Create User")
        if submitted:
            new_id = create_user(new_name, new_email, new_weight)
            if new_id:
                st.success(f"User '{new_name}' created successfully with ID: {new_id}")
                st.session_state.user_id = new_id
                st.rerun()
            else:
                st.error("Failed to create user. Email may already be in use.")

# Main content
if st.session_state.user_id:
    user_data = get_user(st.session_state.user_id)
    if user_data:
        st.header(f"Welcome, {user_data[1]}!")

    menu_options = ["Log Workout", "View Progress", "Set Goals", "Friends & Leaderboard", "Business Insights"]
    selected_option = st.selectbox("Select an action:", menu_options)

    # --- Log Workout Section ---
    if selected_option == "Log Workout":
        st.subheader("Log a New Workout")
        with st.form("new_workout_form"):
            workout_date = st.date_input("Date", value=date.today())
            duration = st.number_input("Duration (minutes)", min_value=1)
            st.markdown("### Add Exercises")
            exercises = []
            num_exercises = st.number_input("Number of exercises", min_value=1, value=1)
            for i in range(num_exercises):
                st.markdown(f"**Exercise {i+1}**")
                ex_name = st.text_input("Exercise Name", key=f"ex_name_{i}")
                ex_sets = st.number_input("Sets", min_value=1, key=f"ex_sets_{i}")
                ex_reps = st.number_input("Reps", min_value=1, key=f"ex_reps_{i}")
                ex_weight = st.number_input("Weight (kg)", min_value=0.0, format="%.2f", key=f"ex_weight_{i}")
                exercises.append({'name': ex_name, 'sets': ex_sets, 'reps': ex_reps, 'weight': ex_weight})
            
            submitted = st.form_submit_button("Log Workout")
            if submitted:
                if create_workout_with_exercises(st.session_state.user_id, workout_date, duration, exercises):
                    st.success("Workout logged successfully!")
                else:
                    st.error("Failed to log workout.")

    # --- View Progress Section ---
    elif selected_option == "View Progress":
        st.subheader("Workout History & Progress")
        workouts = get_all_workouts_for_user(st.session_state.user_id)
        if workouts:
            df_workouts = pd.DataFrame(workouts, columns=["Workout ID", "Date", "Duration (min)"])
            
            st.markdown("#### Your Workout History")
            st.dataframe(df_workouts)

            selected_workout_id = st.selectbox("Select a workout to view exercises:", df_workouts["Workout ID"])
            if selected_workout_id:
                exercises = get_exercises_for_workout(selected_workout_id)
                if exercises:
                    df_exercises = pd.DataFrame(exercises, columns=["Exercise Name", "Sets", "Reps", "Weight (kg)"])
                    st.markdown("#### Exercises for Selected Workout")
                    st.dataframe(df_exercises)
                else:
                    st.info("No exercises found for this workout.")
        else:
            st.info("No workouts logged yet. Go to 'Log Workout' to get started.")

    # --- Goal Setting Section ---
    elif selected_option == "Set Goals":
        st.subheader("Set & Track Personal Goals")
        with st.form("new_goal_form"):
            goal_description = st.text_area("Goal Description")
            target_value = st.number_input("Target Value (e.g., workouts per week)", min_value=1)
            submitted = st.form_submit_button("Set Goal")
            if submitted:
                if create_goal(st.session_state.user_id, goal_description, target_value):
                    st.success("Goal set successfully!")
                else:
                    st.error("Failed to set goal.")

        st.markdown("---")
        st.markdown("### Your Current Goals")
        goals = get_goals(st.session_state.user_id)
        if goals:
            for goal in goals:
                goal_id, description, target, progress = goal
                st.write(f"**Goal ID:** {goal_id}")
                st.write(f"**Description:** {description}")
                st.write(f"**Target:** {target}")
                
                new_progress = st.number_input("Update Progress:", min_value=0, value=progress, key=f"goal_progress_{goal_id}")
                if new_progress != progress:
                    if update_goal_progress(goal_id, new_progress):
                        st.success(f"Progress for goal {goal_id} updated to {new_progress}!")
                    else:
                        st.error("Failed to update goal progress.")
                
                if st.button(f"Delete Goal {goal_id}", key=f"delete_goal_{goal_id}"):
                    if delete_goal(goal_id):
                        st.success(f"Goal {goal_id} deleted successfully.")
                        st.rerun()
                    else:
                        st.error("Failed to delete goal.")

        else:
            st.info("No goals set yet.")

    # --- Friends & Leaderboard Section ---
    elif selected_option == "Friends & Leaderboard":
        st.subheader("Friends")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Add Friends")
            all_users = get_all_users()
            user_map = {user[1]: user[0] for user in all_users if user[0] != st.session_state.user_id}
            if user_map:
                friend_to_add = st.selectbox("Select a user to add:", list(user_map.keys()))
                if st.button("Add Friend"):
                    success, message = add_friend(st.session_state.user_id, user_map[friend_to_add])
                    if success:
                        st.success(message)
                    else:
                        st.warning(message)

        with col2:
            st.markdown("#### Your Friends List")
            friends_list = get_friends_list(st.session_state.user_id)
            if friends_list:
                df_friends = pd.DataFrame(friends_list, columns=["Friend ID", "Name"])
                st.dataframe(df_friends)
                friend_to_remove = st.selectbox("Select a friend to remove:", df_friends["Friend ID"])
                if st.button("Remove Friend"):
                    if remove_friend(st.session_state.user_id, friend_to_remove):
                        st.success("Friend removed.")
                        st.rerun()
                    else:
                        st.error("Failed to remove friend.")
            else:
                st.info("You have no friends yet. Add some to get started!")

        st.markdown("---")
        st.subheader("Leaderboard")
        leaderboard_metric = st.selectbox(
            "Select a metric:",
            options=["total_workouts_last_30_days", "total_duration_last_30_days", "avg_duration_all_time"],
            format_func=lambda x: x.replace('_', ' ').title()
        )
        leaderboard_data = get_leaderboard_data(leaderboard_metric, st.session_state.user_id)
        if leaderboard_data:
            df_leaderboard = pd.DataFrame(leaderboard_data, columns=["User Name", "Metric Value"])
            st.dataframe(df_leaderboard.reset_index(drop=True).style.background_gradient(cmap='Greens'))
        else:
            st.info("No data available for the leaderboard.")

    # --- Business Insights Section ---
    elif selected_option == "Business Insights":
        st.subheader("Your Fitness Journey Insights")
        insights = get_business_insights(st.session_state.user_id)
        if insights:
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric(label="Total Workouts", value=insights['total_workouts'])
            with col2:
                st.metric(label="Total Duration (min)", value=f"{insights['total_duration']:.2f}")
            with col3:
                st.metric(label="Avg Duration (min)", value=f"{insights['avg_duration']:.2f}")
            with col4:
                st.metric(label="Min Duration (min)", value=f"{insights['min_duration']:.2f}")
            with col5:
                st.metric(label="Max Duration (min)", value=f"{insights['max_duration']:.2f}")
        else:
            st.info("No workout data available to generate insights.")

else:
    st.info("Please select or create a user from the sidebar to use the application.")