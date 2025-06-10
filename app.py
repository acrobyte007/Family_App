from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from meal_plane import weekly_meal_planner
from shopping import shopping_list_generator
from db import (
    load_latest_data, get_timestamps, load_data_by_timestamp,
    save_family_member, save_activity, update_activity, delete_activity,
    save_meal_plan, save_shopping_list, save_schedule,
)

app = FastAPI(title="Family Planner API")

# Pydantic models for request/response validation
class FamilyMemberRequest(BaseModel):
    name: str

class ActivityRequest(BaseModel):
    name: str
    time: str  # Format: HH:MM
    days: List[str]
    location: str
    caregiver: str
    repetition: str

class ActivityUpdateRequest(BaseModel):
    name: str
    time: str
    days: List[str]
    location: str
    caregiver: str
    repetition: str

class MealPlanRequest(BaseModel):
    preferences: str

class StateResponse(BaseModel):
    family_members: List[str]
    activities: List[Dict]
    meal_plan: Dict
    shopping_list: Dict
    schedule: List[Dict]

# Helper functions (same as Streamlit app)
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

def create_meal_plan_table(meal_plan: Dict) -> List[Dict]:
    """Create a day-wise table for meals with Breakfast, Lunch, and Dinner columns."""
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
    """Return meal plan details with ingredients."""
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

# API Endpoints
@app.get("/state", response_model=StateResponse)
async def get_state():
    """Get the current state of family members, activities, meal plan, shopping list, and schedule."""
    data = load_latest_data()
    return {
        "family_members": data["family_members"],
        "activities": data["activities"],
        "meal_plan": data["meal_plan"],
        "shopping_list": data["shopping_list"],
        "schedule": data["schedule"]
    }

@app.get("/timestamps/{entity}")
async def get_entity_timestamps(entity: str):
    """Get timestamps for a specific entity."""
    valid_entities = ["FamilyMember", "Activity", "MealPlan", "ShoppingList", "Schedule"]
    if entity not in valid_entities:
        raise HTTPException(status_code=400, detail="Invalid entity")
    timestamps = get_timestamps(globals()[entity])
    return {"timestamps": ["Latest"] + timestamps}

@app.get("/data/{entity}/{timestamp}")
async def get_data_by_timestamp(entity: str, timestamp: str):
    """Get data for a specific entity and timestamp."""
    valid_entities = {
        "FamilyMember": "family_members",
        "Activity": "activities",
        "MealPlan": "meal_plan",
        "ShoppingList": "shopping_list",
        "Schedule": "schedule"
    }
    if entity not in valid_entities:
        raise HTTPException(status_code=400, detail="Invalid entity")
    if timestamp == "Latest":
        data = load_latest_data()
        return {valid_entities[entity]: data[valid_entities[entity]]}
    data = load_data_by_timestamp(globals()[entity], timestamp, valid_entities[entity])
    if data is None:
        raise HTTPException(status_code=404, detail="Data not found")
    return {valid_entities[entity]: data}

@app.post("/family_member")
async def add_family_member(member: FamilyMemberRequest):
    """Add a new family member."""
    save_family_member(member.name)
    return {"message": f"Added {member.name} to family members", "name": member.name}

@app.post("/activity")
async def add_activity(activity: ActivityRequest):
    """Add a new activity."""
    new_activity = {
        "name": activity.name,
        "time": activity.time,
        "days": activity.days,
        "location": activity.location,
        "caregiver": activity.caregiver,
        "repetition": activity.repetition
    }
    save_activity(new_activity)
    activities = load_latest_data()["activities"] + [new_activity]
    schedule = generate_schedule(activities)
    save_schedule(schedule)
    return {"message": "Activity added", "activity": new_activity}

@app.put("/activity/{activity_name}")
async def edit_activity(activity_name: str, activity: ActivityUpdateRequest):
    """Edit an existing activity."""
    new_activity = {
        "name": activity.name,
        "time": activity.time,
        "days": activity.days,
        "location": activity.location,
        "caregiver": activity.caregiver,
        "repetition": activity.repetition
    }
    update_activity(activity_name, new_activity)
    activities = [a if a["name"] != activity_name else new_activity for a in load_latest_data()["activities"]]
    schedule = generate_schedule(activities)
    save_schedule(schedule)
    return {"message": "Activity updated", "activity": new_activity}

@app.delete("/activity/{activity_name}")
async def delete_activity_endpoint(activity_name: str):
    """Delete an activity."""
    delete_activity(activity_name)
    activities = [a for a in load_latest_data()["activities"] if a["name"] != activity_name]
    schedule = generate_schedule(activities)
    save_schedule(schedule)
    return {"message": "Activity deleted"}

@app.post("/meal_plan")
async def generate_meal_plan(meal_plan: MealPlanRequest):
    """Generate a meal plan based on preferences."""
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

@app.get("/meal_plan_table")
async def get_meal_plan_table():
    """Get the meal plan as a day-wise table."""
    meal_plan = load_latest_data()["meal_plan"]
    if not meal_plan:
        raise HTTPException(status_code=404, detail="No meal plan found")
    meal_table = create_meal_plan_table(meal_plan)
    return {"meal_plan_table": meal_table}

@app.get("/meal_plan_details")
async def get_meal_plan_details_endpoint():
    """Get meal plan details with ingredients."""
    meal_plan = load_latest_data()["meal_plan"]
    if not meal_plan:
        raise HTTPException(status_code=404, detail="No meal plan found")
    details = get_meal_plan_details(meal_plan)
    return {"meal_plan_details": details}

@app.get("/shopping_list_items")
async def get_shopping_list_items():
    """Get shopping list as a flat list of items."""
    shopping_list = load_latest_data()["shopping_list"]
    if not shopping_list:
        raise HTTPException(status_code=404, detail="No shopping list found")
    items = [item for section, items_list in shopping_list.items() for item in items_list]
    return {"shopping_list_items": items}

@app.get("/driver_schedule")
async def get_driver_schedule():
    """Get the schedule filtered for Driver."""
    schedule = load_latest_data()["schedule"]
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found")
    driver_schedule = [s for s in schedule if s["caregiver"] == "Driver"]
    if not driver_schedule:
        return {"driver_schedule": [], "message": "No activities assigned to Driver"}
    return {"driver_schedule": driver_schedule}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)