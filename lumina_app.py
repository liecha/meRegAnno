import streamlit as st
import pandas as pd
import datetime
import altair as alt
import io

# ===================== IMPORT NEW MODULES =====================
from scripts.validation import validate_bmr_parameters, display_validation_results
from scripts.error_handling import (
    error_handler, handle_errors, error_context, loading_indicator,
    show_error_state, safe_dataframe_operation
)
from scripts.state_management import (
    init_state, get_user_settings, update_user_settings, 
    show_notifications, clear_all_notifications, state_manager
)
from scripts.ui_components import create_data_table
from scripts.constants import APP_NAME, APP_ICON, get_table_config

# Import existing modules with error handling
try:
    from scripts.data_storage import fetch_data_from_storage, save_data_to_storage, delete_item_from_dataset
    import scripts.data_storage as ds

    from scripts.data_dashboard import calc_bmr, date_time_now, time_now, time_to_string, datetime_to_string
    from scripts.data_dashboard import translate_dates_to_text, calc_daily_energy_output, calc_energy_deficite
    from scripts.data_dashboard import nutrition_content, nutrition_differ, add_summary_to_dataset 
    from scripts.data_dashboard import energy_differ, energy_balance_at_current_time

    from scripts.nutritions import locate_eatables, code_detector 
except ImportError as e:
    st.error(f"Failed to import required modules: {e}")
    st.stop()

# Import ALL original forms with improvements
from scripts.forms import (
    create_new_form_activity, create_new_form_food, create_form_add_recipie_to_database,
    create_form_add_food_item_to_database, create_copy_previous_meal_section, get_copied_meal_items
)

from scripts.activity_summary import (
    filter_data_by_period, get_training_summary, get_food_summary,
    create_training_chart, create_weekly_summary_chart, create_improved_energy_balance_chart, get_available_activities, 
    format_time_period, get_activity_colors
)

# ===================== DATA STORAGE CONFIGURATION =====================
USE_DATABASE = False  # Set this to True to use Supabase database, False to use CSV files
ds.USE_DATABASE = USE_DATABASE

# ===================== APP CONFIGURATION =====================
st.set_page_config(
    page_title=APP_NAME,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize state management
init_state()

# CSS styling - SAME AS ORIGINAL
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
    
    /* Improved styling for validation messages */
    .stAlert > div {
        padding: 0.5rem 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# ===================== DATA LOADING WITH ERROR HANDLING =====================
@handle_errors("data loading", show_user_error=True, fallback_value=pd.DataFrame())
def load_energy_data():
    """Load energy data with error handling"""
    with loading_indicator("Loading energy data..."):
        return fetch_data_from_storage('data/updated-database-results.csv')

# Load main data
df_energy = load_energy_data()

# ===================== MAIN HEADER =====================
st.subheader('Emelie Chandni Jutvik')

# Show any pending notifications
show_notifications()

# ===================== IMPROVED SIDEBAR WITH VALIDATION =====================
with st.sidebar:
    st.image("lumina_1.png")

    # Storage method indicator - SAME AS ORIGINAL
    storage_method = "🗄️ Database (Supabase)" if USE_DATABASE else "📄 CSV Files"
    st.caption(f"Storage: {storage_method}")
    
    # Expandable User Settings Section with Validation - ENHANCED
    with st.expander("⚙️ User Settings", expanded=False):
        current_settings = get_user_settings()
        
        weight = st.number_input(
            "Weight (kg)", 
            min_value=30.0, 
            max_value=300.0, 
            value=current_settings.get('weight', 50.0), 
            step=0.5,
            help="Enter your weight in kilograms"
        )
        
        height = st.number_input(
            "Height (cm)", 
            min_value=100.0, 
            max_value=250.0, 
            value=current_settings.get('height', 170.0), 
            step=0.5,
            help="Enter your height in centimeters"
        )
        
        age = st.number_input(
            "Age (years)", 
            min_value=10, 
            max_value=100, 
            value=current_settings.get('age', 43), 
            step=1,
            help="Enter your age in years"
        )
        
        # Validate BMR parameters - NEW
        bmr_validation = validate_bmr_parameters(weight, height, age)
        display_validation_results(bmr_validation, show_warnings=True)
        
        if not bmr_validation.has_errors():
            # Calculate BMR - SAME AS ORIGINAL
            bmr = calc_bmr(weight, height, age)
            
            # Update user settings in state - NEW
            update_user_settings(weight=weight, height=height, age=age, bmr=bmr)
            
            # Display calculated BMR - ENHANCED
            st.success(f"Your calculated basal energy need is **{bmr} kcal per day**")
            st.caption("This is the energy your body needs at rest for basic functions.")
        else:
            st.error("Please correct the user settings to calculate BMR")
            bmr = current_settings.get('bmr', 1187)  # Fallback value
    
    # Date selection - SAME AS ORIGINAL
    st.markdown("#### Date Selection")
    date_now = date_time_now()  
    selected_date_input = st.date_input("Select a date", date_now, key='head_selector') 
    selected_date = datetime_to_string(selected_date_input)
    
    # Navigation - SAME AS ORIGINAL
    st.markdown("#### Navigation")

# ===================== ALL ORIGINAL PAGE FUNCTIONS WITH ENHANCEMENTS =====================

@handle_errors("dashboard creation")
def create_dashobard():  # Keeping original function name
    """ORIGINAL dashboard function with error handling enhancements"""
    state_manager.set_page('Dashboard')
    
    col = st.columns((5.5, 5.5), gap='medium') 
    with col[0]: 
        # All original dashboard logic with error handling
        current_date, text_month, text_weekday = translate_dates_to_text(selected_date)
        df_energy_date = safe_dataframe_operation(
            df_energy, 
            lambda df: df[df['date'] == selected_date],
            fallback_df=pd.DataFrame()
        )
        
        sum_energy_output = calc_daily_energy_output(df_energy_date, bmr)
        df_deficite = calc_energy_deficite(df_energy, selected_date, selected_date_input)
        deficite_string = ''
        seven_days_deficite_sum = 0
        
        if len(df_deficite) > 0:
            seven_days_deficite_sum = sum(df_deficite['energy_acc'].values[1:])
            for i in range(0, len(df_deficite)):
                deficite_string = deficite_string + str(int(df_deficite['energy_acc'].iloc[i])) + ', '
            deficite_string = deficite_string[:-2]
        
        if len(df_energy_date) != 0:
            # NUTRITION - SAME AS ORIGINAL
            df_nutrition_acc = nutrition_content(df_energy_date)
            df_nutritions_labeled = nutrition_differ(df_energy_date)
            
            # ACTIVITY - SAME AS ORIGINAL
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
                
                # Using improved table component
                create_data_table(
                    df_deficite_show,
                    {
                        "date_text": st.column_config.Column("Day", width="small", required=True),
                        "energy_acc": st.column_config.Column("Deficite (kcal/day)", width="small", required=True),
                    },
                    'energy_deficite'
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
                    
                    # Using improved table component
                    create_data_table(
                        df_activity_irl,
                        get_table_config('activity_summary'),
                        'change_registration'
                    )
                
                st.caption("_:blue[Nutrition intake]_ for registered meals at selected day")
                st.bar_chart(df_nutritions_labeled, x="time", y="nutrient", color="label")

@handle_errors("activity registration page")
def create_page_activity_registration():
    """ORIGINAL activity registration with improvements"""
    state_manager.set_page('Activity')
    
    col = st.columns((5.5, 5.5), gap='medium') 
    df_energy_date = safe_dataframe_operation(
        df_energy, 
        lambda df: df[df['date'] == selected_date],
        fallback_df=pd.DataFrame()
    )
    
    if len(df_energy_date) != 0:            
        df_activity_irl = add_summary_to_dataset(df_energy_date)
    
    with col[0]:  
        st.markdown('#### Stored activities') 
        if len(df_energy_date) != 0:
            if len(df_energy_date) > 0:
                df_activity_irl = df_activity_irl[['time', 'summary']]
                
                # Using improved table component
                create_data_table(
                    df_activity_irl,
                    get_table_config('activity_summary'),
                    'stored_activities'
                )
                
                st.caption("_:blue[Stored activities]_ from selected day in _:blue[real time]_")
                st.bar_chart(df_energy_date, x="time", y="energy", color="activity") 
        else:
             st.caption("There are _:blue[no stored activities]_ at selected day") 
    
    with col[1]:
        st.markdown("#### Create new activity")
        # USING IMPROVED FORM WITH VALIDATION
        create_new_form_activity(bmr)

@handle_errors("meal registration page")  
def create_page_meal_registration_with_copy():
    """ORIGINAL meal registration with copy functionality and improvements"""
    state_manager.set_page('Meals')
    
    col = st.columns((5.5, 5.5), gap='medium') 
    df_meal_items = None
    code = ''
    options_string = ''
    
    # Initialize session state for meal items - SAME AS ORIGINAL
    if "current_meal_items" not in st.session_state:
        st.session_state.current_meal_items = None
    
    with col[0]: 
        # Add the copy previous meal section - SAME AS ORIGINAL
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

        # Add portion control for recipes - SAME AS ORIGINAL
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
        
        # Combine all meal sources: recipes, individual foods, and copied meals - ENHANCED
        temp_store = []
        df_recipies = pd.DataFrame([{"Food":'Deleted', "Amount (g)": 0.0}])
        df_meal = pd.DataFrame([{"Food":'', "Amount (g)": 0.0}])
        df_copied = get_copied_meal_items()
        
        # Add copied meal items to the meal - SAME AS ORIGINAL
        if not df_copied.empty:
            copied_name = st.session_state.selected_previous_meal['name']
            options_string = f"{copied_name}/"
            for _, item in df_copied.iterrows():
                temp_store.append({"Food": item['Food'], "Amount (g)": item['Amount (g)']})
        
        # Rest of the existing recipe and food item logic - SAME AS ORIGINAL
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
                df_food_nutrition = locate_eatables(df_result_meal)
                code = code_detector(df_result_meal, df_food_nutrition, 1)
                df_result_meal['code'] = code

                # Store the meal items for saving to meal database - SAME AS ORIGINAL
                df_meal_items = df_result_meal[['Food', 'Amount (g)']].copy()
                
                # Add date and time columns - SAME AS ORIGINAL
                current_date = datetime_to_string(date_time_now())
                current_time = time_to_string(time_now())
                
                # Clean up options_string for meal name - SAME AS ORIGINAL
                meal_name = options_string[:-1] if options_string.endswith('/') else options_string
                
                # Add columns in the correct order for CSV - SAME AS ORIGINAL
                df_meal_items.insert(0, 'name', meal_name)
                df_meal_items.insert(0, 'time', current_time)
                df_meal_items.insert(0, 'date', current_date)
                
                # Rename columns to match CSV structure - SAME AS ORIGINAL
                df_meal_items = df_meal_items.rename(columns={
                    'Food': 'livsmedel',
                    'Amount (g)': 'amount'
                })
                
                # Add code and favorite columns - SAME AS ORIGINAL
                df_meal_items['code'] = code
                df_meal_items['favorite'] = False
                
                # Store in session state - SAME AS ORIGINAL
                st.session_state.current_meal_items = df_meal_items

        else:
            st.error('Your meal is empty', icon="🚨")
            st.write('Search for food items, select recipes, or copy a previous meal.')

    with col[1]:  
        st.markdown("#### Food Registration")
        st.caption("_:blue[Register your meal]_ to the dashboard")  
        
        # Clean up options_string - SAME AS ORIGINAL
        if options_string.endswith('/'):
            options_string = options_string[:-1]

        # Use the meal items from session state - SAME AS ORIGINAL
        df_meal_items = st.session_state.current_meal_items

        # Call the IMPROVED form function with validation
        create_new_form_food(code, options_string, bmr, df_meal_items)

@handle_errors("database page")
def create_page_database():
    """Database page with improved 2-column layout"""
    state_manager.set_page('Database')
    
    # Changed from 3 columns to 2 columns
    col = st.columns((5.0, 10.0), gap='medium') 
    
    # FIRST COLUMN: Add food item (unchanged)
    with col[0]: 
        st.markdown("#### Add food item")
        st.caption("_:blue[Add new food item]_ to the database")  
        create_form_add_food_item_to_database()
    
    # SECOND COLUMN: Recipe creation workflow (spans what used to be columns 2 and 3)
    with col[1]: 
        # Search for food items section
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

        # Create recipe section
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
            st.write('Search for food items to add to your recipie.')
        
        # Save recipe section (now spans the full width of the second column)
        st.markdown("#### Save recipie")
        st.caption("_:blue[Save your recipie]_ to the database")  
        create_form_add_recipie_to_database(meal_df, code)

@handle_errors("log book page")
def create_page_logg_book():
    """ORIGINAL log book page with improvements"""
    state_manager.set_page('Log book')
    
    col = st.columns((5.0, 8.0), gap='medium') 
    with col[0]: 
        st.markdown("#### Recipies in database")
        st.caption("These are the stored _:blue[ recipies in your database]_")  
        df_meal_db = fetch_data_from_storage('data/recipie_databas.csv')
        summary = df_meal_db.groupby(['name', 'code']).count().sort_values(['favorite', 'name'])
        for i in range(0, len(summary)):
            this_meal = df_meal_db[df_meal_db['name'] == summary.index[i][0]]
            if this_meal['favorite'].iloc[0] == True:
                this_icon = '⭐'
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
            
            # Using improved table component
            edited_df = create_data_table(
                df_activity_show,
                {
                    "time": st.column_config.Column("Time", width="small", required=True),
                    "summary": st.column_config.Column("Summary", width="large", required=True),
                    "delete": st.column_config.Column("Delete", width="small", required=True),
                },
                'change_registration_logg'
            )

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

        # REST OF LOG BOOK FUNCTIONALITY - SAME AS ORIGINAL
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
                    
                    # Using improved table component
                    edited_df_recipie = create_data_table(
                        df_recipie_show,
                        {
                            "livsmedel": st.column_config.Column("Food", width="large", required=True),
                            "amount": st.column_config.Column("Amount (g)", width="small", required=True),
                        },
                        'change_recipie_logg'
                    )
                
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

@handle_errors("summary page")
def create_page_summary():
    """Training-focused summary page with improved layout and progress tracking"""
    state_manager.set_page('Summary')
    
    # Single column layout - stacked sections
    st.markdown('### Training Summary & Progress')
    st.caption("Overview of your training activities and progress over time (excluding walking)")
    
    # CONTROLS SECTION
    st.markdown('#### Period & Activity Controls')
    
    # Create three columns for controls
    control_col1, control_col2, control_col3 = st.columns(3)
    
    with control_col1:
        # Period selection
        period_type = st.selectbox(
            "Time Period", 
            ["Week", "Month", "Day"],
            key='summary_period'
        )
    
    with control_col2:
        # Date selection - reuse the existing selected_date from sidebar
        period_display = format_time_period(period_type, selected_date_input)
        st.write(f"**Selected Period:**")
        st.caption(f"{period_display}")
    
    with control_col3:
        # Activity selection - EXCLUDE WALKING by default for training focus
        available_activities = get_available_activities(df_energy)
        # Remove 'Walk' from available activities for training focus
        training_activities = [act for act in available_activities]
        
        selected_activities = st.multiselect(
            "Training Activities",
            training_activities,
            default=training_activities,  # Select all training activities except walking
            key='summary_activities'
        )
    
    st.markdown("---")
    
    # Filter data based on period
    filtered_df = filter_data_by_period(df_energy, period_type, selected_date_input)
    
    # TRAINING ACTIVITIES SECTION
    st.markdown('#### Activity Overview')
    
    # Get training summary
    training_summary = get_training_summary(filtered_df, selected_activities)
    
    if not training_summary.empty:
        # Key metrics in columns
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        total_sessions = training_summary['Sessions'].sum()
        total_distance = training_summary['Total Distance (km)'].sum()
        total_energy_burned = training_summary['Total Energy (kcal)'].sum()
        total_duration = training_summary['Total Duration (min)'].sum()
        
        metric_col1.metric("Total Sessions", total_sessions)
        metric_col2.metric("Total Distance", f"{total_distance:.1f} km")
        metric_col3.metric("Energy Burned", f"{int(total_energy_burned)} kcal")
        metric_col4.metric("Total Duration", f"{int(total_duration)} min")
        
        # Simplified activity breakdown table - only requested columns
        st.markdown("##### Activity Breakdown")
        
        # Format the summary for display with only requested columns
        display_summary = training_summary.copy()
        display_summary['Total Distance (km)'] = display_summary['Total Distance (km)'].round(2)
        display_summary['Total Duration (min)'] = display_summary['Total Duration (min)'].round(0)
        display_summary['Avg Pace (min/km)'] = display_summary['Avg Pace (min/km)'].round(2)
        
        # Select only the columns you requested in the specified order
        columns_to_show = [
            'activity', 'Sessions', 'Total Distance (km)', 'Total Energy (kcal)', 
            'Avg Energy (kcal)', 'Total Duration (min)', 'Avg Pace (min/km)', 
            'Total Steps', 'Sample Note'
        ]
        
        # Filter to only show existing columns
        available_columns = [col for col in columns_to_show if col in display_summary.columns]
        simplified_summary = display_summary[available_columns]
        
        # Create simplified table with only requested columns
        create_data_table(
            simplified_summary,
            {
                "activity": st.column_config.Column("Activity", width="small"),
                "Sessions": st.column_config.Column("Sessions", width="small"),
                "Total Distance (km)": st.column_config.Column("Distance (km)", width="small"),
                "Total Energy (kcal)": st.column_config.Column("Energy (kcal)", width="small"),
                "Avg Energy (kcal)": st.column_config.Column("Avg Energy", width="small"),
                "Total Duration (min)": st.column_config.Column("Duration (min)", width="small"),
                "Avg Pace (min/km)": st.column_config.Column("Pace", width="small"),
                "Total Steps": st.column_config.Column("Steps", width="small"),
                "Sample Note": st.column_config.Column("Notes", width="medium"),
            },
            'training_summary_table'
        )
        
        # Training insights
        st.markdown("##### Training Insights")
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            # Most frequent activity
            most_frequent = training_summary.loc[training_summary['Sessions'].idxmax()]
            st.info(f"**Most Frequent:** {most_frequent['activity']} ({most_frequent['Sessions']} sessions)")
            
            # Highest energy activity
            if training_summary['Total Energy (kcal)'].max() > 0:
                highest_energy = training_summary.loc[training_summary['Total Energy (kcal)'].idxmax()]
                st.info(f"**Highest Energy:** {highest_energy['activity']} ({int(highest_energy['Total Energy (kcal)'])} kcal)")
        
        with insight_col2:
            # Longest distance activity
            distance_activities = training_summary[training_summary['Total Distance (km)'] > 0]
            if not distance_activities.empty:
                longest_distance = distance_activities.loc[distance_activities['Total Distance (km)'].idxmax()]
                st.info(f"**Longest Distance:** {longest_distance['activity']} ({longest_distance['Total Distance (km)']:.1f} km)")
            
            # Average session duration
            avg_session_duration = total_duration / total_sessions if total_sessions > 0 else 0
            st.info(f"**Avg Session:** {int(avg_session_duration)} minutes")
        
    else:
        st.warning("No training data available for the selected period and activities.")
        st.info("Try selecting a different time period or ensure you have logged training activities.")
    
    st.markdown("---")
    
    # VISUALIZATIONS SECTION (EXACTLY AS YOU REQUESTED)
    st.markdown('#### Training Visualizations')
    
    # Chart type selection
    chart_type = st.selectbox(
        "Select chart type",
        ["Energy Balance", "Energy Burned", "Distance", "Weekly Distribution"],
        key='chart_type'
    )
    
    # Create charts
    if chart_type == "Energy Burned":
        chart = create_training_chart(filtered_df, selected_activities, "energy")
        st.altair_chart(chart, use_container_width=True)
        
    elif chart_type == "Distance":
        chart = create_training_chart(filtered_df, selected_activities, "distance")
        st.altair_chart(chart, use_container_width=True)
        
    elif chart_type == "Weekly Distribution":
        chart = create_weekly_summary_chart(filtered_df, selected_activities)
        st.altair_chart(chart, use_container_width=True)
        
    elif chart_type == "Energy Balance":
        # IMPROVED: Line chart for energy balance instead of bars
        chart = create_improved_energy_balance_chart(filtered_df)
        st.altair_chart(chart, use_container_width=True)
    
    # Progress tracking suggestions
    if training_summary.empty:
        st.markdown("---")
        st.markdown("##### Getting Started with Training Tracking")
        st.info("""
        **To build a comprehensive training overview:**
        - Log your training sessions regularly (Run, Bike, Swim, Strength, Yoga)
        - Include distance, duration, and energy burned when possible
        - Use different time periods (Week/Month) to see progress trends
        - Track consistency by reviewing weekly distributions
        """)

# ===================== NAVIGATION SETUP - SAME AS ORIGINAL =====================
page_names_to_funcs = {
    "Dashboard": create_dashobard,  # Keeping original function name
    "Activity": create_page_activity_registration,
    "Meals": create_page_meal_registration_with_copy,
    "Database": create_page_database,
    "Log book": create_page_logg_book,
    "Summary": create_page_summary
}

# ===================== MAIN APP EXECUTION =====================
try:
    # Get selected page - SAME AS ORIGINAL
    demo_name = st.sidebar.selectbox("Select a page", page_names_to_funcs.keys())
    
    # Clear old notifications if changing pages - NEW
    current_page = state_manager.get_state('navigation', 'current_page')
    if current_page != demo_name:
        clear_all_notifications()
    
    # Execute selected page function - SAME AS ORIGINAL
    page_names_to_funcs[demo_name]()

except Exception as e:
    error_handler.show_user_error(e, "main app execution")
    st.error("A critical error occurred. Please refresh the page.")
    
    # Show error diagnostics in debug mode - NEW
    if st.sidebar.checkbox("Show Error Diagnostics", key="show_diagnostics"):
        from scripts.error_handling import show_error_diagnostics
        show_error_diagnostics()

# ===================== SIDEBAR FOOTER - ENHANCED =====================
with st.sidebar:
    
    # Show form state indicators - NEW
    form_states = []
    if state_manager.is_form_dirty('activity_form'):
        form_states.append("Activity form has unsaved changes")
    if state_manager.is_form_dirty('food_form'):
        form_states.append("Food form has unsaved changes")
    
    if form_states:
        st.warning("Unsaved changes:")
        for state_msg in form_states:
            st.caption(f"🔄 {state_msg}")
