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
        driver_required = st.checkbox("Driver Required")
        date = st.date_input("Date", value=datetime.now())
        submit = st.form_submit_button("Add")
        if submit and name and time and days and location and date:
            data = {
                "name": name,
                "time": time,
                "days": days,
                "location": location,
                "driver_required": driver_required,
                "date": date.strftime("%Y-%m-%d")
            }
            result = make_api_request("POST", "/Child_activity", data=data, params={"role": "Parent"})
            if result:
                st.success(result.get("message", "Activity added"))

    st.header("Delete Activity")
    with st.form("delete_activity"):
        activities = make_api_request("GET", "/activities", params={"role": "Parent"})
        activity_names = activities.get("activity_names", []) if activities else []
        if activity_names:
            activity_name = st.selectbox("Select Activity to Delete", activity_names)
            submit = st.form_submit_button("Delete")
            if submit:
                result = make_api_request("POST", "/delete_activity", data={"activity_name": activity_name}, params={"role": "Parent"})
                if result:
                    st.success(result.get("message", "Activity deleted"))
        else:
            st.warning("No activities available to delete")

# Parent and Cook can view shopping list
if role in ["Parent", "Cook"]:
    st.header("Shopping List")
    if st.button("View Shopping List"):
        result = make_api_request("GET", "/shopping_list_items", params={"role": role})
        if result:
            st.write("Shopping List Items:", result.get("shopping_list_items", []))

# Parent and Driver can view driver schedule
if role in ["Parent", "Driver"]:
    st.header("Driver Schedule")
    if st.button("View Driver Schedule"):
        result = make_api_request("GET", "/driver_schedule", params={"role": role})
        if result:
            st.write(result.get("message", "No schedule retrieved"))
            st.write("Schedule:", result.get("schedule", []))

# Cook can view meal plan
if role == "Cook":
    st.header("Meal Plan")
    if st.button("View Meal Plan"):
        result = make_api_request("GET", "/state", params={"role": "Cook"})
        if result:
            st.write("Meal Plan:", result.get("meal_plan", {}))