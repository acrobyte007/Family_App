from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime, timezone

# Initialize SQLAlchemy
Base = declarative_base()
engine = create_engine('sqlite:///family_planner.db', echo=False)
Session = sessionmaker(bind=engine)

# Define database models
class FamilyMember(Base):
    __tablename__ = 'family_members'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    time = Column(String, nullable=False)
    days = Column(String, nullable=False)  # Store as JSON string
    location = Column(String, nullable=False)
    caregiver = Column(String, nullable=False)
    repetition = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class MealPlan(Base):
    __tablename__ = 'meal_plans'
    id = Column(Integer, primary_key=True)
    data = Column(Text, nullable=False)  # Store as JSON string
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ShoppingList(Base):
    __tablename__ = 'shopping_lists'
    id = Column(Integer, primary_key=True)
    data = Column(Text, nullable=False)  # Store as JSON string
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    data = Column(Text, nullable=False)  # Store as JSON string
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Create tables
Base.metadata.create_all(engine)

def load_latest_data():
    """Load the latest data from the database."""
    session = Session()
    try:
        # Load latest family members
        family_members = session.query(FamilyMember).order_by(FamilyMember.timestamp.desc()).all()
        family_members_data = [fm.name for fm in family_members] if family_members else []

        # Load latest activities
        activities = session.query(Activity).order_by(Activity.timestamp.desc()).all()
        activities_data = [
            {
                "name": a.name,
                "time": a.time,
                "days": json.loads(a.days),
                "location": a.location,
                "caregiver": a.caregiver,
                "repetition": a.repetition
            } for a in activities
        ] if activities else []

        # Load latest meal plan
        meal_plan = session.query(MealPlan).order_by(MealPlan.timestamp.desc()).first()
        meal_plan_data = json.loads(meal_plan.data) if meal_plan else {}

        # Load latest shopping list
        shopping_list = session.query(ShoppingList).order_by(ShoppingList.timestamp.desc()).first()
        shopping_list_data = json.loads(shopping_list.data) if shopping_list else {}

        # Load latest schedule
        schedule = session.query(Schedule).order_by(Schedule.timestamp.desc()).first()
        schedule_data = json.loads(schedule.data) if schedule else []

        return {
            "family_members": family_members_data,
            "activities": activities_data,
            "meal_plan": meal_plan_data,
            "shopping_list": shopping_list_data,
            "schedule": schedule_data
        }
    finally:
        session.close()

def get_timestamps(table):
    """Get list of timestamps for a given table."""
    session = Session()
    try:
        timestamps = session.query(table.timestamp).distinct().order_by(table.timestamp.desc()).all()
        return [ts[0].strftime("%Y-%m-%d %H:%M:%S") for ts in timestamps]
    finally:
        session.close()

def load_data_by_timestamp(table, timestamp, key):
    """Load data from a table for a specific timestamp."""
    session = Session()
    try:
        data = session.query(table).filter(table.timestamp == datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")).all()
        if data:
            if table == FamilyMember:
                return [d.name for d in data]
            elif table == Activity:
                return [
                    {
                        "name": a.name,
                        "time": a.time,
                        "days": json.loads(a.days),
                        "location": a.location,
                        "caregiver": a.caregiver,
                        "repetition": a.repetition
                    } for a in data
                ]
            elif table in [MealPlan, ShoppingList, Schedule]:
                return json.loads(data[0].data)
        return None
    finally:
        session.close()

def save_family_member(name):
    """Save a family member to the database."""
    session = Session()
    try:
        new_member = FamilyMember(name=name)
        session.add(new_member)
        session.commit()
    finally:
        session.close()

def save_activity(activity):
    """Save an activity to the database."""
    session = Session()
    try:
        db_activity = Activity(
            name=activity["name"],
            time=activity["time"],
            days=json.dumps(activity["days"]),
            location=activity["location"],
            caregiver=activity["caregiver"],
            repetition=activity["repetition"]
        )
        session.add(db_activity)
        session.commit()
    finally:
        session.close()

def update_activity(old_name, new_activity):
    """Update an activity in the database."""
    session = Session()
    try:
        session.query(Activity).filter(Activity.name == old_name).delete()
        session.add(Activity(
            name=new_activity["name"],
            time=new_activity["time"],
            days=json.dumps(new_activity["days"]),
            location=new_activity["location"],
            caregiver=new_activity["caregiver"],
            repetition=new_activity["repetition"]
        ))
        session.commit()
    finally:
        session.close()

def delete_activity(name):
    """Delete an activity from the database."""
    session = Session()
    try:
        session.query(Activity).filter(Activity.name == name).delete()
        session.commit()
    finally:
        session.close()

def save_meal_plan(meal_plan):
    """Save a meal plan to the database."""
    session = Session()
    try:
        session.add(MealPlan(data=json.dumps(meal_plan)))
        session.commit()
    finally:
        session.close()

def save_shopping_list(shopping_list):
    """Save a shopping list to the database."""
    session = Session()
    try:
        session.add(ShoppingList(data=json.dumps(shopping_list)))
        session.commit()
    finally:
        session.close()

def save_schedule(schedule):
    """Save a schedule to the database."""
    session = Session()
    try:
        session.add(Schedule(data=json.dumps(schedule)))
        session.commit()
    finally:
        session.close()