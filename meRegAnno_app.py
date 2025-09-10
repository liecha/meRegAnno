# Import libraries
import streamlit as st
import pandas as pd
import datetime
import altair as alt

import io

# ===================== DATA STORAGE CONFIGURATION =====================
# SINGLE SOURCE OF TRUTH: Set this to True to use Supabase database, False to use CSV files
USE_DATABASE = False  # Change to True when ready to use database

# Import and configure data storage module
from scripts.data_storage import fetch_data_from_storage
from scripts.data_storage import save_data_to_storage
from scripts.data_storage import delete_item_from_dataset
import scripts.data_storage as ds
ds.USE_DATABASE = USE_DATABASE  # Pass configuration to data_storage module

from scripts.data_dashboard import calc_bmr
from scripts.data_dashboard import date_time_now
from scripts.data_dashboard import time_now
from scripts.data_dashboard import time_to_string
from scripts.data_dashboard import datetime_to_string
from scripts.data_dashboard import translate_dates_to_text
from scripts.data_dashboard import calc_daily_energy_output
from scripts.data_dashboard import calc_energy_deficite
from scripts.data_dashboard import nutrition_content
from scripts.data_dashboard import nutrition_differ
from scripts.data_dashboard import add_summary_to_dataset 
from scripts.data_dashboard import energy_differ
from scripts.data_dashboard import energy_balance_at_current_time

from scripts.nutritions import locate_eatables
from scripts.nutritions import code_detector

from scripts.forms import create_new_form_activity
from scripts.forms import create_new_form_food
from scripts.forms import create_form_add_recipie_to_database
from scripts.forms import create_form_add_food_item_to_database

# Rest of your existing code continues here...
# Page configuration
st.set_page_config(
    page_title="meRegAnno",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded")

alt.themes.enable("dark")

# CSS styling
st.markdown("""
    <style>
    /* Remove blank space at top and bottom */ 
    .block-container {
        padding-top: 0rem;
    }

    /* Remove enter to commit in input_text fields */                
    div[data-testid="InputInstructions"] > span:nth-child(1) {
        visibility: hidden;
    }

    /* breakline for metric text */
    div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
    overflow-wrap: break-word;
    white-space: break-spaces;
    color: red;
    }
    </style>
""", unsafe_allow_html=True)

df_energy = fetch_data_from_storage('data/updated-database-results.csv')

st.subheader('Emelie Chandni Jutvik')

def create_dashobard():
    col = st.columns((5.5, 5.5), gap='medium') 
    with col[0]: 
        current_date, text_month, text_weekday = translate_dates_to_text(selected_date)
        df_energy_date = df_energy[df_energy['date'] == selected_date]
        sum_energy_output = calc_daily_energy_output(df_energy_date, bmr)
        df_deficite = calc_energy_deficite(df_energy, selected_date, selected_date_input)
        deficite_string = ''
        seven_days_deficite_sum = 0
        if len(df_deficite) > 0:
            seven_days_deficite_sum = sum(df_deficite['energy_acc'].values)
            for i in range(0, len(df_deficite)):
                deficite_string = deficite_string + str(int(df_deficite['energy_acc'].iloc[i])) + ', '
            deficite_string = deficite_string[:-2]
        
        if len(df_energy_date) != 0:
            # NUTRITION
            df_nutrition_acc = nutrition_content(df_energy_date)
            df_nutritions_labeled = nutrition_differ(df_energy_date)
            
            # ACTIVITY
            df_activity_irl = add_summary_to_dataset(df_energy_date)
        
            df_energy_plot = energy_differ(df_energy_date)
            energy_in, energy_out, energy_balance, deficite_text = energy_balance_at_current_time(df_energy_date)
              
        if len(df_energy_date) == 0:
            st.markdown('#### Summary energy') 
            st.caption("The selected date is _:blue[" + str(current_date) + ' ' + text_month + " (" + text_weekday + ")]_")  
            st.caption("There is _:blue[no data available]_ for the selected day")    
        else:
            st.markdown('#### Summary energy') 
            st.caption("The selected date is _:blue[" + str(current_date) + ' ' + text_month + " (" + text_weekday + ")]_")               
            col1, col2, col3 = st.columns(3)
            col1.metric("Input energy", energy_in, "+ kcal")
            col2.metric("Output energy", energy_out, "-kcal")
            col3.metric("Deficite", energy_balance, deficite_text)  
            st.caption("_:blue[Energy inputs/outputs/deficite]_ at selected day in _:blue[real time]_")

        if len(df_energy_date) == 0:
            st.markdown('#### Accumulated deficit') 
            if seven_days_deficite_sum == 0:
                st.caption("There is _:blue[no data available]_ for the selected day")
            else:
                st.caption("_:blue[Total energy deficite]_ is " + "_:blue[" + str(int(seven_days_deficite_sum)) + " kcal]_  for the last seven days")  

        else:
            st.markdown('#### Accumulated deficit') 
            if seven_days_deficite_sum == 0:
                st.caption("There is _:blue[no data available]_ for the selected day")
            else:
                st.caption("_:blue[Total energy deficite]_ is " + "_:blue[" + str(int(seven_days_deficite_sum)) + " kcal]_  for the last seven days")  
                df_deficite_show = df_deficite[['date_text', 'energy_acc']]
                st.data_editor(
                    df_deficite_show, 
                    column_config={
                        "date_text": st.column_config.Column(
                            "Day",
                            width="small",
                            required=True,
                        ),
                        "energy_acc": st.column_config.Column(
                            "Deficite (kcal/day)",
                            width="small",
                            required=True,
                        ),
                    },
                    key='energy_deficite', 
                    hide_index=True, 
                    use_container_width=True
                )
            st.caption("_:blue[Energy inputs/outputs/deficite]_ at selected day in _:blue[real time]_")
            st.bar_chart(df_energy_plot, x="time", y="energy", color="label")
                                
    with col[1]:
        if len(df_energy_date) == 0:
            st.markdown('#### Summary meals/activity') 
            if len(df_deficite) != 0:
                st.caption("_:blue[Total energy needed]_ at selected day is _:blue[" + str(int(sum_energy_output)) + " kcal]_. Your body requires _:blue[" + str(bmr) + " kcal]_ at rest.")  
            else:
                st.caption("_:blue[No data is available]_ at selected date")  
        else:
            st.markdown('#### Summary meals/activity') 
            if len(df_deficite) != 0:
                st.caption("_:blue[Total energy needed]_ at selected day is _:blue[" + str(int(sum_energy_output)) + " kcal]_. Your body requires _:blue[" + str(bmr) + " kcal]_ at rest.")  
            else:
                st.caption("_:blue[No data is available]_ at selected date")  
            
            if sum(df_nutritions_labeled['nutrient'].values) == 0.0:
                st.caption("There are _:blue[no meals registered]_ for the selected day")   
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric("Protein", str(int(df_nutrition_acc['value'].iloc[0])) + ' g', df_nutrition_acc['percent'].iloc[0])
                col2.metric("Carbs", str(int(df_nutrition_acc['value'].iloc[1])) + ' g', df_nutrition_acc['percent'].iloc[1])
                col3.metric("Fat", str(int(df_nutrition_acc['value'].iloc[2])) + ' g', df_nutrition_acc['percent'].iloc[2]) 
                st.caption("_:blue[Nutrition intake]_ at selected day in _:blue[real time]_")
                
            st.markdown('#### Registered meals/activities') 
            if sum(df_nutritions_labeled['nutrient'].values) == 0.0:
                st.caption("There are _:blue[no meals registered]_ for the selected day")
            else: 
                st.caption("There are _:blue[meals and activities registered]_ for the selected day")
                if len(df_energy_date) > 0:
                    df_activity_irl = df_activity_irl[['time', 'summary']]
                    st.data_editor(
                        df_activity_irl, 
                        column_config={
                            "time": st.column_config.Column(
                                "Time",
                                width="small",
                                required=True,
                            ),
                            "summary": st.column_config.Column(
                                "Summary",
                                width="large",
                                required=True,
                            ),
                        },
                        key='change_registration', 
                        hide_index=True, 
                        use_container_width=True
                    )
                st.caption("_:blue[Nutrition intake]_ for registered meals at selected day")
                st.bar_chart(df_nutritions_labeled, x="time", y="nutrient", color="label")    
                 
def create_page_activity_registration():
    col = st.columns((5.5, 5.5), gap='medium') 
    df_energy_date = df_energy[df_energy['date'] == selected_date]
    if len(df_energy_date) != 0:            
            df_activity_irl = add_summary_to_dataset(df_energy_date)
    with col[0]:  
        st.markdown('#### Stored activities') 
        if len(df_energy_date) != 0:
            if len(df_energy_date) > 0:
                df_activity_irl = df_activity_irl[['time', 'summary']]
                st.data_editor(
                    df_activity_irl, 
                    column_config={
                        "time": st.column_config.Column(
                            "Time",
                            width="small",
                            required=True,
                        ),
                        "summary": st.column_config.Column(
                            "Summary",
                            width="large",
                            required=True,
                        ),
                    },
                    key='change_registration', 
                    hide_index=True, 
                    use_container_width=True
                )
                st.caption("_:blue[Stored activities]_ from selected day in _:blue[real time]_")
                st.bar_chart(df_energy_date, x="time", y="energy", color="activity") 
        else:
             st.caption("There are _:blue[no stored activities]_ at selected day") 
    with col[1]:
        st.markdown("#### Create new activity")
        create_new_form_activity(bmr)




# Add this new function to your main app file (meRegAnno_app.py)
# Insert this function after the existing meal registration functions

def create_copy_previous_meal_section():
    """Create a section for copying previous meals"""
    st.markdown("#### Copy previous meal")
    st.caption("Select a _:blue[previously saved meal]_ to add to your current meal")
    
    # Initialize session state for modal
    if "show_meal_modal" not in st.session_state:
        st.session_state.show_meal_modal = False
    if "selected_previous_meal" not in st.session_state:
        st.session_state.selected_previous_meal = None
    if "copied_meal_items" not in st.session_state:
        st.session_state.copied_meal_items = []
    
    # Button to open meal selection modal
    if st.button("Browse previous meals", type="secondary", key="open_meal_modal"):
        st.session_state.show_meal_modal = True
    
    # Modal for meal selection
    if st.session_state.show_meal_modal:
        create_meal_selection_modal()
    
    # Display selected meal info if any
    if st.session_state.selected_previous_meal:
        meal_info = st.session_state.selected_previous_meal
        st.success(f"Selected: **{meal_info['name']}** from {meal_info['date']} at {meal_info['time']}")
        st.caption(f"Meal code: {meal_info['code']}")
        
        # Clear selection button
        if st.button("Clear selection", key="clear_meal_selection"):
            st.session_state.selected_previous_meal = None
            st.session_state.copied_meal_items = []
            st.rerun()

def create_meal_selection_modal():
    """Create a modal for selecting previous meals"""
    # Load meal database
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
    
    # Create modal container
    with st.container():
        st.markdown("---")
        st.markdown("### 🍽️ Select a Previous Meal")
        
        # Close button
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("✖️ Close", key="close_meal_modal"):
                st.session_state.show_meal_modal = False
                st.rerun()
        
        # Get unique meals grouped by name, date, and time
        df_meals_grouped = df_meal_db.groupby(['name', 'date', 'time', 'code']).first().reset_index()
        df_meals_grouped = df_meals_grouped.sort_values(['date', 'time'], ascending=False)
        
        # Search functionality
        search_term = st.text_input("🔍 Search meals", key="meal_search", 
                                   help="Search by meal name")
        
        if search_term:
            df_meals_filtered = df_meals_grouped[
                df_meals_grouped['name'].str.contains(search_term, case=False, na=False)
            ]
        else:
            df_meals_filtered = df_meals_grouped
        
        # Display meals in a nice format
        if df_meals_filtered.empty:
            st.warning("No meals found matching your search")
        else:
            st.caption(f"Found {len(df_meals_filtered)} meals")
            
            # Display meals
            for idx, row in df_meals_filtered.iterrows():
                with st.expander(f"🍽️ {row['name']} - {row['date']} at {row['time']}", 
                               expanded=False):
                    
                    # Show meal details
                    meal_items = df_meal_db[
                        (df_meal_db['name'] == row['name']) & 
                        (df_meal_db['date'] == row['date']) & 
                        (df_meal_db['time'] == row['time'])
                    ]
                    
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.write(f"**Date:** {row['date']}")
                        st.write(f"**Time:** {row['time']}")
                        if row['favorite']:
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
                    if st.button(f"Select this meal", 
                               key=f"select_meal_{idx}_{row['date']}_{row['time']}"):
                        # Store selected meal info
                        st.session_state.selected_previous_meal = {
                            'name': row['name'],
                            'date': row['date'],
                            'time': row['time'],
                            'code': row['code'],
                            'favorite': row['favorite']
                        }
                        
                        # Store meal items for adding to current meal
                        st.session_state.copied_meal_items = meal_items[['livsmedel', 'amount']].rename(
                            columns={'livsmedel': 'Food', 'amount': 'Amount (g)'}
                        ).to_dict('records')
                        
                        st.session_state.show_meal_modal = False
                        st.success(f"Selected meal: {row['name']}")
                        st.rerun()
        
        st.markdown("---")

def get_copied_meal_items():
    """Get the copied meal items for integration with existing meal creation"""
    if st.session_state.get('copied_meal_items'):
        return pd.DataFrame(st.session_state.copied_meal_items)
    return pd.DataFrame()

# Modified version of the meal registration page
def create_page_meal_registration_with_copy():
    """Modified meal registration page that includes copy previous meal functionality"""
    col = st.columns((5.5, 5.5), gap='medium') 
    df_meal_items = None
    code = ''
    options_string = ''
    
    # Initialize session state for meal items
    if "current_meal_items" not in st.session_state:
        st.session_state.current_meal_items = None
    
    with col[0]: 
        # Add the copy previous meal section at the top
        create_copy_previous_meal_section()
        
        st.markdown("#### Add recipie")
        st.caption("Type in a _:blue[ recipie name]_ that you want to add to your meal")  
        df_recipie_db = fetch_data_from_storage('data/recipie_databas.csv').sort_values(['name'])
        
        recipie_list = df_recipie_db['name'].unique()

        st.multiselect(
            "Select recipies to add to your meal",
            recipie_list,
            key='find_recipie'
        )

        if "options_recipie" not in st.session_state:
            st.session_state.options_recipie = []
        options_recipie = st.session_state.find_recipie

        # Add portion control for recipes
        recipe_portions = {}
        if len(options_recipie) > 0:
            st.markdown("##### Recipe portions")
            st.caption("Specify portion sizes for selected recipes (1.0 = full portion, 0.5 = half portion)")
            for recipe_name in options_recipie:
                portion_key = f"portion_{recipe_name.replace(' ', '_')}"
                recipe_portions[recipe_name] = st.number_input(
                    f"Portion of {recipe_name}", 
                    min_value=0.05, 
                    max_value=10.0, 
                    value=1.0, 
                    step=0.05,
                    key=portion_key,
                    help=f"Enter portion size for {recipe_name} (e.g., 0.5 for half portion)"
                )

        st.markdown("#### Add food items")
        st.caption("_:blue[Type in food items]_ that you want to add to your meal")  
        df_food_db = fetch_data_from_storage('data/livsmedelsdatabas.csv')
        food_list = df_food_db['livsmedel'].values

        st.multiselect(
            "Select food items to add to your meal",
            food_list,
            key='create_meal'
        )

        if "options" not in st.session_state:
            st.session_state.options = []
        options = st.session_state.create_meal

        st.markdown("#### Your meal")
        st.caption("This is the _:blue[ content of your meal]_")  
        
        # Combine all meal sources: recipes, individual foods, and copied meals
        temp_store = []
        df_recipies = pd.DataFrame([{"Food":'Deleted', "Amount (g)": 0.0}])
        df_meal = pd.DataFrame([{"Food":'', "Amount (g)": 0.0}])
        df_copied = get_copied_meal_items()
        
        # Add copied meal items to the meal
        if not df_copied.empty:
            copied_name = st.session_state.selected_previous_meal['name']
            options_string = f"{copied_name}/"
            for _, item in df_copied.iterrows():
                temp_store.append({"Food": item['Food'], "Amount (g)": item['Amount (g)']})
        
        # Rest of the existing recipe and food item logic...
        if (len(options) > 0) or len(options_recipie) or not df_copied.empty:
            temp_store_recipies = []
            if len(options_recipie) > 0:
                for i in range(0, len(options_recipie)):
                    df_this_recpie = df_recipie_db[df_recipie_db['name'] == options_recipie[i]]
                    portion_size = recipe_portions.get(options_recipie[i], 1.0)
                    
                    for k in range(0, len(df_this_recpie)):
                        scaled_amount = df_this_recpie['amount'].iloc[k] * portion_size
                        temp_store_recipies.append({
                            "Food": df_this_recpie['livsmedel'].iloc[k], 
                            "Amount (g)": round(scaled_amount, 1)
                        })
                    
                    if portion_size != 1.0:
                        options_string = options_string + f"{df_this_recpie['name'].iloc[0]} ({portion_size:.2f})/"
                    else:
                        options_string = options_string + df_this_recpie['name'].iloc[0] + '/'
                        
                df_recipies = pd.DataFrame(temp_store_recipies)
                
            for i in range(0, len(options)):
                temp_store.append({"Food": options[i], "Amount (g)": 0})
                options_string = options_string + options[i] + '/'
                
            df_meal = pd.DataFrame(temp_store)
            df_total = pd.concat([df_recipies, df_meal])
            df_total = df_total[df_total['Food'] != 'Deleted']
            df_result_meal = st.data_editor(df_total, key='create_meal_editor', hide_index=True, use_container_width=True)
            
            if len(df_result_meal) > 0:
                from scripts.nutritions import locate_eatables, code_detector
                df_food_nutrition = locate_eatables(df_result_meal)
                code = code_detector(df_result_meal, df_food_nutrition, 1)
                df_result_meal['code'] = code

                # Store the meal items for saving to meal database
                df_meal_items = df_result_meal[['Food', 'Amount (g)']].copy()
                
                # Add date and time columns
                from scripts.data_dashboard import datetime_to_string, time_to_string, date_time_now, time_now
                current_date = datetime_to_string(date_time_now())
                current_time = time_to_string(time_now())
                
                # Clean up options_string for meal name
                meal_name = options_string[:-1] if options_string.endswith('/') else options_string
                
                # Add columns in the correct order for CSV
                df_meal_items.insert(0, 'name', meal_name)
                df_meal_items.insert(0, 'time', current_time)
                df_meal_items.insert(0, 'date', current_date)
                
                # Rename columns to match CSV structure
                df_meal_items = df_meal_items.rename(columns={
                    'Food': 'livsmedel',
                    'Amount (g)': 'amount'
                })
                
                # Add code and favorite columns
                df_meal_items['code'] = code
                df_meal_items['favorite'] = False
                
                # Store in session state
                st.session_state.current_meal_items = df_meal_items

        else:
            st.error('Your meal is empty', icon="🚨")
            st.write('Search for food items, select recipes, or copy a previous meal.')

    with col[1]:  
        st.markdown("#### Food Registration")
        st.caption("_:blue[Register your meal]_ to the dashboard")  
        
        # Clean up options_string
        if options_string.endswith('/'):
            options_string = options_string[:-1]

        # Use the meal items from session state
        df_meal_items = st.session_state.current_meal_items

        # Call the existing form function
        create_new_form_food(code, options_string, bmr, df_meal_items)






def create_page_meal_registration():
    col = st.columns((5.5, 5.5), gap='medium') 
    df_meal_items = None  # Initialize variable to store meal composition
    code = ''  # Initialize code variable
    options_string = ''  # Initialize options_string
    
    # Initialize session state for meal items
    if "current_meal_items" not in st.session_state:
        st.session_state.current_meal_items = None
    
    with col[0]: 
        st.markdown("#### Add recipie")
        st.caption("Type in a _:blue[ recipie name]_ that you want to add to your meal")  
        df_recipie_db = fetch_data_from_storage('data/recipie_databas.csv').sort_values(['name'])
        
        recipie_list = df_recipie_db['name'].unique()

        st.multiselect(
            "Select recipies to add to your meal",
            recipie_list,
            key='find_recipie'
        )

        if "options_recipie" not in st.session_state:
            st.session_state.options_recipie = []
        options_recipie = st.session_state.find_recipie

        # Add portion control for recipes with 0.05 step increments
        recipe_portions = {}
        if len(options_recipie) > 0:
            st.markdown("##### Recipe portions")
            st.caption("Specify portion sizes for selected recipes (1.0 = full portion, 0.5 = half portion)")
            for recipe_name in options_recipie:
                portion_key = f"portion_{recipe_name.replace(' ', '_')}"
                recipe_portions[recipe_name] = st.number_input(
                    f"Portion of {recipe_name}", 
                    min_value=0.05, 
                    max_value=10.0, 
                    value=1.0, 
                    step=0.05,  # Changed to 0.05 for steps of 5
                    key=portion_key,
                    help=f"Enter portion size for {recipe_name} (e.g., 0.5 for half portion)"
                )

        st.markdown("#### Add food items")
        st.caption("_:blue[Type in food items]_ that you want to add to your meal")  
        df_food_db = fetch_data_from_storage('data/livsmedelsdatabas.csv')
        food_list = df_food_db['livsmedel'].values

        st.multiselect(
            "Select food items to add to your meal",
            food_list,
            key='create_meal'
        )

        if "options" not in st.session_state:
            st.session_state.options = []
        options = st.session_state.create_meal

        st.markdown("#### Your meal")
        st.caption("This is the _:blue[ content of your meal]_")  
        temp_store = []
        df_recipies = pd.DataFrame([{"Food":'Deleted', "Amount (g)": 0.0}])
        df_meal = pd.DataFrame([{"Food":'', "Amount (g)": 0.0}])
        
        if (len(options) > 0) or len(options_recipie):
            temp_store_recipies = []
            if len(options_recipie) > 0:
                for i in range(0, len(options_recipie)):
                    df_this_recpie = df_recipie_db[df_recipie_db['name'] == options_recipie[i]]
                    # Get the portion size for this recipe
                    portion_size = recipe_portions.get(options_recipie[i], 1.0)
                    
                    for k in range(0, len(df_this_recpie)):
                        # Apply portion scaling to the recipe amounts
                        scaled_amount = df_this_recpie['amount'].iloc[k] * portion_size
                        temp_store_recipies.append({
                            "Food": df_this_recpie['livsmedel'].iloc[k], 
                            "Amount (g)": round(scaled_amount, 1)
                        })
                    
                    # Update options_string with proper 2-decimal formatting
                    if portion_size != 1.0:
                        options_string = options_string + f"{df_this_recpie['name'].iloc[0]} ({portion_size:.2f})/"
                    else:
                        options_string = options_string + df_this_recpie['name'].iloc[0] + '/'
                        
                df_recipies = pd.DataFrame(temp_store_recipies)
                
            for i in range(0, len(options)):
                temp_store.append({"Food": options[i], "Amount (g)": 0})
                options_string = options_string + options[i] + '/'
                
            df_meal = pd.DataFrame(temp_store)
            df_total = pd.concat([df_recipies, df_meal])
            df_total = df_total[df_total['Food'] != 'Deleted']
            df_result_meal = st.data_editor(df_total, key='create_meal_editor', hide_index=True, use_container_width=True)
            
            if len(df_result_meal) > 0:
                df_food_nutrition = locate_eatables(df_result_meal)
                code = code_detector(df_result_meal, df_food_nutrition, 1)
                df_result_meal['code'] = code

                # Store the meal items for saving to meal database
                # Add the meal name column and prepare for saving
                df_meal_items = df_result_meal[['Food', 'Amount (g)']].copy()
                
                # Add date and time columns
                current_date = datetime_to_string(date_time_now())
                current_time = time_to_string(time_now())
                
                # Clean up options_string for meal name (remove trailing slash)
                meal_name = options_string[:-1] if options_string.endswith('/') else options_string
                
                # Add columns in the correct order for CSV
                df_meal_items.insert(0, 'name', meal_name)
                df_meal_items.insert(0, 'time', current_time)
                df_meal_items.insert(0, 'date', current_date)
                
                # Rename columns to match CSV structure
                df_meal_items = df_meal_items.rename(columns={
                    'Food': 'livsmedel',
                    'Amount (g)': 'amount'
                })
                
                # Add code and favorite columns
                df_meal_items['code'] = code
                df_meal_items['favorite'] = False  # Default to False, will be updated in form
                
                # Store in session state so it persists across reruns
                st.session_state.current_meal_items = df_meal_items

        else:
            st.error('Your meal is empty', icon="🚨")
            st.write('Search for food items to add to your meal.')

    with col[1]:  
        st.markdown("#### Food Registration")
        st.caption("_:blue[Register your meal]_ to the dashboard")  
        # Clean up options_string
        if options_string.endswith('/'):
            options_string = options_string[:-1]

        # Use the meal items from session state
        df_meal_items = st.session_state.current_meal_items

        # Call the modified form function with meal items
        create_new_form_food(code, options_string, bmr, df_meal_items)


def create_page_database():
    col = st.columns((5.0, 5.0, 5.0), gap='medium') 
    with col[0]: 
        st.markdown("#### Add food item")
        st.caption("_:blue[Add new food item]_ to the database")  
        create_form_add_food_item_to_database()
    with col[1]: 
        st.markdown("#### Search for food items")
        st.caption("_:blue[Type in food items]_ that you want to add to your recipie")  
        df_food_db = fetch_data_from_storage('data/livsmedelsdatabas.csv')
        food_list = df_food_db['livsmedel'].values
        
        st.multiselect(
            "Select food items to your recipie",
            food_list,
            key='add_meal'
        )

        if "options_database" not in st.session_state:
            st.session_state.options_database = []
        options_database = st.session_state.add_meal

        st.markdown("#### Create recipie")
        portions = st.slider("Amount of portions", 1, 30, 1)
        st.write("Portions: ", portions)
        st.caption("This is the _:blue[ content of your recipie]_")  
        temp_store_database = []
        code = ''
        meal_df = pd.DataFrame([{}])
        if len(options_database) > 0:
            for i in range(0, len(options_database)):
                temp_store_database.append({"Food": options_database[i], "Amount (g)": 0})
            df_my = pd.DataFrame(temp_store_database)
            meal_df = st.data_editor(df_my, key='add_meal_editor', hide_index=True, use_container_width=True)
            if len(meal_df) > 0:
                df_food_nutrition = locate_eatables(meal_df)
                code = code_detector(meal_df, df_food_nutrition, portions)
                meal_df['code'] = code
        else:
            st.error('Your recipie is empty', icon="🚨")
            st.write('Serach for food items to add to your recipie.')
    with col[2]:
        st.markdown("#### Save recipie")
        st.caption("_:blue[Save your recipie]_ to the database")  
        create_form_add_recipie_to_database(meal_df, code)   


def create_page_logg_book():
    col = st.columns((5.0, 8.0), gap='medium') 
    with col[0]: 
        st.markdown("#### Recipies in database")
        st.caption("These are the stored _:blue[ recipies in your database]_")  
        df_meal_db = fetch_data_from_storage('data/recipie_databas.csv')
        summary = df_meal_db.groupby(['name', 'code']).count().sort_values(['favorite', 'name'])
        for i in range(0, len(summary)):
            this_meal = df_meal_db[df_meal_db['name'] == summary.index[i][0]]
            if this_meal['favorite'].iloc[0] == True:
                this_icon = '⭐️'
            else:
                this_icon = '🍲'
            expander = st.expander(summary.index[i][0], icon=this_icon)
            this_code = this_meal['code'].iloc[0]
            expander.write("_**Meal code**_: :green[" + this_code + "]")
            expander.write("_**Ingredients:**_ \n")
            for j in range(0, len(this_meal)):
                expander.write(':violet[' + "     -- " + this_meal['livsmedel'].iloc[j] + ' ] ' +  '   (_' + str(this_meal['amount'].iloc[j])+ "_ g)") 
    with col[1]: 
        st.markdown('#### Delete registered post')  
        st.caption("_:blue[Select registrations]_ that you aim to _:blue[delete]_")
        selected_date_delete = datetime_to_string(selected_date_input)
        df_energy_date = df_energy[df_energy['date'] == selected_date_delete]
        if len(df_energy_date) != 0:            
            df_activity_irl = add_summary_to_dataset(df_energy_date)
        if len(df_energy_date) > 0:
            row_insert = len(df_activity_irl) * [False]
            df_activity_irl.insert(0, 'delete', row_insert)
            df_activity_show = df_activity_irl[['delete', 'time', 'summary']]
            edited_df = st.data_editor(
                df_activity_show, 
                column_config={
                    "time": st.column_config.Column(
                        "Time",
                        width="small",
                        required=True,
                    ),
                    "summary": st.column_config.Column(
                        "Summary",
                        width="large",
                        required=True,
                    ),
                    "delete": st.column_config.Column(
                        "Delete",
                        width="small",
                        required=True,
                    ),
                },
                key='change_registration_logg', 
                hide_index=True, 
                use_container_width=True)

            button_pressed = st.button("Delete item", key="button_reg_logg")
            if button_pressed:
                df_drop = edited_df[edited_df.delete == True]
                for i in range(0, len(df_drop)):
                    drop_time = df_drop['time'].iloc[i]
                    drop_summary = df_drop['summary'].iloc[i]
                    for j in range(0, len(df_activity_irl)):
                        df_acrtivity_time = df_activity_irl['time'].iloc[j]
                        df_acrtivity_summary = df_activity_irl['summary'].iloc[j]
                        if (df_acrtivity_time == drop_time) and (df_acrtivity_summary == drop_summary):
                            df_activity_irl = df_activity_irl[df_activity_irl['time'] != drop_time]
                            break
                df_new = df_activity_irl.drop(['delete'], axis=1)
                delete_item_from_dataset(selected_date_delete, df_new, bmr)
                st.rerun()

        st.markdown('#### Delete recipies in database')  
        st.caption("_:blue[Select recipie]_ that you aim to _:blue[delete]_")
        df_meal_db = fetch_data_from_storage('data/recipie_databas.csv')
        df_names_recipies = df_meal_db.groupby(['name']).count().reset_index()
        if len(df_names_recipies) > 0:
            recipies_list = df_names_recipies['name'].values
            selected_recipie = st.selectbox("Select a recipie", recipies_list, key='recipie_delete_selector')
            
            st.checkbox("Delete recipie", key="button_delete_recipie_logg")
            st.checkbox("Change recipie", key="button_change_recipie_logg")

            if "delete_recipie" not in st.session_state:
                st.session_state.delete_recipie = False
            delete_recipie = st.session_state.button_delete_recipie_logg
            
            if "change_recipie" not in st.session_state:
                st.session_state.change_recipie = False
            change_recipie = st.session_state.button_change_recipie_logg

            def submit_delete():
                st.session_state.button_delete_recipie_logg = False
                save_data_to_storage(df_meal_db_update, 'data/recipie_databas.csv')
            
            def submit_change():
                st.session_state.button_change_recipie_logg = False
                df_meal_db_update_change = df_meal_db[df_meal_db['name'] != selected_recipie]
                df_add_update = pd.concat([df_meal_db_update_change, edited_df_recipie])
                save_data_to_storage(df_add_update, 'data/recipie_databas.csv')

            if delete_recipie:
                df_meal_db_update = df_meal_db[df_meal_db['name'] != selected_recipie]
                button_pressed_delete_save = st.button("Save changes", key="button_save_delete_logg", on_click=submit_delete)
                if button_pressed_delete_save:  
                    st.rerun()

            if change_recipie:
                df_meal_db_change = df_meal_db[df_meal_db['name'] == selected_recipie]
                if len(df_meal_db_change) > 0:
                    df_recipie_show = df_meal_db_change[['livsmedel', 'amount']]
                    edited_df_recipie = st.data_editor(
                        df_recipie_show, 
                        column_config={
                            "livsmedel": st.column_config.Column(
                                "Food",
                                width="large",
                                required=True,
                            ),
                            "amount": st.column_config.Column(
                                "Amount (g)",
                                width="small",
                                required=True,
                            ),
                        },
                        key='change_recipie_logg', 
                        hide_index=True, 
                        use_container_width=True)
                if len(edited_df_recipie) > 0:
                    edited_df_recipie = edited_df_recipie.rename(columns={"livsmedel": "Food", "amount": "Amount (g)"})
                    df_food_nutrition = locate_eatables(edited_df_recipie)
                    code = code_detector(edited_df_recipie, df_food_nutrition, 1)
                    edited_df_recipie['code'] = code
                    edited_df_recipie['name'] = selected_recipie
                    edited_df_recipie['favorite'] = df_meal_db_change['favorite'].iloc[0]
                    edited_df_recipie = edited_df_recipie.rename(columns={"Food": "livsmedel", "Amount (g)": "amount"})
                    edited_df_recipie = edited_df_recipie[['name', 'livsmedel', 'amount', 'code', 'favorite']]
                    st.button("Save changes", key="button_save_change_logg", on_click=submit_change)
        else:
            st.caption("There are _:blue[no recipies]_ saved in your database")
        
            
with st.sidebar:
    st.image("zeus_logo_test.png")

    # Storage method indicator
    storage_method = "🗄️ Database (Supabase)" if USE_DATABASE else "📄 CSV Files"
    st.caption(f"Storage: {storage_method}")
    
    # Expandable User Settings Section
    with st.expander("⚙️ User Settings", expanded=False):
        weight = st.number_input(
            "Weight (kg)", 
            min_value=30.0, 
            max_value=300.0, 
            value=50.0, 
            step=0.5,
            help="Enter your weight in kilograms"
        )
        
        height = st.number_input(
            "Height (cm)", 
            min_value=100.0, 
            max_value=250.0, 
            value=170.0, 
            step=0.5,
            help="Enter your height in centimeters"
        )
        
        age = st.number_input(
            "Age (years)", 
            min_value=10, 
            max_value=100, 
            value=43, 
            step=1,
            help="Enter your age in years"
        )
        
        # Calculate BMR with the user inputs
        bmr = calc_bmr(weight, height, age)
        
        # Display calculated BMR to user
        st.success(f"Your calculated basal energy need is **{bmr} kcal per day**")
        st.caption("This is the energy your body needs at rest for basic functions.")
    
    # Date selection
    st.markdown("#### Date Selection")
    date_now = date_time_now()  
    selected_date_input = st.date_input("Select a date", date_now, key='head_selector') 
    selected_date = datetime_to_string(selected_date_input)
    
    # Navigation
    st.markdown("#### Navigation")
    page_names_to_funcs = {
        "Dashboard": create_dashobard,
        "Activity": create_page_activity_registration,
        "Meals": create_page_meal_registration_with_copy,
        "Database": create_page_database,
        "Log book": create_page_logg_book
    }

demo_name = st.sidebar.selectbox("Select a page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()
 