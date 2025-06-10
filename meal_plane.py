import os
import re
from typing import List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from typing_extensions import Annotated, TypedDict

# Load environment variables
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

# Validate API key
if not groq_api_key:
    raise ValueError("GROQ_API_KEY is not set in environment variables")

# Initialize Groq model
groq_model = ChatGroq(
    model_name="llama3-8b-8192",
    groq_api_key=groq_api_key,
    max_retries=2
)

# Define WeeklyMealPlan as a TypedDict for tool usage
class WeeklyMealPlan(TypedDict):
    """Weekly meal plan with meals for each day of the week."""
    monday: Annotated[List[List[str]], ..., "List of meals (breakfast, lunch, dinner) for Monday, each meal is a list of dish name and ingredients"]
    tuesday: Annotated[List[List[str]], ..., "List of meals for Tuesday"]
    wednesday: Annotated[List[List[str]], ..., "List of meals for Wednesday"]
    thursday: Annotated[List[List[str]], ..., "List of meals for Thursday"]
    friday: Annotated[List[List[str]], ..., "List of meals for Friday"]
    saturday: Annotated[List[List[str]], ..., "List of meals for Saturday"]
    sunday: Annotated[List[List[str]], ..., "List of meals for Sunday"]

# Bind the WeeklyMealPlan tool to the Groq model
llm_with_tools = groq_model.bind_tools([WeeklyMealPlan])

def weekly_meal_planner(query: str) -> List[dict]:
    """Generate a weekly meal plan based on a user query, returning tool_calls output."""
    # Create prompt to guide the LLM
    prompt = ChatPromptTemplate.from_template(
        """You are a nutritionist and dietitian. Based on the following user query, create a structured weekly meal plan using the WeeklyMealPlan tool. The plan should have meals for each day (monday to sunday), with three meals per day (breakfast, lunch, dinner). Each meal is a list of strings: the first string is the dish name, followed by its ingredients. Ensure the meals align with the cuisine, diet restrictions, and preferences mentioned in the query. Use lowercase day names.
        
        Query: {query}"""
    )
    
    chain = prompt | llm_with_tools
    result = chain.invoke({"query": query})
    
    # Check for tool calls
    if hasattr(result, "tool_calls") and result.tool_calls:
        # Ensure all days are present in the tool call args
        for tool_call in result.tool_calls:
            if tool_call["name"] == "WeeklyMealPlan":
                meal_plan = tool_call["args"]
                for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
                    if day not in meal_plan:
                        meal_plan[day] = []
                    elif not isinstance(meal_plan[day], list):
                        meal_plan[day] = []
        return result.tool_calls
    
    # Fallback: parse query as text if tool call fails
    fallback_plan = parse_text_fallback(query)
    # Simulate a tool call structure
    return [{
        "name": "WeeklyMealPlan",
        "args": fallback_plan,
        "id": "fallback_call",
        "type": "tool_call"
    }]

def parse_text_fallback(query: str) -> WeeklyMealPlan:
    """Parse query text to create a fallback meal plan."""
    meal_plan = {
        "monday": [],
        "tuesday": [],
        "wednesday": [],
        "thursday": [],
        "friday": [],
        "saturday": [],
        "sunday": []
    }
    days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    meal_types = ["breakfast", "lunch", "dinner"]
    
    # Extract cuisine, diet restrictions, and preferences from query
    cuisine = "Italian"  # Default
    diet_restrictions = "vegetarian"  # Default
    preferences = "spicy"  # Default
    
    for word in query.lower().split():
        if word in ["italian", "mexican", "indian"]:
            cuisine = word
        if word in ["vegetarian", "gluten-free", "vegan", "vegetarian"]:
            diet_restrictions = word
        if word in ["spicy", "quick", "low-carb"]:
            preferences = word
    
    for day in days:
        day_meals = []
        for meal_type in meal_types:
            day_meals.append([f"{cuisine.capitalize()} {meal_type.capitalize()}", f"{cuisine} ingredients", diet_restrictions, preferences])
        meal_plan[day] = day_meals
    
    return meal_plan
import json
def main():
    try:
        # Example usage
        query = "Plan a week of Italian vegetarian spicy meals"
        tool_calls = weekly_meal_planner(query)
        print("Tool Calls:", json.dumps(tool_calls, indent=2))
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()