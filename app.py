import streamlit as st
from typing import Dict, List
import pandas as pd
from meal_plane import weekly_meal_planner
from shopping import shopping_list_generator
from db import (
    load_latest_data, get_timestamps, load_data_by_timestamp,
    save_family_member, save_activity, update_activity, delete_activity,
    save_meal_plan, save_shopping_list, save_schedule,
    FamilyMember, Activity, MealPlan, ShoppingList, Schedule
)

def initialize_session_state():
    """Initialize session state variables."""
    if "role" not in st.session_state:
        st.session_state.role = None
    if "family_members" not in st.session_state:
        st.session_state.family_members = []
    if "activities" not in st.session_state:
        st.session_state.activities = []
    if "meal_plan" not in st.session_state:
        st.session_state.meal_plan = {}
    if "shopping_list" not in st.session_state:
        st.session_state.shopping_list = {}
    if "schedule" not in st.session_state:
        st.session_state.schedule = []

def load_session_state():
    """Load latest data into session state."""
    data = load_latest_data()
    st.session_state.family_members = data["family_members"]
    st.session_state.activities = data["activities"]
    st.session_state.meal_plan = data["meal_plan"]
    st.session_state.shopping_list = data["shopping_list"]
    st.session_state.schedule = data["schedule"]

def generate_schedule(activities: List[Dict]) -> List[Dict]:
    """Generate a reminder schedule from activities."""
    schedule = []
    for activity in activities:
        days = activity.get("days", [])
        for day in days:
            schedule.append({
                "day": day,
                "activity": activity["name"],
                "time": activity["time"],
                "location": activity["location"],
                "caregiver": activity["caregiver"]
            })
    return sorted(schedule, key=lambda x: (x["day"], x["time"]))

def create_meal_plan_table(meal_plan: Dict) -> pd.DataFrame:
    """Create a day-wise table for meals with Breakfast, Lunch, and Dinner columns."""
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meal_table = {"Day": [day.capitalize() for day in days], "Breakfast": [], "Lunch": [], "Dinner": []}
    
    for day in days:
        meals = meal_plan.get(day, [])
        breakfast = meals[0][0] if len(meals) > 0 and len(meals[0]) > 0 else "No meal planned"
        lunch = meals[1][0] if len(meals) > 1 and len(meals[1]) > 0 else "No meal planned"
        dinner = meals[2][0] if len(meals) > 2 and len(meals[2]) > 0 else "No meal planned"
        meal_table["Breakfast"].append(breakfast)
        meal_table["Lunch"].append(lunch)
        meal_table["Dinner"].append(dinner)
    
    return pd.DataFrame(meal_table)

def display_meal_plan_details(meal_plan: Dict):
    """Display meal plan details with ingredients in an expander."""
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for day in days:
        meals = meal_plan.get(day, [])
        if meals:
            with st.expander(f"{day.capitalize()} Meal Details"):
                for i, meal in enumerate(meals):
                    meal_type = ["Breakfast", "Lunch", "Dinner"][i] if i < 3 else f"Meal {i+1}"
                    st.write(f"**{meal_type}**: {meal[0]}")
                    st.write(f"Ingredients: {meal[1] if len(meal) > 1 else 'None'}")

def main():
    st.title("Family Planner App")
    initialize_session_state()
    load_session_state()

    # Role selection
    st.session_state.role = st.selectbox("Select your role", ["Parent", "Cook", "Driver"], key="role_select")

    if st.session_state.role == "Parent":
        # Family members management
        st.subheader("Register Family Members")
        # Dropdown to view previous family members
        family_timestamps = get_timestamps(FamilyMember)
        if family_timestamps:
            selected_family_ts = st.selectbox("View Previous Family Members", ["Latest"] + family_timestamps, key="family_ts")
            if selected_family_ts != "Latest":
                st.session_state.family_members = load_data_by_timestamp(FamilyMember, selected_family_ts, "family_members") or []

        with st.form("family_form"):
            member_name = st.text_input("Family Member Name")
            submit_member = st.form_submit_button("Add Member")
            if submit_member and member_name:
                save_family_member(member_name)
                st.session_state.family_members.append(member_name)
                st.success(f"Added {member_name} to family members")

        if st.session_state.family_members:
            st.write("Family Members:")
            st.write(st.session_state.family_members)

        # Activity management
        st.subheader("Manage Activities")
        # Dropdown to view previous activities
        activity_timestamps = get_timestamps(Activity)
        if activity_timestamps:
            selected_activity_ts = st.selectbox("View Previous Activities", ["Latest"] + activity_timestamps, key="activity_ts")
            if selected_activity_ts != "Latest":
                st.session_state.activities = load_data_by_timestamp(Activity, selected_activity_ts, "activities") or []
                st.session_state.schedule = generate_schedule(st.session_state.activities)

        with st.form("activity_form"):
            activity_name = st.text_input("Activity Name")
            activity_time = st.time_input("Time")
            activity_days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            location = st.text_input("Location")
            caregiver = st.selectbox("Caregiver", st.session_state.family_members + ["Driver"])
            repetition = st.selectbox("Repetition", ["Weekly", "One-time"])
            submit_activity = st.form_submit_button("Add Activity")
            if submit_activity and activity_name and activity_time and activity_days:
                new_activity = {
                    "name": activity_name,
                    "time": activity_time.strftime("%H:%M"),
                    "days": activity_days,
                    "location": location,
                    "caregiver": caregiver,
                    "repetition": repetition
                }
                st.session_state.activities.append(new_activity)
                save_activity(new_activity)
                st.session_state.schedule = generate_schedule(st.session_state.activities)
                save_schedule(st.session_state.schedule)
                st.success("Activity added")

        # Edit/Delete activities
        if st.session_state.activities:
            st.subheader("Current Activities")
            activity_df = pd.DataFrame(st.session_state.activities)
            st.table(activity_df)
            with st.form("edit_delete_form"):
                activity_to_edit = st.selectbox("Select Activity to Edit/Delete", [a["name"] for a in st.session_state.activities])
                new_name = st.text_input("New Activity Name", value=activity_to_edit)
                new_time = st.time_input("New Time", value=pd.to_datetime(st.session_state.activities[[a["name"] for a in st.session_state.activities].index(activity_to_edit)]["time"]).time())
                new_days = st.multiselect("New Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], default=st.session_state.activities[[a["name"] for a in st.session_state.activities].index(activity_to_edit)]["days"])
                new_location = st.text_input("New Location", value=st.session_state.activities[[a["name"] for a in st.session_state.activities].index(activity_to_edit)]["location"])
                new_caregiver = st.selectbox("New Caregiver", st.session_state.family_members + ["Driver"], index=(st.session_state.family_members + ["Driver"]).index(st.session_state.activities[[a["name"] for a in st.session_state.activities].index(activity_to_edit)]["caregiver"]))
                new_repetition = st.selectbox("New Repetition", ["Weekly", "One-time"], index=["Weekly", "One-time"].index(st.session_state.activities[[a["name"] for a in st.session_state.activities].index(activity_to_edit)]["repetition"]))
                col1, col2 = st.columns(2)
                with col1:
                    edit_activity = st.form_submit_button("Edit Activity")
                with col2:
                    delete_activity = st.form_submit_button("Delete Activity")
                
                if edit_activity:
                    idx = [a["name"] for a in st.session_state.activities].index(activity_to_edit)
                    new_activity = {
                        "name": new_name,
                        "time": new_time.strftime("%H:%M"),
                        "days": new_days,
                        "location": new_location,
                        "caregiver": new_caregiver,
                        "repetition": new_repetition
                    }
                    st.session_state.activities[idx] = new_activity
                    update_activity(activity_to_edit, new_activity)
                    st.session_state.schedule = generate_schedule(st.session_state.activities)
                    save_schedule(st.session_state.schedule)
                    st.success("Activity updated")
                
                if delete_activity:
                    delete_activity(activity_to_edit)
                    st.session_state.activities = [a for a in st.session_state.activities if a["name"] != activity_to_edit]
                    st.session_state.schedule = generate_schedule(st.session_state.activities)
                    save_schedule(st.session_state.schedule)
                    st.success("Activity deleted")

        # Meal planning
        st.subheader("Generate Meal Plan")
        # Dropdown to view previous meal plans
        meal_plan_timestamps = get_timestamps(MealPlan)
        if meal_plan_timestamps:
            selected_meal_plan_ts = st.selectbox("View Previous Meal Plans", ["Latest"] + meal_plan_timestamps, key="meal_plan_ts")
            if selected_meal_plan_ts != "Latest":
                st.session_state.meal_plan = load_data_by_timestamp(MealPlan, selected_meal_plan_ts, "meal_plan") or {}
                st.session_state.shopping_list = shopping_list_generator(st.session_state.meal_plan)
                save_shopping_list(st.session_state.shopping_list)

        with st.form("meal_plan_form"):
            meal_prompt = st.text_area("Enter meal preferences (e.g., Italian vegetarian spicy meals)")
            submit_meal = st.form_submit_button("Generate Meal Plan")
            if submit_meal and meal_prompt:
                tool_calls = weekly_meal_planner(meal_prompt)
                st.session_state.meal_plan = tool_calls[0]["args"]
                st.session_state.shopping_list = shopping_list_generator(st.session_state.meal_plan)
                save_meal_plan(st.session_state.meal_plan)
                save_shopping_list(st.session_state.shopping_list)
                st.success("Meal plan generated")

        # Display meal plan as a day-wise table
        if st.session_state.meal_plan:
            st.subheader("Weekly Meal Plan")
            meal_table = create_meal_plan_table(st.session_state.meal_plan)
            st.table(meal_table)
            st.write("View Meal Details and Ingredients")
            display_meal_plan_details(st.session_state.meal_plan)
        
        # Display shopping list as a horizontal list
        if st.session_state.shopping_list:
            st.subheader("Shopping List")
            # Dropdown to view previous shopping lists
            shopping_list_timestamps = get_timestamps(ShoppingList)
            if shopping_list_timestamps:
                selected_shopping_list_ts = st.selectbox("View Previous Shopping Lists", ["Latest"] + shopping_list_timestamps, key="shopping_list_ts")
                if selected_shopping_list_ts != "Latest":
                    st.session_state.shopping_list = load_data_by_timestamp(ShoppingList, selected_shopping_list_ts, "shopping_list") or {}
            items = [item for section, items_list in st.session_state.shopping_list.items() for item in items_list]
            st.write(", ".join(items))

    elif st.session_state.role == "Cook":
        # Display meal plan as a day-wise table
        if st.session_state.meal_plan:
            st.subheader("Weekly Meal Plan")
            # Dropdown to view previous meal plans
            meal_plan_timestamps = get_timestamps(MealPlan)
            if meal_plan_timestamps:
                selected_meal_plan_ts = st.selectbox("View Previous Meal Plans", ["Latest"] + meal_plan_timestamps, key="meal_plan_ts_cook")
                if selected_meal_plan_ts != "Latest":
                    st.session_state.meal_plan = load_data_by_timestamp(MealPlan, selected_meal_plan_ts, "meal_plan") or {}
            meal_table = create_meal_plan_table(st.session_state.meal_plan)
            st.table(meal_table)
            st.write("View Meal Details and Ingredients")
            display_meal_plan_details(st.session_state.meal_plan)
        
        # Display shopping list as a horizontal list
        if st.session_state.shopping_list:
            st.subheader("Shopping List")
            # Dropdown to view previous shopping lists
            shopping_list_timestamps = get_timestamps(ShoppingList)
            if shopping_list_timestamps:
                selected_shopping_list_ts = st.selectbox("View Previous Shopping Lists", ["Latest"] + shopping_list_timestamps, key="shopping_list_ts_cook")
                if selected_shopping_list_ts != "Latest":
                    st.session_state.shopping_list = load_data_by_timestamp(ShoppingList, selected_shopping_list_ts, "shopping_list") or {}
            items = [item for section, items_list in st.session_state.shopping_list.items() for item in items_list]
            st.write(", ".join(items))

    elif st.session_state.role == "Driver":
        # Clear meal plan and shopping list
        st.session_state.meal_plan = {}
        st.session_state.shopping_list = {}
        # Display filtered schedule for Driver
        if st.session_state.schedule:
            st.subheader("Driver Schedule")
            # Dropdown to view previous schedules
            schedule_timestamps = get_timestamps(Schedule)
            if schedule_timestamps:
                selected_schedule_ts = st.selectbox("View Previous Schedules", ["Latest"] + schedule_timestamps, key="schedule_ts")
                if selected_schedule_ts != "Latest":
                    st.session_state.schedule = load_data_by_timestamp(Schedule, selected_schedule_ts, "schedule") or []
            driver_schedule = [s for s in st.session_state.schedule if s["caregiver"] == "Driver"]
            if driver_schedule:
                schedule_df = pd.DataFrame(driver_schedule)
                st.table(schedule_df)
            else:
                st.write("No activities assigned to Driver")

if __name__ == "__main__":
    main()