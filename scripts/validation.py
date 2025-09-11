import pandas as pd
import re
from datetime import datetime, time, date
from typing import List, Dict, Any, Tuple, Optional

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class ValidationResult:
    """Class to hold validation results"""
    def __init__(self):
        self.is_valid = True
        self.errors = []
        self.warnings = []
    
    def add_error(self, message: str):
        """Add an error message"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add a warning message"""
        self.warnings.append(message)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    def get_all_messages(self) -> List[str]:
        """Get all error and warning messages"""
        return self.errors + self.warnings

def validate_date_time_selection(date_input: Optional[date], time_input: Optional[time]) -> ValidationResult:
    """
    Validate that both date and time are properly selected
    
    Args:
        date_input: Selected date
        time_input: Selected time
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    if date_input is None:
        result.add_error("📅 Please select a date before submitting")
    
    if time_input is None:
        result.add_error("🕐 Please select a time before submitting")
    
    # Check if date is too far in the future
    if date_input and date_input > date.today():
        from datetime import timedelta
        max_future_date = date.today() + timedelta(days=7)
        if date_input > max_future_date:
            result.add_warning("⚠️ Selected date is more than a week in the future")
    
    # Check if date is too far in the past
    if date_input and date_input < date.today():
        from datetime import timedelta
        min_past_date = date.today() - timedelta(days=365)
        if date_input < min_past_date:
            result.add_warning("⚠️ Selected date is more than a year in the past")
    
    return result

def validate_activity_data(activity_type: str, **kwargs) -> ValidationResult:
    """
    Validate activity-specific required fields
    
    Args:
        activity_type: Type of activity (Walk, Run, Swim, etc.)
        **kwargs: Activity-specific data
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    if not activity_type or activity_type.strip() == "":
        result.add_error("🏃 Please select an activity type")
        return result
    
    # Get common fields
    duration = kwargs.get('duration', '00:00:00')
    energy = kwargs.get('energy', 0)
    distance = kwargs.get('distance', 0.0)
    pace = kwargs.get('pace', 0.0)
    steps = kwargs.get('steps', 0)
    note = kwargs.get('note', '')
    
    # Validate duration format
    if duration and not _validate_duration_format(duration):
        result.add_error("⏱️ Duration must be in format HH:MM:SS (e.g., 01:30:00)")
    
    # Validate energy burned
    if energy < 0:
        result.add_error("💪 Energy burned cannot be negative")
    elif energy == 0:
        result.add_warning("⚠️ Energy burned is 0 - is this correct?")
    elif energy > 2000:
        result.add_warning("⚠️ Energy burned seems very high (>2000 kcal) - please verify")
    
    # Activity-specific validations
    if activity_type.lower() in ['walk', 'run', 'bike']:
        # Activities that typically have distance
        if distance <= 0:
            result.add_warning("⚠️ Distance is 0 - consider adding distance for better tracking")
        elif distance > 100:  # More than 100km seems unusual
            result.add_warning("⚠️ Distance seems very high - please verify")
        
        # Validate pace if provided
        if pace > 0 and distance > 0:
            if pace < 2:  # Less than 2 min/km is very fast
                result.add_warning("⚠️ Pace seems very fast - please verify")
            elif pace > 20:  # More than 20 min/km is very slow
                result.add_warning("⚠️ Pace seems very slow - please verify")
    
    elif activity_type.lower() == 'swim':
        # Swimming specific validation
        if distance > 10:  # More than 10km swimming is unusual
            result.add_warning("⚠️ Swimming distance seems very high - please verify")
        
        # Swimming pace validation (different from running)
        if pace > 0 and pace < 1:
            result.add_warning("⚠️ Swimming pace seems very fast - please verify")
    
    elif activity_type.lower() in ['strength', 'yoga']:
        # Activities that don't typically have distance
        if distance > 0:
            result.add_warning("⚠️ Distance is unusual for this activity type")
    
    # Validate steps if provided
    if steps > 0:
        if steps > 50000:  # More than 50k steps seems unusual
            result.add_warning("⚠️ Step count seems very high - please verify")
        elif activity_type.lower() in ['swim', 'strength', 'yoga'] and steps > 1000:
            result.add_warning("⚠️ Step count seems high for this activity type")
    
    # Validate note length
    if note and len(note) > 500:
        result.add_warning("⚠️ Note is very long - consider shortening it")
    
    return result

def validate_meal_composition(meal_items: pd.DataFrame) -> ValidationResult:
    """
    Validate meal composition - simplified to allow zero amounts
    
    Args:
        meal_items: DataFrame with meal composition
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    # Only check if meal_items exists and is not None
    if meal_items is None:
        return result  # Return valid result - let the form handle this
    
    if meal_items.empty:
        return result  # Return valid result - allow empty meals
    
    # Very basic validation - only check for completely invalid data
    try:
        # Just verify the DataFrame can be processed
        if len(meal_items) > 0:
            # Check if there are any food names that are completely empty
            if 'Food' in meal_items.columns:
                empty_foods = meal_items['Food'].isna().all() or (meal_items['Food'] == '').all()
                if empty_foods and len(meal_items) > 1:
                    result.add_warning("Some food items may be missing names")
    except Exception:
        # If anything fails, just return valid - don't block submission
        pass
    
    return result

def validate_nutrition_code(code: str) -> ValidationResult:
    """
    Validate nutrition code format (kcal/protein/carb/fat)
    
    Args:
        code: Nutrition code string
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    if not code or code.strip() == '':
        result.add_error("🔢 Nutrition code cannot be empty")
        return result
    
    # Check format
    parts = code.split('/')
    if len(parts) != 4:
        result.add_error("📋 Nutrition code must be in format: kcal/protein/carb/fat")
        return result
    
    # Validate each part is numeric
    labels = ['calories', 'protein', 'carbohydrates', 'fat']
    for i, (part, label) in enumerate(zip(parts, labels)):
        try:
            value = float(part)
            if value < 0:
                result.add_error(f"❌ {label.capitalize()} cannot be negative")
            elif i == 0 and value > 5000:  # Calories > 5000
                result.add_warning("⚠️ Calorie count seems very high")
            elif i > 0 and value > 500:  # Macros > 500g
                result.add_warning(f"⚠️ {label.capitalize()} amount seems very high")
        except ValueError:
            result.add_error(f"🔢 {label.capitalize()} must be a valid number")
    
    return result

def validate_recipe_data(recipe_name: str, recipe_items: pd.DataFrame, portions: int = 1) -> ValidationResult:
    """
    Validate recipe data
    
    Args:
        recipe_name: Name of the recipe
        recipe_items: DataFrame with recipe composition
        portions: Number of portions
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    # Validate recipe name
    if not recipe_name or recipe_name.strip() == '':
        result.add_error("📝 Recipe name cannot be empty")
    elif len(recipe_name) > 100:
        result.add_warning("⚠️ Recipe name is very long - consider shortening it")
    
    # Validate portions
    if portions <= 0:
        result.add_error("👥 Number of portions must be greater than 0")
    elif portions > 50:
        result.add_warning("⚠️ Number of portions seems very high")
    
    # Validate recipe composition
    meal_validation = validate_meal_composition(recipe_items)
    result.errors.extend(meal_validation.errors)
    result.warnings.extend(meal_validation.warnings)
    if meal_validation.has_errors():
        result.is_valid = False
    
    return result

def validate_food_item_data(name: str, calories: float, protein: float, carb: float, fat: float) -> ValidationResult:
    """
    Validate food item data for database entry
    
    Args:
        name: Food item name
        calories: Calories per 100g
        protein: Protein per 100g
        carb: Carbohydrates per 100g
        fat: Fat per 100g
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    # Validate name
    if not name or name.strip() == '':
        result.add_error("🥗 Food item name cannot be empty")
    elif len(name) > 100:
        result.add_warning("⚠️ Food item name is very long")
    
    # Validate nutritional values
    nutrients = {
        'Calories': calories,
        'Protein': protein,
        'Carbohydrates': carb,
        'Fat': fat
    }
    
    for nutrient_name, value in nutrients.items():
        if value < 0:
            result.add_error(f"❌ {nutrient_name} cannot be negative")
        elif nutrient_name == 'Calories' and value > 900:
            result.add_warning(f"⚠️ {nutrient_name} seems very high (>{value} per 100g)")
        elif nutrient_name != 'Calories' and value > 100:
            result.add_warning(f"⚠️ {nutrient_name} seems very high (>{value}g per 100g)")
    
    # Check if macros add up reasonably
    try:
        macro_calories = (protein * 4) + (carb * 4) + (fat * 9)
        if abs(macro_calories - calories) > calories * 0.2:  # More than 20% difference
            result.add_warning("⚠️ Calories don't match macronutrient breakdown - please verify")
    except:
        pass
    
    return result

def validate_portion_size(portion: float, recipe_name: str = "") -> ValidationResult:
    """
    Validate recipe portion size
    
    Args:
        portion: Portion size (e.g., 0.5 for half portion)
        recipe_name: Name of recipe (for error messages)
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    recipe_text = f" for {recipe_name}" if recipe_name else ""
    
    if portion <= 0:
        result.add_error(f"📏 Portion size{recipe_text} must be greater than 0")
    elif portion > 10:
        result.add_warning(f"⚠️ Portion size{recipe_text} seems very large ({portion})")
    elif portion < 0.05:
        result.add_warning(f"⚠️ Portion size{recipe_text} seems very small ({portion})")
    
    return result

def validate_bmr_parameters(weight: float, height: float, age: int) -> ValidationResult:
    """
    Validate BMR calculation parameters
    
    Args:
        weight: Weight in kg
        height: Height in cm
        age: Age in years
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    # Validate weight
    if weight <= 0:
        result.add_error("⚖️ Weight must be greater than 0")
    elif weight < 30:
        result.add_warning("⚠️ Weight seems very low - please verify")
    elif weight > 300:
        result.add_warning("⚠️ Weight seems very high - please verify")
    
    # Validate height
    if height <= 0:
        result.add_error("📏 Height must be greater than 0")
    elif height < 100:
        result.add_warning("⚠️ Height seems very low - please verify")
    elif height > 250:
        result.add_warning("⚠️ Height seems very high - please verify")
    
    # Validate age
    if age <= 0:
        result.add_error("🎂 Age must be greater than 0")
    elif age < 10:
        result.add_warning("⚠️ Age seems very low for using this app")
    elif age > 100:
        result.add_warning("⚠️ Age seems very high - please verify")
    
    return result

def _validate_duration_format(duration_str: str) -> bool:
    """
    Helper function to validate duration format (HH:MM:SS)
    
    Args:
        duration_str: Duration string to validate
    
    Returns:
        bool: True if valid format
    """
    if not duration_str:
        return False
    
    # Check format HH:MM:SS
    pattern = r'^([0-9]{1,2}):([0-5][0-9]):([0-5][0-9])$'
    match = re.match(pattern, duration_str)
    
    if not match:
        return False
    
    # Additional validation for reasonable values
    hours, minutes, seconds = map(int, match.groups())
    
    # Check for reasonable duration (less than 24 hours)
    if hours >= 24:
        return False
    
    return True

def validate_database_connection() -> ValidationResult:
    """
    Validate database connection and basic functionality
    
    Returns:
        ValidationResult object
    """
    result = ValidationResult()
    
    try:
        # This would be implemented based on your database setup
        # For now, just a placeholder
        result.add_warning("⚠️ Database connection validation not implemented")
    except Exception as e:
        result.add_error(f"❌ Database connection failed: {str(e)}")
    
    return result

def get_validation_summary(validation_results: List[ValidationResult]) -> Dict[str, Any]:
    """
    Get a summary of multiple validation results
    
    Args:
        validation_results: List of ValidationResult objects
    
    Returns:
        Dictionary with validation summary
    """
    total_errors = []
    total_warnings = []
    all_valid = True
    
    for result in validation_results:
        total_errors.extend(result.errors)
        total_warnings.extend(result.warnings)
        if not result.is_valid:
            all_valid = False
    
    return {
        'is_valid': all_valid,
        'total_errors': len(total_errors),
        'total_warnings': len(total_warnings),
        'errors': total_errors,
        'warnings': total_warnings,
        'can_submit': all_valid and len(total_errors) == 0
    }

# Example usage functions for Streamlit integration
def display_validation_results(result: ValidationResult, show_warnings: bool = True):
    """
    Display validation results in Streamlit
    
    Args:
        result: ValidationResult object
        show_warnings: Whether to display warnings
    """
    import streamlit as st
    
    # Display errors
    for error in result.errors:
        st.error(error)
    
    # Display warnings if enabled
    if show_warnings:
        for warning in result.warnings:
            st.warning(warning)

def check_form_ready_to_submit(validation_results: List[ValidationResult]) -> bool:
    """
    Check if form is ready to submit based on validation results
    
    Args:
        validation_results: List of validation results
    
    Returns:
        bool: True if form can be submitted
    """
    for result in validation_results:
        if result.has_errors():
            return False
    return True