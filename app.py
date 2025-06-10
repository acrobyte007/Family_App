import streamlit as st
import requests
from datetime import datetime

# FastAPI backend URL
BASE_URL = "http://localhost:8000"

# Streamlit app
st.title("Family Planner")

# Role selection
role = st.selectbox("Select your role", ["Parent", "Cook", "Driver"])

# Helper function to make API requests
def make_api_request(method, endpoint, data=None, params=None):
    try:
        if method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data, params=params)
        elif method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}", params=params)
        elif method == "DELETE":
            response = requests.delete(f"{BASE_URL}{endpoint}", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error: {e}")
        return None

# Parent-specific functionality
if role == "Parent":
    st.header("Add Family Member")
    with st.form("add_family_member"):
        name = st.text_input("Family Member Name")
        submit = st.form_submit_button("Add")
        if submit and name:
            result = make_api_request("POST", "/family_member", data={"name": name}, params={"role": "Parent"})
            if result:
                st.success(result.get("message", "Family member added"))

    st.header("Add Child Activity")
    with st.form("add_activity"):
        name = st.text_input("Activity Name")
        time = st.text_input("Time (e.g., 14:00)")
        days = st.multiselect("Days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        location = st.text_input("Location")
        caregiver = st.text_input("Caregiver")
        repetition = st.selectbox("Repetition", ["Weekly", "One-time"])
        driver_required = st.checkbox("Driver Required")
        date = st.date_input("Date", value=datetime.now())
        submit = st.form_submit_button("Add")
        if submit and name and time and days and location and caregiver and repetition and date:
            data = {
                "name": name,
                "time": time,
                "days": days,
                "location": location,
                "caregiver": caregiver,
                "repetition": repetition,
                "driver_required": driver_required,
                "date": date.strftime("%Y-%m-%d")
            }
            result = make_api_request("POST", "/Child_activity", data=data, params={"role": "Parent"})
            if result:
                st.success(result.get("message", "Activity added"))
    st.header("Delete Activity")
    with st.form("delete_activity"):
        # Fetch activities directly from the backend (use /driver_schedule as a fallback to get activities)
        result = make_api_request("GET", "/driver_schedule", params={"role": "Parent"})
        activity_names = [entry["activity"] for entry in result.get("schedule", [])] if result else []
        if activity_names:
            activity_name = st.selectbox("Select Activity to Delete", activity_names)
            submit = st.form_submit_button("Delete Activity")
            if submit:
                result = make_api_request("DELETE", f"/activity/{activity_name}", params={"role": "Parent"})
                if result:
                    st.success(result.get("message", "Activity deleted"))
                else:
                    st.error("Failed to delete activity")
        else:
            st.warning("No activities available to delete")

# Parent and Cook can view shopping list
if role in ["Parent", "Cook"]:
    st.header("Shopping List")
    if st.button("View Shopping List"):
        result = make_api_request("GET", "/shopping_list_items", params={"role": role})
        if result:
            items = result.get("shopping_list_items", [])
            if items:
                st.write("Shopping List Items:")
                for item in items:
                    st.write(f"- {item}")
            else:
                st.warning("No shopping list items available")

# Parent and Driver can view driver schedule
if role in ["Parent", "Driver"]:
    st.header("Driver Schedule")
    if st.button("View Driver Schedule"):
        result = make_api_request("GET", "/driver_schedule", params={"role": role})
        if result:
            st.write(result.get("message", "No schedule retrieved"))
            schedule = result.get("schedule", [])
            if schedule:
                st.write("Schedule:")
                for entry in schedule:
                    st.write(f"- {entry['day']} {entry['date']}: {entry['activity']} at {entry['time']} ({entry['location']}, Caregiver: {entry['caregiver']}, Driver Required: {entry['driver_required']})")
            else:
                st.warning("No driver-required activities in the schedule")

# Cook can view meal plan
if role == "Cook":
    st.header("Meal Plan")
    if st.button("View Meal Plan"):
        result = make_api_request("GET", "/state", params={"role": "Cook"})
        if result:
            meal_plan = result.get("meal_plan", {})
            if meal_plan:
                st.write("Meal Plan:")
                for day, meals in meal_plan.items():
                    st.write(f"{day.capitalize()}:")
                    for i, meal in enumerate(meals):
                        meal_type = ["Breakfast", "Lunch", "Dinner"][i] if i < 3 else f"Meal {i+1}"
                        st.write(f"  - {meal_type}: {meal[0]}")
            else:
                st.warning("No meal plan available")

# Parent can generate meal plan
if role == "Parent":
    st.header("Generate Meal Plan")
    with st.form("generate_meal_plan"):
        preferences = st.text_area("Meal Preferences (e.g., vegetarian, low-carb)")
        submit = st.form_submit_button("Generate")
        if submit and preferences:
            result = make_api_request("POST", "/meal_plan", data={"preferences": preferences}, params={"role": "Parent"})
            if result:
                st.success(result.get("message", "Meal plan generated"))
                st.write("Generated Meal Plan:", result.get("meal_plan", {}))