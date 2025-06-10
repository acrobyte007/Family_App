import streamlit as st
import os
from dotenv import load_dotenv
from typing import Dict, List, Optional
from meal_plane import weekly_meal_planner
from shopping import shopping_list_generator
from activity import child_activity_planner

# Load environment variables
load_dotenv()

# Streamlit app configuration
st.set_page_config(page_title="Family Planner", layout="wide")

# Main app
def main():
    st.title("Family Planner App")

    # Role selection
    role = st.sidebar.selectbox("Select Role", ["Parent", "Cook", "Driver"])

    # Initialize session state
    if "activities" not in st.session_state:
        st.session_state["activities"] = []
    if "weekly_meals" not in st.session_state:
        st.session_state["weekly_meals"] = {}
    if "shopping_list" not in st.session_state:
        st.session_state["shopping_list"] = {}
    if "activity_schedule" not in st.session_state:
        st.session_state["activity_schedule"] = {"reminders": []}
    if "family_members" not in st.session_state:
        st.session_state["family_members"] = []

    # Clear meal plan and shopping list for Driver role
    if role == "Driver":
        st.session_state["weekly_meals"] = {}
        st.session_state["shopping_list"] = {}

    # Register new family member (Parent only)
    if role == "Parent":
        st.subheader("Register Family Member")
        with st.form("member_form"):
            member_name = st.text_input("Member Name")
            submit_member = st.form_submit_button("Add Member")
            if submit_member and member_name:
                if member_name not in st.session_state["family_members"] and member_name.lower() != "driver":
                    st.session_state["family_members"].append(member_name)
                    st.success(f"Added {member_name} to family members!")
                else:
                    st.error("Member already exists or invalid (cannot use 'Driver').")

        # Display current family members
        if st.session_state["family_members"]:
            st.write("**Registered Family Members**")
            for member in st.session_state["family_members"]:
                st.write(f"- {member}")

    # Activity management (Parent only)
    if role == "Parent":
        st.subheader("Manage Activities")
        with st.form("activity_form"):
            activity_name = st.text_input("Activity Name")
            activity_time = st.text_input("Time (e.g., 15:00)")
            activity_days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            activity_location = st.text_input("Location")
            activity_repetition = st.selectbox("Repetition", ["weekly", "monthly", "one-time"])
            caregiver_options = ["Driver"] + st.session_state["family_members"]
            activity_caregiver = st.selectbox("Caregiver", caregiver_options)
            submit_activity = st.form_submit_button("Add Activity")

            if submit_activity and activity_name and activity_time and activity_days and activity_location and activity_caregiver:
                new_activity = {
                    "name": activity_name,
                    "time": activity_time,
                    "days": activity_days,
                    "location": activity_location,
                    "repetition": activity_repetition,
                    "caregiver": activity_caregiver.strip()
                }
                st.session_state["activities"].append(new_activity)
                st.success(f"Added {activity_name} to activities!")
                try:
                    st.session_state["activity_schedule"] = child_activity_planner(st.session_state["activities"], current_date="2025-06-09")
                except Exception as e:
                    st.warning(f"Failed to update activity schedule: {str(e)}")

        st.subheader("Current Activities")
        if st.session_state["activities"]:
            for i, activity in enumerate(st.session_state["activities"]):
                st.write(f"{activity['name']} at {activity['time']} on {', '.join(activity['days'])} ({activity['location']}, {activity['repetition']}, Caregiver: {activity['caregiver']})")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Edit {activity['name']}", key=f"edit_{i}"):
                        st.session_state["edit_index"] = i
                        st.session_state["edit_mode"] = True
                with col2:
                    if st.button(f"Delete {activity['name']}", key=f"delete_{i}"):
                        st.session_state["activities"].pop(i)
                        st.success(f"Deleted {activity['name']}")
                        try:
                            st.session_state["activity_schedule"] = child_activity_planner(st.session_state["activities"], current_date="2025-06-09")
                        except Exception as e:
                            st.warning(f"Failed to update activity schedule: {str(e)}")
                        st.rerun()

            if "edit_mode" in st.session_state and st.session_state["edit_mode"]:
                edit_index = st.session_state["edit_index"]
                activity = st.session_state["activities"][edit_index]
                with st.form(f"edit_form_{edit_index}"):
                    edit_name = st.text_input("Activity Name", value=activity["name"])
                    edit_time = st.text_input("Time", value=activity["time"])
                    edit_days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"], default=activity["days"])
                    edit_location = st.text_input("Location", value=activity["location"])
                    edit_repetition = st.selectbox("Repetition", ["weekly", "monthly", "one-time"], index=["weekly", "monthly", "one-time"].index(activity["repetition"]))
                    edit_caregiver = st.selectbox("Caregiver", caregiver_options, index=caregiver_options.index(activity["caregiver"]))
                    submit_edit = st.form_submit_button("Save Changes")

                    if submit_edit:
                        st.session_state["activities"][edit_index] = {
                            "name": edit_name,
                            "time": edit_time,
                            "days": edit_days,
                            "location": edit_location,
                            "repetition": edit_repetition,
                            "caregiver": edit_caregiver.strip()
                        }
                        st.session_state["edit_mode"] = False
                        st.success(f"Updated {edit_name}")
                        try:
                            st.session_state["activity_schedule"] = child_activity_planner(st.session_state["activities"], current_date="2025-06-09")
                        except Exception as e:
                            st.warning(f"Failed to update activity schedule: {str(e)}")
                        st.rerun()
        else:
            st.info("No activities added yet. Use the form above to add activities.")

    # Meal planning (Parent only)
    if role == "Parent":
        st.subheader("Meal Planning")
        with st.form("meal_form"):
            query = st.text_input("Meal Plan Query (e.g., 'Plan a week of Italian vegetarian spicy meals')", "Plan a week of Italian vegetarian spicy meals")
            submit_meal = st.form_submit_button("Generate Plan")

            if submit_meal:
                try:
                    tool_calls = weekly_meal_planner(query)
                    st.write("**Debug: Raw Tool Calls Response**")
                    st.write(tool_calls)
                    meal_plan = None
                    # Handle both flat and nested tool call structures
                    if isinstance(tool_calls, list):
                        for call in tool_calls:
                            if isinstance(call, dict):
                                # Handle nested tool_calls
                                if call.get("tool_calls"):
                                    for sub_call in call.get("tool_calls", []):
                                        if sub_call.get("function", {}).get("name") == "WeeklyMealPlan":
                                            meal_plan = sub_call["parameters"]
                                            break
                                # Handle direct WeeklyMealPlan call
                                elif call.get("function", {}).get("name") == "WeeklyMealPlan":
                                    meal_plan = call["parameters"]
                            if meal_plan:
                                break
                    if not meal_plan:
                        raise ValueError("No valid WeeklyMealPlan found in response")
                    
                    st.session_state["weekly_meals"] = meal_plan
                    try:
                        shopping_list = shopping_list_generator(meal_plan)
                        st.session_state["shopping_list"] = shopping_list
                    except Exception as e:
                        st.warning(f"Failed to generate shopping list: {str(e)}")
                        st.session_state["shopping_list"] = {}
                except Exception as e:
                    st.error(f"Failed to generate meal plan. Ensure the query specifies vegetarian meals and check your API key. Error: {str(e)}")
                    st.session_state["weekly_meals"] = {}
                    st.session_state["shopping_list"] = {}

    # Meal plan and shopping list display (Parent, Cook)
    if role in ["Parent", "Cook"]:
        if st.session_state["weekly_meals"]:
            st.subheader("Weekly Meal Plan")
            display_meal_plan(st.session_state["weekly_meals"])
        else:
            st.info("No meal plan available. Parent can generate a meal plan.")
        
        if st.session_state["shopping_list"]:
            st.subheader("Shopping List")
            display_shopping_list(st.session_state["shopping_list"])
        else:
            st.info("No shopping list available. Generate a meal plan to create one.")

    # Activity schedule (Parent, Driver)
    if role in ["Parent", "Driver"]:
        st.subheader("Activity Schedule")
        if role == "Parent":
            st.write("**Debug: Raw Activities**")
            st.write(st.session_state["activities"])
            st.write("**Debug: Raw Schedule Reminders**")
            st.write(st.session_state["activity_schedule"]["reminders"])

        if st.button("Refresh Activity Schedule"):
            try:
                st.session_state["activity_schedule"] = child_activity_planner(st.session_state["activities"], current_date="2025-06-09")
                st.success("Activity schedule refreshed!")
            except Exception as e:
                st.warning(f"Failed to refresh activity schedule: {str(e)}")
                st.session_state["activity_schedule"] = {"reminders": []}

        if role == "Driver":
            filtered_schedule = {
                "reminders": [
                    reminder for reminder in st.session_state["activity_schedule"]["reminders"]
                    if reminder.get("caregiver", "").lower().strip() == "driver"
                ]
            }
            st.write("**Debug: Filtered Reminders for Driver**")
            st.write(filtered_schedule["reminders"])
            display_activity_schedule(filtered_schedule)
        else:
            display_activity_schedule(st.session_state["activity_schedule"])

def display_meal_plan(meal_plan: Dict[str, List[List[str]]]):
    """Display the weekly meal plan in a table format."""
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meal_types = ["Breakfast", "Lunch", "Dinner"]

    for day in days:
        meals = meal_plan.get(day, [])
        if meals:
            st.write(f"**{day.capitalize()}**")
            table_data = []
            for i, meal in enumerate(meals):
                if i < len(meal_types):
                    dish_name = meal[0].split(": ", 1)[1] if ": " in meal[0] else meal[0]
                    ingredients = meal[1] if len(meal) > 1 else ""
                    table_data.append({
                        "Meal Type": meal_types[i],
                        "Dish Name": dish_name,
                        "Ingredients": ingredients
                    })
            st.table(table_data)
            st.write("---")
        else:
            st.write(f"**{day.capitalize()}**: No meals planned")

def display_shopping_list(shopping_list: Dict[str, List[str]]):
    """Display the shopping list, excluding empty sections."""
    for section, items in shopping_list.items():
        if items:
            st.write(f"**{section}**")
            for item in items:
                st.write(f"- {item}")

def display_activity_schedule(schedule: Dict):
    """Display the child activity schedule in a table format."""
    reminders = schedule.get("reminders", [])
    if not reminders:
        st.info("No activities scheduled.")
        return

    table_data = []
    for reminder in reminders:
        if isinstance(reminder, dict) and all(key in reminder for key in ["name", "time", "day", "location"]):
            table_data.append({
                "Activity Name": reminder["name"],
                "Time": reminder["time"],
                "Day": reminder["day"],
                "Location": reminder["location"],
                "Repetition": reminder.get("repetition", ""),
                "Caregiver": reminder.get("caregiver", "")
            })
        else:
            st.warning(f"Invalid reminder format: {reminder}")

    if table_data:
        st.table(table_data)
    else:
        st.info("No valid activities found in schedule.")

if __name__ == "__main__":
    main()