import os
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta

def child_activity_planner(
    activities: List[Dict[str, str | List[str] | str]],
    current_date: Optional[str] = None
) -> Dict:
    """Generate a weekly calendar view and reminders for child activities."""
    # Default to current date (June 9, 2025) if not provided
    if current_date:
        try:
            current_dt = datetime.strptime(current_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid current_date format, use YYYY-MM-DD")
    else:
        current_dt = datetime(2025, 6, 9)  # Default to June 9, 2025

    # Define days of the week
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    # Initialize calendar and reminders
    calendar = {day: [] for day in days_of_week}
    reminders = []
    
    # Get start of the current week (Monday)
    start_of_week = current_dt - timedelta(days=current_dt.weekday())
    
    for activity in activities:
        # Validate inputs
        required_keys = {"name", "time", "days", "location", "repetition", "caregiver"}
        if not all(key in activity for key in required_keys):
            raise ValueError(f"Activity missing required fields: {required_keys}")
        
        name = activity["name"]
        time = activity["time"]
        days = activity["days"] if isinstance(activity["days"], list) else [activity["days"]]
        location = activity["location"]
        repetition = activity["repetition"].lower()
        caregiver = activity["caregiver"]
        
        # Validate time format (HH:MM)
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            raise ValueError(f"Invalid time format for activity '{name}', use HH:MM")
        
        # Validate days
        for day in days:
            if day not in days_of_week:
                raise ValueError(f"Invalid day '{day}' in activity '{name}', use {days_of_week}")
        
        # Validate repetition
        if repetition not in ["weekly", "monthly", "one-time"]:
            raise ValueError(f"Invalid repetition '{repetition}' in activity '{name}', use weekly/monthly/one-time")
        
        # Add activity to calendar
        for day in days:
            activity_details = {
                "name": name,
                "time": time,
                "location": location,
                "caregiver": caregiver,
                "repetition": repetition
            }
            calendar[day].append(activity_details)
        
        # Generate reminders for the current week
        if repetition in ["weekly", "one-time"]:
            for day in days:
                # Calculate the date for this activity in the current week
                day_index = days_of_week.index(day)
                activity_date = start_of_week + timedelta(days=day_index)
                
                # For one-time events, only include if the date matches current_date
                if repetition == "one-time" and activity_date.date() != current_dt.date():
                    continue
                
                reminder = {
                    "date": activity_date.strftime("%Y-%m-%d"),
                    "day": day,
                    "time": time,
                    "name": name,
                    "location": location,
                    "caregiver": caregiver,
                    "message": f"Reminder: {name} on {day}, {activity_date.strftime('%Y-%m-%d')} at {time} at {location} (Caregiver: {caregiver})"
                }
                reminders.append(reminder)
        elif repetition == "monthly":
            # For monthly, include if the day of the month matches or is within the current week
            day_index = days_of_week.index(days[0])  # Assume single day for monthly
            activity_date = start_of_week + timedelta(days=day_index)
            if activity_date.day == current_dt.day:
                reminder = {
                    "date": activity_date.strftime("%Y-%m-%d"),
                    "day": days[0],
                    "time": time,
                    "name": name,
                    "location": location,
                    "caregiver": caregiver,
                    "message": f"Reminder: {name} on {days[0]}, {activity_date.strftime('%Y-%m-%d')} at {time} at {location} (Caregiver: {caregiver})"
                }
                reminders.append(reminder)
    
    # Sort activities by time within each day
    for day in calendar:
        calendar[day].sort(key=lambda x: x["time"])
    
    # Sort reminders by date and time
    reminders.sort(key=lambda x: (x["date"], x["time"]))
    
    # Return combined output
    return {
        "calendar": calendar,
        "reminders": reminders
    }

def main():
        # Example activities
        activities = [
            {
                "name": "Soccer Practice",
                "time": "15:00",
                "days": ["Monday", "Wednesday"],
                "location": "Community Field",
                "repetition": "weekly",
                "caregiver": "Alice"
            },
            {
                "name": "Piano Lesson",
                "time": "16:30",
                "days": "Tuesday",
                "location": "Music School",
                "repetition": "weekly",
                "caregiver": "Bob"
            },
            {
                "name": "Art Class",
                "time": "10:00",
                "days": "Saturday",
                "location": "Art Studio",
                "repetition": "monthly",
                "caregiver": "Alice"
            }
        ]
        
        # Generate calendar and reminders
        result = child_activity_planner(activities, current_date="2025-06-09")
        print(result)
        
        # Create artifact for output
        
if __name__ == "__main__":
    main()