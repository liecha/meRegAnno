# ui_components.py - Reusable UI Components for meRegAnno App
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Callable

def create_date_time_selector(
    date_key: str,
    time_key: str,
    date_label: str = "Select a date",
    time_label: str = "Select a time",
    default_date: Optional[date] = None,
    default_time: Optional[time] = None,
    show_validation: bool = True
) -> tuple:
    """
    Create a standardized date and time selector with validation
    
    Returns:
        tuple: (selected_date, selected_time)
    """
    col1, col2 = st.columns(2)
    
    with col1:
        selected_date = st.date_input(
            date_label,
            value=default_date or datetime.now().date(),
            key=date_key
        )
        if show_validation:
            if selected_date:
                st.success(f"Date: {selected_date}")
            else:
                st.error("Please select a date")
    
    with col2:
        selected_time = st.time_input(
            time_label,
            value=default_time,
            key=time_key
        )
        if show_validation:
            if selected_time:
                st.success(f"Time: {selected_time}")
            else:
                st.error("Please select a time")
    
    return selected_date, selected_time

def create_nutrition_display(nutrition_data: pd.DataFrame, title: str = "Nutrition Summary"):
    """Create standardized nutrition display"""
    if nutrition_data.empty:
        st.caption("No nutrition data available")
        return
    
    st.markdown(f"#### {title}")
    if len(nutrition_data) >= 3:
        col1, col2, col3 = st.columns(3)
        col1.metric("Protein", f"{int(nutrition_data['value'].iloc[0])} g", nutrition_data['percent'].iloc[0])
        col2.metric("Carbs", f"{int(nutrition_data['value'].iloc[1])} g", nutrition_data['percent'].iloc[1])
        col3.metric("Fat", f"{int(nutrition_data['value'].iloc[2])} g", nutrition_data['percent'].iloc[2])

def create_energy_metrics(energy_in: int, energy_out: int, energy_balance: int, deficit_text: str):
    """Create standardized energy metrics display"""
    col1, col2, col3 = st.columns(3)
    col1.metric("Input energy", energy_in, "+ kcal")
    col2.metric("Output energy", energy_out, "-kcal")
    col3.metric("Deficit", energy_balance, deficit_text)

def create_data_table(
    data: pd.DataFrame,
    columns_config: Dict[str, Any],
    table_key: str,
    title: str = None,
    empty_message: str = "No data available"
):
    """Create standardized data table with configuration"""
    if title:
        st.markdown(f"#### {title}")
    
    if data.empty:
        st.caption(empty_message)
        return None
    
    return st.data_editor(
        data,
        column_config=columns_config,
        key=table_key,
        hide_index=True,
        use_container_width=True
    )

def create_form_section(title: str, description: str = None, required: bool = True):
    """Create a form section with consistent styling"""
    required_mark = " *" if required else ""
    st.markdown(f"### {title}{required_mark}")
    if description:
        st.caption(description)
    st.markdown("---")

def create_submit_button_with_validation(
    button_text: str,
    is_valid: bool,
    error_message: str = "Please fix validation errors",
    success_message: str = "Ready to submit",
    button_key: str = None
):
    """Create submit button with validation status"""
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Use st.form_submit_button instead of st.button for forms
        submit_clicked = st.form_submit_button(
            button_text,
            disabled=not is_valid
        )
    
    with col2:
        if not is_valid:
            st.error(error_message)
        else:
            st.success(success_message)
    
    return submit_clicked

def create_activity_input_fields(activity_type: str, current_values: Dict[str, Any] = None):
    """Create activity-specific input fields"""
    if current_values is None:
        current_values = {}
    
    duration = "00:00:00"
    distance = 0.0
    pace = 0.0
    energy = 0
    steps = 0
    note = ""
    
    if activity_type in ["Walk", "Run", "Bike"]:
        col1, col2 = st.columns(2)
        with col1:
            duration = st.text_input(
                "Duration (hh:mm:ss)",
                value=current_values.get('duration', '00:00:00'),
                help="Format: HH:MM:SS"
            )
            distance = st.number_input(
                f"Distance ({'km' if activity_type != 'Swim' else 'meters'})",
                min_value=0.0,
                value=current_values.get('distance', 0.0),
                step=0.1
            )
            if activity_type != "Walk":
                pace = st.number_input(
                    "Pace (min/km)",
                    min_value=0.0,
                    value=current_values.get('pace', 0.0),
                    step=0.1
                )
        
        with col2:
            energy = st.number_input(
                "Energy burned (kcal)",
                min_value=0,
                value=current_values.get('energy', 0),
                step=1
            )
            if activity_type in ["Walk", "Run"]:
                steps = st.number_input(
                    "Steps",
                    min_value=0,
                    value=current_values.get('steps', 0),
                    step=1
                )
    
    elif activity_type == "Swim":
        col1, col2 = st.columns(2)
        with col1:
            duration = st.text_input(
                "Duration (hh:mm:ss)",
                value=current_values.get('duration', '00:00:00')
            )
            distance = st.number_input(
                "Distance (meters)",
                min_value=0.0,
                value=current_values.get('distance', 0.0),
                step=25.0
            )
            pace = st.number_input(
                "Pace (min/100m)",
                min_value=0.0,
                value=current_values.get('pace', 0.0),
                step=0.1
            )
        
        with col2:
            energy = st.number_input(
                "Energy burned (kcal)",
                min_value=0,
                value=current_values.get('energy', 0),
                step=1
            )
    
    elif activity_type in ["Strength", "Yoga"]:
        col1, col2 = st.columns(2)
        with col1:
            duration = st.text_input(
                "Duration (hh:mm:ss)",
                value=current_values.get('duration', '00:00:00')
            )
            energy = st.number_input(
                "Energy burned (kcal)",
                min_value=0,
                value=current_values.get('energy', 0),
                step=1
            )
        with col2:
            pass  # Empty column for layout
    
    # Notes section for all activities
    note_placeholder = {
        "Walk": "Describe your walk: route, pace, how you felt, weather conditions...",
        "Run": "Describe your run: route, performance, splits, how you felt...",
        "Swim": "Pool details, strokes used, technique focus, how you felt...",
        "Bike": "Route details, terrain, bike type, weather conditions...",
        "Strength": "Exercises performed, weights used, sets/reps, muscle groups...",
        "Yoga": "Yoga style, poses practiced, meditation time, how you felt..."
    }.get(activity_type, "Activity details and notes...")
    
    note = st.text_area(
        "Activity notes",
        value=current_values.get('note', ''),
        placeholder=note_placeholder,
        height=100
    )
    
    return {
        'duration': duration,
        'distance': distance,
        'pace': pace,
        'energy': energy,
        'steps': steps,
        'note': note
    }

def create_meal_selection_interface(meal_database: pd.DataFrame):
    """Create meal selection interface for copying previous meals"""
    if meal_database.empty:
        st.info("No previous meals found")
        return None
    
    # Group meals by name, date, and time
    grouped_meals = meal_database.groupby(['name', 'date', 'time', 'code']).first().reset_index()
    grouped_meals = grouped_meals.sort_values(['date', 'time'], ascending=False)
    
    # Search functionality
    search_term = st.text_input("Search meals", help="Search by meal name")
    
    if search_term:
        filtered_meals = grouped_meals[
            grouped_meals['name'].str.contains(search_term, case=False, na=False)
        ]
    else:
        filtered_meals = grouped_meals
    
    if filtered_meals.empty:
        st.warning("No meals found matching your search")
        return None
    
    selected_meal = None
    st.caption(f"Found {len(filtered_meals)} meals")
    
    for idx, row in filtered_meals.iterrows():
        with st.expander(f"{row['name']} - {row['date']} at {row['time']}", expanded=False):
            # Show meal details
            meal_items = meal_database[
                (meal_database['name'] == row['name']) & 
                (meal_database['date'] == row['date']) & 
                (meal_database['time'] == row['time'])
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
            
            # Show ingredients
            st.write("**Ingredients:**")
            for _, item in meal_items.iterrows():
                st.write(f"• {item['livsmedel']}: {item['amount']} g")
            
            # Select button
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
    
    return selected_meal

def create_recipe_portions_input(selected_recipes: List[str]) -> Dict[str, float]:
    """Create portion size inputs for selected recipes"""
    recipe_portions = {}
    
    if selected_recipes:
        st.markdown("##### Recipe portions")
        st.caption("Specify portion sizes for selected recipes (1.0 = full portion, 0.5 = half portion)")
        
        for recipe_name in selected_recipes:
            portion_key = f"portion_{recipe_name.replace(' ', '_')}"
            recipe_portions[recipe_name] = st.number_input(
                f"Portion of {recipe_name}",
                min_value=0.05,
                max_value=10.0,
                value=1.0,
                step=0.05,
                key=portion_key,
                help=f"Enter portion size for {recipe_name}"
            )
    
    return recipe_portions

def create_loading_spinner(message: str = "Loading..."):
    """Create a loading spinner with message"""
    return st.empty().info(f"⏳ {message}")

def create_success_message(message: str, show_balloons: bool = False):
    """Create a success message with optional balloons"""
    st.success(f"✅ {message}")
    if show_balloons:
        st.balloons()

def create_error_display(error_message: str, details: str = None, suggestions: List[str] = None):
    """Create comprehensive error display"""
    st.error(error_message)
    
    if details:
        with st.expander("Error Details"):
            st.code(details)
    
    if suggestions:
        st.info("What you can try:")
        for suggestion in suggestions:
            st.write(f"• {suggestion}")

def create_form_progress_indicator(current_step: int, total_steps: int, step_names: List[str]):
    """Create a progress indicator for multi-step forms"""
    progress = current_step / total_steps
    st.progress(progress)
    
    cols = st.columns(total_steps)
    for i, (col, step_name) in enumerate(zip(cols, step_names)):
        with col:
            if i < current_step:
                st.success(f"✅ {step_name}")
            elif i == current_step:
                st.info(f"📍 {step_name}")
            else:
                st.write(f"⭕ {step_name}")

def create_confirmation_dialog(
    message: str,
    confirm_text: str = "Confirm",
    cancel_text: str = "Cancel",
    key: str = "confirm_dialog"
):
    """Create a confirmation dialog"""
    st.warning(message)
    col1, col2 = st.columns(2)
    
    with col1:
        confirm = st.button(confirm_text, key=f"{key}_confirm", type="primary")
    
    with col2:
        cancel = st.button(cancel_text, key=f"{key}_cancel")
    
    return confirm, cancel

def create_info_box(title: str, content: str, box_type: str = "info"):
    """Create an information box"""
    if box_type == "info":
        st.info(f"**{title}**\n\n{content}")
    elif box_type == "warning":
        st.warning(f"**{title}**\n\n{content}")
    elif box_type == "success":
        st.success(f"**{title}**\n\n{content}")
    else:
        st.write(f"**{title}**\n\n{content}")

# Export all UI components
__all__ = [
    'create_date_time_selector', 'create_nutrition_display', 'create_energy_metrics',
    'create_data_table', 'create_form_section', 'create_submit_button_with_validation',
    'create_activity_input_fields', 'create_meal_selection_interface', 
    'create_recipe_portions_input', 'create_loading_spinner', 'create_success_message',
    'create_error_display', 'create_form_progress_indicator', 'create_confirmation_dialog',
    'create_info_box'
]