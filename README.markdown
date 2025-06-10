# Family Planner

## Overview
Family Planner is a web application designed to help families manage their schedules, meal plans, and shopping lists. It features a role-based system with three user roles: **Parent**, **Cook**, and **Driver**, each with specific permissions. The application uses a **FastAPI** backend for API services, a **SQLite** database for data storage, and a **Streamlit** frontend for a user-friendly interface. Supporting logic for activities, meal planning, and shopping lists is handled by dedicated modules.

### Features
- **Role-Based Access**:
  - **Parent**: Add/delete family members, add/delete child activities, generate meal plans, view shopping lists, and driver schedules.
  - **Cook**: View meal plans and shopping lists.
  - **Driver**: View driver-required activity schedules.
- **Activity Management**: Schedule child activities with details like time, days, location, caregiver, and driver requirements.
- **Meal Planning**: Generate weekly meal plans based on preferences (e.g., vegetarian) and view them in a table format.
- **Shopping List**: Automatically generate shopping lists from meal plans.
- **Driver Schedule**: Display activities requiring a driver in a clear schedule format.
- **Database Integration**: Persistent storage using SQLite for family members, activities, meal plans, shopping lists, and schedules.

## Project Structure
```
Family_App/
├── activity.py       # Logic for activity management
├── back_end.py       # FastAPI backend with API endpoints
├── db.py             # SQLite database setup and functions
├── app.py            # Streamlit frontend for the UI
├── meal_plane.py     # Logic for generating weekly meal plans
├── shopping.py       # Logic for generating shopping lists
├── family_planner.db # SQLite database file (generated)
├── venv/             # Virtual environment
└── README.md         # Project documentation
```

## Requirements
- Python 3.12+
- Dependencies (install via `requirements.txt`):
  ```
  fastapi
  uvicorn
  sqlalchemy
  streamlit
  requests
  pandas
  ```

## Setup Instructions
1. **Clone the Repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd Family_App
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install fastapi uvicorn sqlalchemy streamlit requests pandas
   ```

4. **Initialize the Database**:
   - Run `db.py` to create the SQLite database (`family_planner.db`):
     ```bash
     python db.py
     ```
   - **Note**: This will drop and recreate tables, deleting existing data. For production, use a migration tool like Alembic to preserve data.

5. **Start the FastAPI Backend**:
   - Ensure `activity.py`, `meal_plane.py`, and `shopping.py` are in the project directory, as they are imported by `back_end.py`.
   - Start the server:
     ```bash
     uvicorn back_end:app --host 0.0.0.0 --port 8000
     ```

6. **Start the Streamlit Frontend**:
   - In a separate terminal, activate the virtual environment and run:
     ```bash
     streamlit run app.py
     ```
   - Open the browser at `http://localhost:8501`.

## Usage
1. **Access the Application**:
   - Open `http://localhost:8501` in your browser to access the Streamlit UI.
   - Select a role (`Parent`, `Cook`, or `Driver`) from the dropdown.

2. **Parent Role**:
   - **Add Family Member**: Enter a name and submit to add a family member.
   - **Add Child Activity**: Fill in activity details (name, time, days, location, caregiver, repetition, driver required, date) and submit.
   - **Delete Activity**: Select an activity from the dropdown and delete it.
   - **Generate Meal Plan**: Enter preferences (e.g., "vegetarian") and generate a weekly meal plan, displayed as a table.
   - **View Shopping List**: See the shopping list generated from the meal plan.
   - **View Driver Schedule**: View all activities, including those requiring a driver.

3. **Cook Role**:
   - **View Meal Plan**: Display the weekly meal plan in a table format (Day, Breakfast, Lunch, Dinner).
   - **View Shopping List**: See the shopping list items.

4. **Driver Role**:
   - **View Driver Schedule**: Display activities with `driver_required=True` in a schedule format.

## API Endpoints
The FastAPI backend (`back_end.py`) provides the following endpoints (accessible at `http://localhost:8000`):
- `POST /family_member`: Add a family member (Parent only).
- `POST /Child_activity`: Add a child activity (Parent only).
- `DELETE /activity/{activity_name}`: Delete an activity (Parent only).
- `POST /meal_plan`: Generate a meal plan and shopping list (Parent only).
- `GET /meal_plan`: Fetch the latest meal plan (Parent, Cook).
- `GET /shopping_list_items`: Get shopping list items (Parent, Cook).
- `GET /driver_schedule`: Get the driver schedule (Parent, Driver).

## Supporting Modules
- **activity.py**: Contains logic for managing activities, such as scheduling and validation (referenced in `back_end.py`).
- **meal_plane.py**: Implements the `weekly_meal_planner` function to generate meal plans based on user preferences.
- **shopping.py**: Implements the `shopping_list_generator` function to create shopping lists from meal plans.

## Database Schema
The SQLite database (`family_planner.db`, defined in `db.py`) includes:
- `family_members`: Stores family member names.
- `activities`: Stores activity details (name, time, days, location, caregiver, repetition, driver_required, date).
- `meal_plans`: Stores weekly meal plans as JSON.
- `shopping_lists`: Stores shopping lists as JSON.
- `schedules`: Stores activity schedules as JSON.

## Troubleshooting
- **404 Errors**: Ensure the FastAPI server is running (`uvicorn back_end:app --host 0.0.0.0 --port 8000`) and all endpoints are defined in `back_end.py`.
- **Missing Activities/Meal Plans**: Add activities or generate a meal plan via the Parent role to populate the database.
- **Module Not Found**: Ensure `activity.py`, `meal_plane.py`, and `shopping.py` are in the project directory and contain the required functions (`weekly_meal_planner`, `shopping_list_generator`).
- **Database Issues**: If the schema is outdated, recreate tables by running `db.py` (warning: deletes data).
- **Streamlit Warnings**: Ensure Streamlit is updated (`pip install --upgrade streamlit`).
- **SQLAlchemy Warning**: The `declarative_base` warning in `db.py` can be fixed by updating:
  ```python
  from sqlalchemy.orm import declarative_base
  Base = declarative_base()
  ```

## Future Improvements
- Add user authentication for secure role-based access.
- Implement a dedicated `/activities` GET endpoint to list activities directly.
- Use Alembic for database migrations to avoid data loss.
- Enhance the UI with interactive tables (e.g., `st.dataframe`) and custom styling.
- Add endpoint to update existing activities.
- Document `activity.py`, `meal_plane.py`, and `shopping.py` for clarity on their functionality.
