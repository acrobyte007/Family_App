from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict
from meal_plane import weekly_meal_planner
from shopping import shopping_list_generator
from db import (
    load_latest_data,save_family_member, save_activity, delete_activity,save_meal_plan, save_shopping_list, save_schedule,
)
from enum import Enum

app = FastAPI(title="Family Planner API")

# Role Enum
class Role(str, Enum):
    PARENT = "Parent"
    COOK = "Cook"
    DRIVER = "Driver"

# Pydantic models
class FamilyMemberRequest(BaseModel):
    name: str

class ActivityRequest(BaseModel):
    name: str
    time: str
    days: List[str]
    location: str
    caregiver: str
    repetition: str
    driver_required: bool = False  # New field for driver requirement
    date: str  # Assuming date is required as per the endpoint

class ActivityUpdateRequest(BaseModel):
    name: str
    time: str
    days: List[str]
    location: str
    caregiver: str
    repetition: str
    driver_required: bool = False
    date: str

class MealPlanRequest(BaseModel):
    preferences: str

class StateResponse(BaseModel):
    family_members: List[str] = []
    activities: List[Dict] = []
    meal_plan: Dict = {}
    shopping_list: Dict = {}
    schedule: List[Dict] = []

# Role-based permission checker
def filter_data_by_role(data: Dict, role: Role) -> Dict:
    """Filter data based on user role."""
    filtered_data = {
        "family_members": [],
        "activities": [],
        "meal_plan": {},
        "shopping_list": {},
        "schedule": []
    }

    if role == Role.PARENT:
        # Parent sees all data
        filtered_data.update(data)
    elif role == Role.COOK:
        # Cook sees only meal plan and shopping list
        filtered_data["meal_plan"] = data["meal_plan"]
        filtered_data["shopping_list"] = data["shopping_list"]
    elif role == Role.DRIVER:
        # Driver sees only activities/schedule where driver_required is True
        filtered_data["activities"] = [a for a in data["activities"] if a.get("driver_required", False)]
        filtered_data["schedule"] = [s for s in data["schedule"] if s.get("driver_required", False)]

    return filtered_data

# Helper functions
def generate_schedule(activities: List[Dict], role: Role = Role.PARENT) -> List[Dict]:
    """Generate a reminder schedule from activities, filtered by role."""
    schedule = []
    for activity in activities:
        if role == Role.DRIVER and not activity.get("driver_required", False):
            continue
        days = activity.get("days", [])
        for day in days:
            schedule.append({
                "day": day,
                "activity": activity["name"],
                "time": activity["time"],
                "location": activity["location"],
                "caregiver": activity["caregiver"],
                "driver_required": activity.get("driver_required", False),
                "date": activity.get("date")
            })
    return sorted(schedule, key=lambda x: (x["day"], x["time"]))

def create_meal_plan_table(meal_plan: Dict) -> List[Dict]:
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meal_table = []
    for day in days:
        meals = meal_plan.get(day, [])
        breakfast = meals[0][0] if len(meals) > 0 and len(meals[0]) > 0 else "No meal planned"
        lunch = meals[1][0] if len(meals) > 1 and len(meals[1]) > 0 else "No meal planned"
        dinner = meals[2][0] if len(meals) > 2 and len(meals[2]) > 0 else "No meal planned"
        meal_table.append({
            "Day": day.capitalize(),
            "Breakfast": breakfast,
            "Lunch": lunch,
            "Dinner": dinner
        })
    return meal_table

def get_meal_plan_details(meal_plan: Dict) -> Dict:
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    details = {}
    for day in days:
        meals = meal_plan.get(day, [])
        if meals:
            day_details = []
            for i, meal in enumerate(meals):
                meal_type = ["Breakfast", "Lunch", "Dinner"][i] if i < 3 else f"Meal {i+1}"
                day_details.append({
                    "meal_type": meal_type,
                    "name": meal[0],
                    "ingredients": meal[1] if len(meal) > 1 else "None"
                })
            details[day.capitalize()] = day_details
    return details

@app.post("/family_member")
async def add_family_member(member: FamilyMemberRequest, role: Role = Query(..., description="User role")):
    """Add a new family member (Parent only)."""
    if role != Role.PARENT:
        raise HTTPException(status_code=403, detail="Only Parent role can add family members")
    save_family_member(member.name)
    return {"message": f"Added {member.name} to family members", "name": member.name}

@app.post("/Child_activity")
async def add_activity(activity: ActivityRequest, role: Role = Query(..., description="User role")):
    """Add a new activity (Parent only)."""
    if role != Role.PARENT:
        raise HTTPException(status_code=403, detail="Only Parent role can add activities")
    new_activity = {
        "name": activity.name,
        "time": activity.time,
        "days": activity.days,
        "location": activity.location,
        "caregiver": activity.caregiver,
        "repetition": activity.repetition,
        "driver_required": activity.driver_required,
        "date": activity.date
    }
    save_activity(new_activity)
    # Reload latest data to include the newly added activity
    data = load_latest_data()
    activities = data["activities"]
    # Generate schedule for all roles to ensure driver sees the activity
    schedule = generate_schedule(activities, Role.PARENT)  # Use PARENT role to include all activities
    save_schedule(schedule)
    return {"message": "Activity added", "activity": new_activity}

@app.delete("/activity/{activity_name}")
async def delete_activity_endpoint(activity_name: str, role: Role = Query(..., description="User role")):
    """Delete an activity by name (Parent only)."""
    if role != Role.PARENT:
        raise HTTPException(status_code=403, detail="Only Parent role can delete activities")
    activities = load_latest_data()["activities"]
    if not any(activity["name"] == activity_name for activity in activities):
        raise HTTPException(status_code=404, detail="Activity not found")
    delete_activity(activity_name)
    # Update schedule after deletion
    remaining_activities = [a for a in activities if a["name"] != activity_name]
    schedule = generate_schedule(remaining_activities, role)
    save_schedule(schedule)
    return {"message": f"Activity '{activity_name}' deleted"}

@app.post("/meal_plan")
async def generate_meal_plan(meal_plan: MealPlanRequest, role: Role = Query(..., description="User role")):
    """Generate a meal plan (Parent only)."""
    if role != Role.PARENT:
        raise HTTPException(status_code=403, detail="Only Parent role can generate meal plans")
    tool_calls = weekly_meal_planner(meal_plan.preferences)
    meal_plan_data = tool_calls[0]["args"]
    shopping_list = shopping_list_generator(meal_plan_data)
    save_meal_plan(meal_plan_data)
    save_shopping_list(shopping_list)
    return {
        "message": "Meal plan generated",
        "meal_plan": meal_plan_data,
        "shopping_list": shopping_list
    }

@app.get("/shopping_list_items")
async def get_shopping_list_items(role: Role = Query(..., description="User role")):
    """Get shopping list as a flat list of items (Parent, Cook)."""
    if role not in [Role.PARENT, Role.COOK]:
        raise HTTPException(status_code=403, detail="Access denied for this role")
    shopping_list = load_latest_data()["shopping_list"]
    if not shopping_list:
        raise HTTPException(status_code=404, detail="No shopping list found")
    items = [item for section, items_list in shopping_list.items() for item in items_list]
    return {"shopping_list_items": items}

@app.get("/driver_schedule")
async def get_driver_schedule(role: Role = Query(..., description="User role")):
    """Get schedule for driver activities (Driver, Parent)."""
    if role not in [Role.DRIVER, Role.PARENT]:
        raise HTTPException(status_code=403, detail="Access denied for this role")
    data = load_latest_data()
    driver_activities = [a for a in data["activities"] if a.get("driver_required", False)]
    if not driver_activities:
        return {"message": "No driver-required activities found", "schedule": []}
    schedule = generate_schedule(driver_activities, role)
    return {"message": "Driver schedule retrieved", "schedule": schedule}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)