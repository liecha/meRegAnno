import streamlit as st
import pandas as pd
from datetime import datetime, time

# Import existing modules (keeping original imports)
from scripts.data_dashboard import datetime_to_string, time_to_string
from scripts.data_storage import fetch_data_from_storage, add_registration, save_data_to_storage
from scripts.constants import ACTIVITY_TYPES, get_activity_emoji

def simple_time_validation(selected_time):
    """Simple validation - only check if time is selected"""
    if selected_time is None:
        st.error("🕐 Please select a time before submitting")
        return False
    return True

def create_new_form_activity(bmr):
    # Define activity types and emojis locally to avoid import issues
    ACTIVITY_TYPES = ["Walk", "Run", "Bike", "Swim", "Strength", "Yoga"]
    
    def get_activity_emoji(activity_type):
        emojis = {
            "Walk": "🚶‍♀️",
            "Run": "🏃‍♀️", 
            "Bike": "🚴‍♀️",
            "Swim": "🏊‍♀️",
            "Strength": "💪",
            "Yoga": "🧘‍♀️"
        }
        return emojis.get(activity_type, "🏃‍♀️")

    # Check if we just submitted successfully - if so, use cleared values
    if "activity_just_submitted" in st.session_state and st.session_state.activity_just_submitted:
        # Clear the flag
        st.session_state.activity_just_submitted = False
        # Use None/empty values for widgets
        default_time = None
        default_activity = ""
    else:
        # Normal behavior - use session state values if they exist
        default_time = st.session_state.get('act_time', None)
        default_activity = st.session_state.get('activity_type_select', "")

    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input("Select a date", datetime.now().date(), key='act_date')
        st.success(f"Date: {selected_date}")
    
    with col2:
        selected_time = st.time_input("Select a time", value=default_time, key='act_time')
        if selected_time:
            st.success(f"Time: {selected_time}")
        else:
            st.error("Please select a time")
    
    activity_type = st.selectbox(
        "Choose activity", 
        [""] + ACTIVITY_TYPES,
        index=0 if default_activity == "" else ([""] + ACTIVITY_TYPES).index(default_activity) if default_activity in ACTIVITY_TYPES else 0,
        key="activity_type_select"
    )
    
    if not activity_type:
        st.info("Please select an activity type to continue")
        return
    
    with st.form(key="activity_form", clear_on_submit=True):
        st.subheader(f"{get_activity_emoji(activity_type)} Register {activity_type} Activity")
        
        if activity_type in ["Walk", "Run", "Bike"]:
            col1, col2 = st.columns(2)
            with col1:
                duration = st.text_input("Duration (hh:mm:ss)", value='00:00:00')
                distance = st.number_input(f"Distance ({'km' if activity_type != 'Swim' else 'meters'})", min_value=0.0, step=0.1)
                if activity_type != "Walk":
                    pace = st.number_input("Pace (min/km)", min_value=0.0, step=0.1)
                else:
                    pace = 0.0
            
            with col2:
                energy = st.number_input("Energy burned (kcal)", min_value=0, step=1)
                if activity_type in ["Walk", "Run"]:
                    steps = st.number_input("Steps", min_value=0, step=1)
                else:
                    steps = 0
        
        elif activity_type == "Swim":
            col1, col2 = st.columns(2)
            with col1:
                duration = st.text_input("Duration (hh:mm:ss)", value='00:00:00')
                distance = st.number_input("Distance (meters)", min_value=0.0, step=25.0)
                pace = st.number_input("Pace (min/100m)", min_value=0.0, step=0.1)
            
            with col2:
                energy = st.number_input("Energy burned (kcal)", min_value=0, step=1)
                steps = 0
        
        elif activity_type in ["Strength", "Yoga"]:
            col1, col2 = st.columns(2)
            with col1:
                duration = st.text_input("Duration (hh:mm:ss)", value='00:00:00')
                energy = st.number_input("Energy burned (kcal)", min_value=0, step=1)
            with col2:
                pass  # Empty column for layout
            distance = 0.0
            pace = 0.0
            steps = 0
        
        # Notes section
        note_placeholder = {
            "Walk": "Describe your walk: route, pace, how you felt, weather conditions...",
            "Run": "Describe your run: route, performance, splits, how you felt...",
            "Swim": "Pool details, strokes used, technique focus, how you felt...",
            "Bike": "Route details, terrain, bike type, weather conditions...",
            "Strength": "Exercises performed, weights used, sets/reps, muscle groups...",
            "Yoga": "Yoga style, poses practiced, meditation time, how you felt..."
        }.get(activity_type, "Activity details and notes...")
        
        note = st.text_area("Activity notes", placeholder=note_placeholder, height=100)
        
        # Submit button - ONLY TIME VALIDATION
        time_is_valid = selected_time is not None
        
        col1, col2 = st.columns([1, 3])
        with col1:
            submit_button = st.form_submit_button("Submit Activity", disabled=not time_is_valid)
        
        with col2:
            if not time_is_valid:
                st.error("Please select a time before submitting")
            else:
                st.success("Ready to submit activity")
        
        # Handle form submission
        if submit_button and time_is_valid:
            try:
                # Convert distance for swimming (meters to km)
                distance_km = distance / 1000.0 if activity_type == "Swim" else distance
                
                # Prepare activity data
                activity_registration = {
                    "date": selected_date,
                    "time": selected_time,
                    "label": 'TRAINING',
                    "energy": -1 * int(energy),
                    "pro": 0,
                    "carb": 0,
                    "fat": 0,
                    "activity": activity_type,
                    "distance": distance_km,
                    "duration": duration,
                    "pace": pace,
                    "steps": steps,
                    "note": str(note),
                }
                
                # Set flag to indicate successful submission
                st.session_state.activity_just_submitted = True
                
                # Save the registration (this will call st.rerun() internally)
                add_registration(activity_registration, bmr)
                
                st.success(f"✅ {activity_type} activity registered successfully!")
                st.balloons()
                
            except Exception as e:
                st.error("Failed to save activity. Please try again.")
                with st.expander("Error Details"):
                    st.code(str(e))

def create_new_form_food(code, options_string, bmr, df_meal_items=None):
    """
    Food registration form with clearing mechanism
    """
    # Check if we just submitted successfully - if so, use cleared values
    if "food_just_submitted" in st.session_state and st.session_state.food_just_submitted:
        # Clear the flag
        st.session_state.food_just_submitted = False
        # Use None for default time
        default_time = None
    else:
        # Normal behavior - use session state values if they exist
        default_time = st.session_state.get('food_time', None)
    
    # Date and time selection
    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input("Select a date", datetime.now().date(), key='food_date')
        st.success(f"Date: {selected_date}")
    
    with col2:
        selected_time = st.time_input("What time did you eat", value=default_time, key='food_time')
        if selected_time:
            st.success(f"Time: {selected_time}")
        else:
            st.error("Please select a time")
    
    # Meal registration form
    with st.form(key="food_registration_form", clear_on_submit=True):
        st.markdown("### Register Meal")
        
        # Nutrition code input
        meal_code = st.text_input(
            "Meal code (kcal/protein/carb/fat)", 
            value=code,
            help="Automatically calculated from meal composition",
            key="meal_code_input"
        )
        
        # Meal details
        meal_note = st.text_input(
            "Meal details", 
            value=options_string,
            help="Description of the meal contents",
            key="meal_note_input"
        )
        
        # Favorite meal option
        mark_favorite = st.checkbox(
            "Mark as favorite meal", 
            help="Save this meal to your favorites for easy access later"
        )
        
        # Show info about meal composition
        if df_meal_items is None:
            st.info("Create a meal composition on the left to register it")
        elif df_meal_items.empty:
            st.info("Add some ingredients to your meal")
        
        # Only validate time and require meal data
        time_is_valid = selected_time is not None
        form_is_valid = time_is_valid and df_meal_items is not None and not df_meal_items.empty
        
        # Submit button
        col1, col2 = st.columns([1, 3])
        with col1:
            submit_button = st.form_submit_button("Register Meal", disabled=not form_is_valid)
        
        with col2:
            if not time_is_valid:
                st.error("Please select a time")
            elif df_meal_items is None or df_meal_items.empty:
                st.error("Please create a meal composition first")
            else:
                st.success("Ready to register meal")
        
        # Handle form submission
        if submit_button and form_is_valid:
            try:
                # Parse nutrition code
                food_split = meal_code.split('/')
                if len(food_split) != 4:
                    raise ValueError("Invalid nutrition code format")
                
                # SAVE MEAL TO DATABASE FIRST
                if df_meal_items is not None and len(df_meal_items) > 0:
                    try:
                        # Prepare meal data for database
                        df_meal_to_save = df_meal_items.copy()
                        df_meal_to_save['date'] = datetime_to_string(selected_date)
                        df_meal_to_save['time'] = time_to_string(selected_time)
                        df_meal_to_save['favorite'] = mark_favorite
                        
                        # Load existing meal database
                        try:
                            df_meal_db = fetch_data_from_storage('data/meal_databas.csv')
                        except:
                            df_meal_db = pd.DataFrame(columns=[
                                'date', 'time', 'name', 'livsmedel', 'amount', 'code', 'favorite'
                            ])
                        
                        # Save to database
                        df_updated_meal_db = pd.concat([df_meal_db, df_meal_to_save], ignore_index=True)
                        save_data_to_storage(df_updated_meal_db, 'data/meal_databas.csv')
                        
                    except Exception as e:
                        st.warning(f"Could not save meal to database: {str(e)}")
                
                # Register the meal in main energy tracking
                meal_registration_data = {
                    "date": selected_date,
                    "time": selected_time,
                    "label": 'FOOD',
                    "energy": int(food_split[0]),
                    "pro": int(food_split[1]),
                    "carb": int(food_split[2]),
                    "fat": int(food_split[3]),
                    "activity": 'Eat',
                    "distance": 0.0,
                    "note": str(meal_note),
                }
                
                # Set flag to indicate successful submission
                st.session_state.food_just_submitted = True
                
                # Clear meal creation state (only the current_meal_items, others handled by main page)
                if 'current_meal_items' in st.session_state:
                    st.session_state.current_meal_items = None
                
                # Set a flag for the main page to clear the meal creation widgets
                st.session_state.clear_meal_widgets = True
                
                add_registration(meal_registration_data, bmr)
                
                st.success("✅ Meal registered successfully!")
                st.balloons()
                
            except ValueError as e:
                st.error(f"Invalid input: {str(e)}")
            except Exception as e:
                st.error("Failed to register meal. Please try again.")
                with st.expander("Error Details"):
                    st.code(str(e))

def create_form_add_food_item_to_database():
    """
    Create form for adding new food items to database with clearing
    """
    # Check if we just submitted successfully
    if "food_item_just_submitted" in st.session_state and st.session_state.food_item_just_submitted:
        # Clear the flag
        st.session_state.food_item_just_submitted = False
        # Use cleared values
        default_food_name = ""
        default_calories = 0.0
        default_protein = 0.0
        default_carb = 0.0
        default_fat = 0.0
    else:
        # Use session state or defaults
        default_food_name = st.session_state.get('food_item_name', "")
        default_calories = st.session_state.get('food_item_calories', 0.0)
        default_protein = st.session_state.get('food_item_protein', 0.0)
        default_carb = st.session_state.get('food_item_carb', 0.0)
        default_fat = st.session_state.get('food_item_fat', 0.0)
    
    with st.form(key="food_item_form", clear_on_submit=True):
        st.markdown("### Add New Food Item")
        
        # Food item inputs
        food_name = st.text_input("Name of food item", value=default_food_name)
        
        col1, col2 = st.columns(2)
        with col1:
            calories = st.number_input("Energy (kcal / 100 g)", min_value=0.0, step=1.0, value=default_calories)
            protein = st.number_input("Proteins (g / 100 g)", min_value=0.0, step=0.1, value=default_protein)
        
        with col2:
            carb = st.number_input("Carbohydrates (g / 100 g)", min_value=0.0, step=0.1, value=default_carb)
            fat = st.number_input("Fats (g / 100 g)", min_value=0.0, step=0.1, value=default_fat)
        
        # Submit button
        submit_button = st.form_submit_button("Save Food Item")
        
        # Handle submission with validation AFTER click
        if submit_button:
            # Check if name is empty only when submitted
            if not food_name or food_name.strip() == "":
                st.error("Please enter a food name")
            else:
                try:
                    # Create new food item
                    new_food_item = {
                        'livsmedel': food_name.strip(),
                        'calorie': float(calories),
                        'protein': float(protein),
                        'carb': float(carb),
                        'fat': float(fat)
                    }
                    
                    # Load existing database
                    df_food_db = fetch_data_from_storage('data/livsmedelsdatabas.csv')
                    
                    # Check for duplicates
                    if food_name.strip().lower() in df_food_db['livsmedel'].str.lower().values:
                        st.warning(f"Food item '{food_name}' already exists in database")
                    else:
                        # Add new item
                        df_new_food_item = pd.DataFrame([new_food_item])
                        df_updated = pd.concat([df_food_db, df_new_food_item], ignore_index=True)
                        
                        # Save to storage
                        save_data_to_storage(df_updated, 'data/livsmedelsdatabas.csv')
                        
                        # Set flag for clearing form
                        st.session_state.food_item_just_submitted = True
                        
                        st.success(f"Food item '{food_name}' added successfully!")
                        st.rerun()
                        
                except Exception as e:
                    st.error("Failed to save food item. Please try again.")
                    with st.expander("Error Details"):
                        st.code(str(e))


def create_form_add_recipie_to_database(meal_df, code):
    """
    Create form for adding recipes to database with clearing
    """
    # Check if we just submitted successfully
    if "recipe_just_submitted" in st.session_state and st.session_state.recipe_just_submitted:
        # Clear the flag
        st.session_state.recipe_just_submitted = False
        # Use cleared values
        default_recipe_name = ""
        default_favorite = False
    else:
        # Use session state or defaults
        default_recipe_name = st.session_state.get('recipe_name', "")
        default_favorite = st.session_state.get('recipe_favorite', False)
    
    with st.form(key="recipe_form", clear_on_submit=True):
        st.markdown("### Save Recipe")
        
        # Recipe name input
        recipe_name = st.text_input("Name of recipe", value=default_recipe_name)
        
        # Display nutrition code (read-only)
        st.text_input(
            "Nutrition code (kcal/protein/carb/fat)",
            value=code,
            disabled=True,
            help="Automatically calculated from recipe ingredients"
        )
        
        # Favorite checkbox
        is_favorite = st.checkbox("Save recipe as favorite", value=default_favorite)
        
        # Submit button
        submit_button = st.form_submit_button("Save Recipe")
        
        # Handle submission with validation AFTER click
        if submit_button:
            # Simple validation - check recipe name and recipe data
            if not recipe_name or recipe_name.strip() == "":
                st.error("Please enter a recipe name")
            elif not hasattr(meal_df, 'empty') or meal_df.empty:
                st.error("No recipe composition data available")
            else:
                try:
                    # Load existing recipe database
                    df_recipe_db = fetch_data_from_storage('data/recipie_databas.csv')
                    
                    # Check for duplicate recipe names
                    if recipe_name.strip().lower() in df_recipe_db['name'].str.lower().values:
                        st.warning(f"Recipe '{recipe_name}' already exists. Choose a different name.")
                    else:
                        # Prepare recipe data
                        df_recipe_data = meal_df.copy()
                        df_recipe_data['name'] = recipe_name.strip()
                        df_recipe_data['code'] = code
                        df_recipe_data['favorite'] = is_favorite
                        
                        # Rename columns to match database schema
                        if 'Food' in df_recipe_data.columns:
                            df_recipe_data = df_recipe_data.rename(columns={
                                "Food": "livsmedel", 
                                "Amount (g)": "amount"
                            })
                        
                        # Ensure correct column order
                        df_recipe_data = df_recipe_data[['name', 'livsmedel', 'amount', 'code', 'favorite']]
                        
                        # Add to database
                        df_updated = pd.concat([df_recipe_db, df_recipe_data], ignore_index=True)
                        save_data_to_storage(df_updated, 'data/recipie_databas.csv')
                        
                        # Set flag for clearing form
                        st.session_state.recipe_just_submitted = True
                        
                        # Set flag for the main database page to clear the recipe composition widgets
                        st.session_state.clear_recipe_widgets = True
                        
                        favorite_text = " as favorite" if is_favorite else ""
                        st.success(f"Recipe '{recipe_name}' saved successfully{favorite_text}!")
                        st.info("Form has been cleared. You can create another recipe.")
                        st.rerun()
                        
                except Exception as e:
                    st.error("Failed to save recipe. Please try again.")
                    with st.expander("Error Details"):
                        st.code(str(e))

def create_copy_previous_meal_section():
    """Create a section for copying previous meals - ORIGINAL FUNCTIONALITY"""
    st.markdown("### Copy Previous Meal")
    
    # Initialize session state for modal - ORIGINAL
    if "show_meal_modal" not in st.session_state:
        st.session_state.show_meal_modal = False
    if "selected_previous_meal" not in st.session_state:
        st.session_state.selected_previous_meal = None
    if "copied_meal_items" not in st.session_state:
        st.session_state.copied_meal_items = []
    
    # Button to open meal selection modal - ORIGINAL
    if st.button("Browse previous meals", type="secondary", key="open_meal_modal"):
        st.session_state.show_meal_modal = True
    
    # Modal for meal selection - ORIGINAL
    if st.session_state.show_meal_modal:
        create_meal_selection_modal()
    
    # Display selected meal info if any - ORIGINAL
    if st.session_state.selected_previous_meal:
        meal_info = st.session_state.selected_previous_meal
        st.success(f"Selected: **{meal_info['name']}** from {meal_info['date']} at {meal_info['time']}")
        st.caption(f"Meal code: {meal_info['code']}")
        
        # Clear selection button - ORIGINAL
        if st.button("Clear selection", key="clear_meal_selection"):
            st.session_state.selected_previous_meal = None
            st.session_state.copied_meal_items = []
            st.rerun()

def create_meal_selection_modal():
    """Create a modal for selecting previous meals - ORIGINAL FUNCTIONALITY"""
    # Load meal database - ORIGINAL
    try:
        df_meal_db = fetch_data_from_storage('data/meal_databas.csv')
    except:
        st.error("No previous meals found in database")
        st.session_state.show_meal_modal = False
        return
    
    if df_meal_db.empty:
        st.error("No previous meals found")
        st.session_state.show_meal_modal = False
        return
    
    # ORIGINAL meal selection interface
    grouped_meals = df_meal_db.groupby(['name', 'date', 'time', 'code']).first().reset_index()
    grouped_meals = grouped_meals.sort_values(['date', 'time'], ascending=False)
    
    # Search functionality - ORIGINAL
    search_term = st.text_input("Search meals", help="Search by meal name")
    
    if search_term:
        filtered_meals = grouped_meals[
            grouped_meals['name'].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_meals = grouped_meals
    
    if filtered_meals.empty:
        st.warning("No meals found matching your search")
        return
    
    selected_meal = None
    st.caption(f"Found {len(filtered_meals)} meals")
    
    for idx, row in filtered_meals.iterrows():
        with st.expander(f"{row['name']} - {row['date']} at {row['time']}", expanded=False):
            # Show meal details - ORIGINAL
            meal_items = df_meal_db[
                (df_meal_db['name'] == row['name']) & 
                (df_meal_db['date'] == row['date']) & 
                (df_meal_db['time'] == row['time'])
            ]
            
            col_info1, col_info2 = st.columns(2)
            with col_info1:
                st.write(f"**Date:** {row['date']}")
                st.write(f"**Time:** {row['time']}")
                if row.get('favorite', False):
                    st.write("⭐ **Favorite meal**")
            
            with col_info2:
                st.write(f"**Nutrition code:** {row['code']}")
                code_parts = row['code'].split('/')
                if len(code_parts) == 4:
                    st.write(f"**Energy:** {code_parts[0]} kcal")
                    st.write(f"**Protein/Carbs/Fat:** {code_parts[1]}/{code_parts[2]}/{code_parts[3]} g")
            
            # Show ingredients - ORIGINAL
            st.write("**Ingredients:**")
            for _, item in meal_items.iterrows():
                st.write(f"• {item['livsmedel']}: {item['amount']} g")
            
            # Select button - ORIGINAL
            if st.button(f"Select this meal", key=f"select_meal_{idx}_{row['date']}_{row['time']}"):
                selected_meal = {
                    'name': row['name'],
                    'date': row['date'],
                    'time': row['time'],
                    'code': row['code'],
                    'favorite': row.get('favorite', False),
                    'items': meal_items[['livsmedel', 'amount']].rename(
                        columns={'livsmedel': 'Food', 'amount': 'Amount (g)'}
                    )
                }
                break
    
    if selected_meal:
        # Store selected meal info - ORIGINAL
        st.session_state.selected_previous_meal = {
            'name': selected_meal['name'],
            'date': selected_meal['date'], 
            'time': selected_meal['time'],
            'code': selected_meal['code'],
            'favorite': selected_meal['favorite']
        }
        
        # Store meal items for adding to current meal - ORIGINAL
        st.session_state.copied_meal_items = selected_meal['items'].to_dict('records')
        
        st.session_state.show_meal_modal = False
        st.success(f"Selected meal: {selected_meal['name']}")
        st.rerun()

def get_copied_meal_items():
    """Get the copied meal items for integration with existing meal creation - ORIGINAL"""
    if st.session_state.get('copied_meal_items'):
        return pd.DataFrame(st.session_state.copied_meal_items)
    return pd.DataFrame()

# Export all form functions - ORIGINAL FUNCTIONALITY
__all__ = [
    'create_new_form_activity',
    'create_new_form_food', 
    'create_form_add_food_item_to_database',
    'create_form_add_recipie_to_database',
    'create_copy_previous_meal_section',
    'create_meal_selection_modal',
    'get_copied_meal_items'
]