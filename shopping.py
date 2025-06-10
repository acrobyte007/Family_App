import os
from dotenv import load_dotenv
from typing import Dict, List
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Initialize the LLM
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="mixtral-8x7b-32768",
    temperature=0.5
)

def shopping_list_generator(meal_plan: Dict[str, List[List[str]]]) -> Dict[str, List[str]]:
    """
    Generate a shopping list from a weekly meal plan by calling the LLM.
    
    Args:
        meal_plan: Dictionary with day keys and lists of [dish, ingredients] pairs.
    
    Returns:
        Dictionary with store sections as keys and lists of ingredients as values.
    """
    # Extract all ingredients from the meal plan
    all_ingredients = []
    for day, meals in meal_plan.items():
        for meal in meals:
            if len(meal) > 1:  # Ensure ingredients exist
                ingredients = meal[1].split(", ")
                all_ingredients.extend(ingredients)

    # Remove duplicates while preserving order
    unique_ingredients = list(dict.fromkeys(all_ingredients))

    # Create prompt for LLM to categorize ingredients
    prompt_template = ChatPromptTemplate.from_template("""
        You are a meal planning assistant. Given a list of ingredients, categorize them into grocery store sections: 
        Produce, Dairy, Pantry, Bakery, and Other. Return a JSON object with these sections as keys and lists of 
        ingredients as values. If an ingredient doesn't clearly fit a section, place it in 'Other'. Use the provided 
        ingredient names exactly as given.

        Ingredients: {ingredients}

        Example output:
        ```json
        {
            "Produce": ["banana", "spinach"],
            "Dairy": ["ricotta cheese", "mozzarella cheese"],
            "Pantry": ["olive oil", "spaghetti"],
            "Bakery": ["whole wheat bread", "baguette"],
            "Other": ["hummus", "Italian seasoning"]
        }
        ```

        Output only the JSON object.
    """)

    # Call the LLM with the ingredients
    try:
        prompt = prompt_template.format_messages(ingredients=", ".join(unique_ingredients))
        response = llm.invoke(prompt)
        # Parse the JSON response
        shopping_list = response.content
        if isinstance(shopping_list, str):
            import json
            shopping_list = json.loads(shopping_list)
        return shopping_list
    except Exception as e:
        # Fallback: Return uncategorized list if LLM fails
        return {
            "Produce": [],
            "Dairy": [],
            "Pantry": [],
            "Bakery": [],
            "Other": unique_ingredients
        }

if __name__ == "__main__":
    # Example meal plan for testing
    sample_meal_plan = {
        "monday": [
            ["Breakfast: Italian Omelette", "eggs, bell peppers, onions, mushrooms, Italian seasoning"],
            ["Lunch: Vegetarian Lasagna", "lasagna noodles, ricotta cheese, marinara sauce, spinach, mushrooms"],
            ["Dinner: Spaghetti Aglio e Olio", "spaghetti, garlic, olive oil, red pepper flakes, parsley"]
        ],
        "friday": [
            ["Breakfast: Smoothie Bowl", "banana, spinach, almond milk, almond butter, granola"],
            ["Lunch: Vegetarian Stuffed Shells", "jumbo shells, ricotta cheese, marinara sauce, spinach, mushrooms"],
            ["Dinner: Spaghetti Carbonara", "spaghetti, eggs, parmesan cheese, black pepper, Italian seasoning"]
        ]
    }
    
    shopping_list = shopping_list_generator(sample_meal_plan)
    print(shopping_list)