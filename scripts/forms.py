import streamlit as st
import pandas as pd
from datetime import datetime, time

# Import new modules
from scripts.validation import (
    validate_date_time_selection, validate_activity_data, validate_meal_composition,
    validate_nutrition_code, validate_recipe_data, validate_food_item_data,
    validate_portion_size, ValidationResult, display_validation_results,
    check_form_ready_to_submit
)
from scripts.error_handling import (
    handle_errors, error_context, loading_indicator, validate_form_submission,
    create_error_recovery_point, restore_from_recovery_point, safe_dataframe_operation
)
from scripts.ui_components import (
    create_date_time_selector, create_activity_input_fields, create_submit_button_with_validation,
    create_form_section, create_success_message, create_meal_selection_interface,
    create_recipe_portions_input
)
from scripts.constants import ACTIVITY_TYPES, get_activity_emoji, get_default_value

# Import existing modules
from scripts.data_dashboard import date_time_now, datetime_to_string, time_to_string
from scripts.data_storage import fetch_data_from_storage, add_registration, save_data_to_storage
from scripts.nutritions import locate_eatables, code_detector

@handle_errors("activity form initialization")
def create_new_form_activity(bmr):
    """
    Create activity registration form with comprehensive validation and error handling
    PRESERVES ALL ORIGINAL FUNCTIONALITY
    """
    # Initialize session state for form data persistence
    if "activity_form_data" not in st.session_state:
        st.session_state.activity_form_data = {
            "selected_date": None,
            "selected_time": None,
            "activity_type": "",
            "duration": "00:00:00",
            "distance": 0.0,
            "pace": 0.0,
            "energy": 0,
            "steps": 0,
            "note": ""
        }
    
    # Recovery point restoration
    recovered_data = restore_from_recovery_point("activity_form")
    if recovered_data and st.button("Restore previous session", key="restore_activity"):
        st.session_state.activity_form_data.update(recovered_data)
        st.success("Previous session restored!")
        st.rerun()
    
    # Date and time selection using UI component
    selected_date, selected_time = create_date_time_selector(
        "act_date", "act_time", 
        "Select a date", "Select a time",
        default_date=st.session_state.activity_form_data.get("selected_date")
    )
    
    # Update session state
    st.session_state.activity_form_data.update({
        "selected_date": selected_date,
        "selected_time": selected_time
    })
    
    # Activity type selection
    activity_type = st.selectbox(
        "Choose activity", 
        [""] + ACTIVITY_TYPES,
        index=0,
        key="activity_type_select"
    )
    st.session_state.activity_form_data["activity_type"] = activity_type
    
    # Validate basic selections before showing detailed form
    datetime_validation = validate_date_time_selection(selected_date, selected_time)
    display_validation_results(datetime_validation)
    
    # Only show detailed form if activity is selected
    if not activity_type:
        st.info("Please select an activity type to continue")
        return
    
    # Create error recovery point
    create_error_recovery_point(st.session_state.activity_form_data, "activity_form")
    
    # Activity-specific form
    with st.form(key="activity_form", clear_on_submit=False):
        st.subheader(f"{get_activity_emoji(activity_type)} Register {activity_type} Activity")
        
        # Get activity input fields using UI component
        activity_data = create_activity_input_fields(
            activity_type, 
            st.session_state.activity_form_data
        )
        
        # Update session state with current values
        st.session_state.activity_form_data.update(activity_data)
        
        # Validation before submit button
        validation_results = [datetime_validation]
        
        # Validate activity data
        activity_validation = validate_activity_data(activity_type, **activity_data)
        validation_results.append(activity_validation)
        
        # Show validation results
        for result in validation_results:
            display_validation_results(result)
        
        # Submit button with validation
        form_is_valid = check_form_ready_to_submit(validation_results)
        submit_button = create_submit_button_with_validation(
            "Submit Activity",
            form_is_valid,
            "Please fix validation errors before submitting",
            "Ready to submit activity"
        )
        
        # Handle form submission
        if submit_button and form_is_valid:
            try:
                with loading_indicator("Saving activity..."):
                    # Convert distance for swimming (meters to km)
                    distance_km = activity_data['distance'] / 1000.0 if activity_type == "Swim" else activity_data['distance']
                    
                    # Prepare activity data - SAME AS ORIGINAL
                    activity_registration = {
                        "date": selected_date,
                        "time": selected_time,
                        "label": 'TRAINING',
                        "energy": -1 * int(activity_data['energy']),
                        "pro": 0,
                        "carb": 0,
                        "fat": 0,
                        "activity": activity_type,
                        "distance": distance_km,
                        "duration": activity_data['duration'],
                        "pace": activity_data['pace'],
                        "steps": activity_data['steps'],
                        "note": str(activity_data['note']),
                    }
                    
                    # Save the registration - SAME AS ORIGINAL
                    add_registration(activity_registration, bmr)
                    
                    # Clear form data on successful submission
                    st.session_state.activity_form_data = {
                        "selected_date": None,
                        "selected_time": None,
                        "activity_type": "",
                        "duration": "00:00:00",
                        "distance": 0.0,
                        "pace": 0.0,
                        "energy": 0,
                        "steps": 0,
                        "note": ""
                    }
                    
                    create_success_message(f"{activity_type} activity registered successfully!", show_balloons=True)
                    
            except Exception as e:
                st.error("Failed to save activity. Please try again.")
                with st.expander("Error Details"):
                    st.code(str(e))

@handle_errors("meal form initialization")
def create_new_form_food(code, options_string, bmr, df_meal_items=None):
    """
    Create food registration form - PRESERVES ALL ORIGINAL FUNCTIONALITY
    """
    # Initialize session state for form persistence
    if "food_form_data" not in st.session_state:
        st.session_state.food_form_data = {
            "selected_date": None,
            "selected_time": None,
            "meal_code": code,
            "meal_note": options_string,
            "mark_favorite": False
        }
    
    # Date and time selection
    selected_date, selected_time = create_date_time_selector(
        "food_date", "food_time",
        "Select a date", "What time did you eat",
        default_date=st.session_state.food_form_data.get("selected_date")
    )
    
    # Update session state
    st.session_state.food_form_data.update({
        "selected_date": selected_date,
        "selected_time": selected_time
    })
    
    # Validate datetime selection
    datetime_validation = validate_date_time_selection(selected_date, selected_time)
    display_validation_results(datetime_validation)
    
    # Meal registration form
    with st.form(key="food_registration_form", clear_on_submit=False):
        create_form_section("Register Meal", "Enter meal details and mark as favorite if desired")
        
        # Nutrition code input with validation
        meal_code = st.text_input(
            "Meal code (kcal/protein/carb/fat)", 
            value=code,
            help="Automatically calculated from meal composition",
            key="meal_code_input"
        )
        
        # Validate nutrition code
        code_validation = validate_nutrition_code(meal_code)
        display_validation_results(code_validation)
        
        # Meal details - SAME AS ORIGINAL
        meal_note = st.text_input(
            "Meal details", 
            value=options_string,
            help="Description of the meal contents",
            key="meal_note_input"
        )
        
        # Favorite meal option - SAME AS ORIGINAL
        mark_favorite = st.checkbox(
            "Mark as favorite meal", 
            value=st.session_state.food_form_data.get("mark_favorite", False),
            help="Save this meal to your favorites for easy access later"
        )
        
        # Update session state
        st.session_state.food_form_data.update({
            "meal_code": meal_code,
            "meal_note": meal_note,
            "mark_favorite": mark_favorite
        })
        
        # Only validate date/time and nutrition code - remove restrictive meal validation
        validation_results = [datetime_validation, code_validation]
        
        # Show friendly info about meal composition without blocking submission
        if df_meal_items is None:
            st.info("Create a meal composition on the left to register it")
        elif df_meal_items.empty:
            st.info("Add some ingredients to your meal")
        else:
            # Just show a simple validation for display purposes, but don't block submission
            meal_validation = validate_meal_composition(df_meal_items)
            display_validation_results(meal_validation)
        
        # Form is valid if date/time are selected and there's some meal data
        # Allow zero amounts - user can register partial meals
        form_is_valid = check_form_ready_to_submit(validation_results) and df_meal_items is not None
        
        # Submit button with validation
        submit_button = create_submit_button_with_validation(
            "Register Meal",
            form_is_valid,
            "Please create a meal composition first" if df_meal_items is None else "Please fix validation errors",
            "Ready to register meal"
        )
        
        # Handle form submission - SAME LOGIC AS ORIGINAL
        if submit_button and form_is_valid:
            try:
                with loading_indicator("Registering meal..."):
                    # Parse nutrition code - SAME AS ORIGINAL
                    food_split = meal_code.split('/')
                    if len(food_split) != 4:
                        raise ValueError("Invalid nutrition code format")
                    
                    # SAVE MEAL TO DATABASE FIRST - SAME AS ORIGINAL
                    if df_meal_items is not None and len(df_meal_items) > 0:
                        try:
                            # Prepare meal data for database - SAME AS ORIGINAL
                            df_meal_to_save = df_meal_items.copy()
                            df_meal_to_save['date'] = datetime_to_string(selected_date)
                            df_meal_to_save['time'] = time_to_string(selected_time)
                            df_meal_to_save['favorite'] = mark_favorite
                            
                            # Load existing meal database - SAME AS ORIGINAL
                            try:
                                df_meal_db = fetch_data_from_storage('data/meal_databas.csv')
                            except:
                                df_meal_db = pd.DataFrame(columns=[
                                    'date', 'time', 'name', 'livsmedel', 'amount', 'code', 'favorite'
                                ])
                            
                            # Save to database - SAME AS ORIGINAL
                            df_updated_meal_db = pd.concat([df_meal_db, df_meal_to_save], ignore_index=True)
                            save_data_to_storage(df_updated_meal_db, 'data/meal_databas.csv')
                            
                        except Exception as e:
                            st.warning(f"Could not save meal to database: {str(e)}")
                    
                    # Register the meal in main energy tracking - SAME AS ORIGINAL
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
                    
                    add_registration(meal_registration_data, bmr)
                    
                    # Clear form data on successful submission - ENHANCED
                    st.session_state.food_form_data = {
                        "selected_date": None,
                        "selected_time": None,
                        "meal_code": "",
                        "meal_note": "",
                        "mark_favorite": False
                    }
                    
                    # Clear meal creation state as well - SAME AS ORIGINAL
                    if 'current_meal_items' in st.session_state:
                        st.session_state.current_meal_items = None
                    if 'create_meal' in st.session_state:
                        st.session_state.create_meal = []
                    if 'find_recipie' in st.session_state:
                        st.session_state.find_recipie = []
                    
                    create_success_message("Meal registered successfully!", show_balloons=True)
                    
            except ValueError as e:
                st.error(f"Invalid input: {str(e)}")
            except Exception as e:
                st.error("Failed to register meal. Please try again.")
                with st.expander("Error Details"):
                    st.code(str(e))

@handle_errors("food item form initialization")
def create_form_add_food_item_to_database():
    """
    Create form for adding new food items to database - PRESERVES ALL ORIGINAL FUNCTIONALITY
    """
    with st.form(key="food_item_form", clear_on_submit=True):
        create_form_section("Add New Food Item", "Add a new food item to the database with nutritional information")
        
        # Food item inputs - SAME AS ORIGINAL but with better layout
        food_name = st.text_input(
            "Name of food item",
            help="Enter the name of the food item (e.g., 'Chicken breast, grilled')"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            calories = st.number_input(
                "Energy (kcal / 100 g)",
                min_value=0.0,
                step=1.0,
                help="Calories per 100 grams"
            )
            protein = st.number_input(
                "Proteins (g / 100 g)",
                min_value=0.0,
                step=0.1,
                help="Protein content per 100 grams"
            )
        
        with col2:
            carb = st.number_input(
                "Carbohydrates (g / 100 g)",
                min_value=0.0,
                step=0.1,
                help="Carbohydrate content per 100 grams"
            )
            fat = st.number_input(
                "Fats (g / 100 g)",
                min_value=0.0,
                step=0.1,
                help="Fat content per 100 grams"
            )
        
        # Validation before submit
        validation_result = validate_food_item_data(food_name, calories, protein, carb, fat)
        display_validation_results(validation_result)
        
        form_is_valid = not validation_result.has_errors()
        
        # Submit button with validation
        submit_button = create_submit_button_with_validation(
            "Save Food Item",
            form_is_valid,
            "Complete all required fields with valid values",
            "Ready to save food item"
        )
        
        # Handle submission - SAME LOGIC AS ORIGINAL
        if submit_button and form_is_valid:
            try:
                with loading_indicator("Saving food item..."):
                    # Create new food item - SAME AS ORIGINAL
                    new_food_item = {
                        'livsmedel': food_name.strip(),
                        'calorie': float(calories),
                        'protein': float(protein),
                        'carb': float(carb),
                        'fat': float(fat)
                    }
                    
                    # Load existing database - SAME AS ORIGINAL
                    df_food_db = fetch_data_from_storage('data/livsmedelsdatabas.csv')
                    
                    # Check for duplicates - ENHANCED
                    if food_name.strip().lower() in df_food_db['livsmedel'].str.lower().values:
                        st.warning(f"Food item '{food_name}' already exists in database")
                        return
                    
                    # Add new item - SAME AS ORIGINAL
                    df_new_food_item = pd.DataFrame([new_food_item])
                    df_updated = pd.concat([df_food_db, df_new_food_item], ignore_index=True)
                    
                    # Save to storage - SAME AS ORIGINAL
                    save_data_to_storage(df_updated, 'data/livsmedelsdatabas.csv')
                    
                    create_success_message(f"Food item '{food_name}' added successfully!")
                    
            except Exception as e:
                st.error("Failed to save food item. Please try again.")
                with st.expander("Error Details"):
                    st.code(str(e))

@handle_errors("recipe form initialization")
def create_form_add_recipie_to_database(meal_df, code):
    """
    Create form for adding recipes to database - PRESERVES ALL ORIGINAL FUNCTIONALITY
    """
    # Initialize session state for recipe data
    if "recipe_form_data" not in st.session_state:
        st.session_state.recipe_form_data = {
            "recipe_name": "",
            "is_favorite": False
        }
    
    with st.form(key="recipe_form", clear_on_submit=True):
        create_form_section("Save Recipe", "Save this recipe composition to your recipe database")
        
        # Recipe name input - SAME AS ORIGINAL
        recipe_name = st.text_input(
            "Name of recipe",
            value=st.session_state.recipe_form_data.get("recipe_name", ""),
            help="Enter a descriptive name for this recipe"
        )
        
        # Display nutrition code (read-only) - SAME AS ORIGINAL
        st.text_input(
            "Nutrition code (kcal/protein/carb/fat)",
            value=code,
            disabled=True,
            help="Automatically calculated from recipe ingredients"
        )
        
        # Favorite checkbox - SAME AS ORIGINAL
        is_favorite = st.checkbox(
            "Save recipe as favorite",
            value=st.session_state.recipe_form_data.get("is_favorite", False),
            help="Mark this recipe as a favorite for easy access"
        )
        
        # Update session state
        st.session_state.recipe_form_data.update({
            "recipe_name": recipe_name,
            "is_favorite": is_favorite
        })
        
        # Validation
        validation_results = []
        
        # Validate recipe data
        if hasattr(meal_df, 'empty') and not meal_df.empty:
            recipe_validation = validate_recipe_data(recipe_name, meal_df, portions=1)
            validation_results.append(recipe_validation)
            display_validation_results(recipe_validation)
        else:
            st.error("No recipe composition data available")
            return
        
        # Validate nutrition code
        code_validation = validate_nutrition_code(code)
        validation_results.append(code_validation)
        display_validation_results(code_validation)
        
        # Check if form is ready to submit
        form_is_valid = check_form_ready_to_submit(validation_results)
        
        # Submit button with validation
        submit_button = create_submit_button_with_validation(
            "Save Recipe",
            form_is_valid,
            "Complete all fields to save the recipe",
            "Ready to save recipe"
        )
        
        # Handle submission - SAME LOGIC AS ORIGINAL
        if submit_button and form_is_valid:
            try:
                with loading_indicator("Saving recipe..."):
                    # Load existing recipe database - SAME AS ORIGINAL
                    df_recipe_db = fetch_data_from_storage('data/recipie_databas.csv')
                    
                    # Check for duplicate recipe names - ENHANCED
                    if recipe_name.strip().lower() in df_recipe_db['name'].str.lower().values:
                        st.warning(f"Recipe '{recipe_name}' already exists. Choose a different name.")
                        return
                    
                    # Prepare recipe data - SAME AS ORIGINAL
                    df_recipe_data = meal_df.copy()
                    df_recipe_data['name'] = recipe_name.strip()
                    df_recipe_data['code'] = code
                    df_recipe_data['favorite'] = is_favorite
                    
                    # Rename columns to match database schema - SAME AS ORIGINAL
                    if 'Food' in df_recipe_data.columns:
                        df_recipe_data = df_recipe_data.rename(columns={
                            "Food": "livsmedel", 
                            "Amount (g)": "amount"
                        })
                    
                    # Ensure correct column order - SAME AS ORIGINAL
                    df_recipe_data = df_recipe_data[['name', 'livsmedel', 'amount', 'code', 'favorite']]
                    
                    # Add to database - SAME AS ORIGINAL
                    df_updated = pd.concat([df_recipe_db, df_recipe_data], ignore_index=True)
                    save_data_to_storage(df_updated, 'data/recipie_databas.csv')
                    
                    # Clear form data and recipe creation state
                    keys_to_clear = [
                        'recipe_form_data', 'add_meal', 'df_meal_storage', 'add_meal_editor'
                    ]
                    
                    for key in keys_to_clear:
                        if key in st.session_state:
                            del st.session_state[key]
                    
                    favorite_text = " as favorite" if is_favorite else ""
                    st.success(f"Recipe '{recipe_name}' saved successfully{favorite_text}!")
                    st.info("Form has been cleared. You can create another recipe.")
                    st.rerun()
                    
            except Exception as e:
                st.error("Failed to save recipe. Please try again.")
                with st.expander("Error Details"):
                    st.code(str(e))

# COPY PREVIOUS MEAL FUNCTIONALITY - PRESERVED FROM ORIGINAL
def create_copy_previous_meal_section():
    """Create a section for copying previous meals - PRESERVES ALL ORIGINAL FUNCTIONALITY"""
    create_form_section("Copy Previous Meal", "Select a previously saved meal to add to your current meal")
    
    # Initialize session state for modal - SAME AS ORIGINAL
    if "show_meal_modal" not in st.session_state:
        st.session_state.show_meal_modal = False
    if "selected_previous_meal" not in st.session_state:
        st.session_state.selected_previous_meal = None
    if "copied_meal_items" not in st.session_state:
        st.session_state.copied_meal_items = []
    
    # Button to open meal selection modal - SAME AS ORIGINAL
    if st.button("Browse previous meals", type="secondary", key="open_meal_modal"):
        st.session_state.show_meal_modal = True
    
    # Modal for meal selection - SAME AS ORIGINAL
    if st.session_state.show_meal_modal:
        create_meal_selection_modal()
    
    # Display selected meal info if any - SAME AS ORIGINAL
    if st.session_state.selected_previous_meal:
        meal_info = st.session_state.selected_previous_meal
        st.success(f"Selected: **{meal_info['name']}** from {meal_info['date']} at {meal_info['time']}")
        st.caption(f"Meal code: {meal_info['code']}")
        
        # Clear selection button - SAME AS ORIGINAL
        if st.button("Clear selection", key="clear_meal_selection"):
            st.session_state.selected_previous_meal = None
            st.session_state.copied_meal_items = []
            st.rerun()

def create_meal_selection_modal():
    """Create a modal for selecting previous meals - PRESERVES ALL ORIGINAL FUNCTIONALITY"""
    # Load meal database - SAME AS ORIGINAL
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
    
    # Use UI component for meal selection
    selected_meal = create_meal_selection_interface(df_meal_db)
    
    if selected_meal:
        # Store selected meal info - SAME AS ORIGINAL
        st.session_state.selected_previous_meal = {
            'name': selected_meal['name'],
            'date': selected_meal['date'], 
            'time': selected_meal['time'],
            'code': selected_meal['code'],
            'favorite': selected_meal['favorite']
        }
        
        # Store meal items for adding to current meal - SAME AS ORIGINAL
        st.session_state.copied_meal_items = selected_meal['items'].to_dict('records')
        
        st.session_state.show_meal_modal = False
        st.success(f"Selected meal: {selected_meal['name']}")
        st.rerun()

def get_copied_meal_items():
    """Get the copied meal items for integration with existing meal creation - PRESERVES ORIGINAL"""
    if st.session_state.get('copied_meal_items'):
        return pd.DataFrame(st.session_state.copied_meal_items)
    return pd.DataFrame()

# Export all form functions - PRESERVES ALL ORIGINAL FUNCTIONALITY
__all__ = [
    'create_new_form_activity',
    'create_new_form_food', 
    'create_form_add_food_item_to_database',
    'create_form_add_recipie_to_database',
    'create_copy_previous_meal_section',
    'create_meal_selection_modal',
    'get_copied_meal_items'
]