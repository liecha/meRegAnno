# Import libraries
import streamlit as st
import pandas as pd
import datetime
import altair as alt
from streamlit_autorefresh import st_autorefresh

import io

from scripts.data_storage import delete_item_from_dataset

from scripts.data_dashboard import date_time_now
from scripts.data_dashboard import datetime_to_string
from scripts.data_dashboard import text_dates
from scripts.data_dashboard import calc_bmr
from scripts.data_dashboard import energy_differ
from scripts.data_dashboard import calc_daily_energy_output
from scripts.data_dashboard import energy_balance_at_current_time
from scripts.data_dashboard import nutrition_content
from scripts.data_dashboard import nutrition_differ
from scripts.data_dashboard import add_summary_to_dataset 

from scripts.nutritions import locate_eatables
from scripts.nutritions import code_detector

from scripts.forms import create_new_form_activity
from scripts.forms import create_new_form_food
from scripts.forms import create_form_add_meal
from scripts.forms import create_form_add_food_item

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

    /* breakline for metric text */
    div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
    overflow-wrap: break-word;
    white-space: break-spaces;
    color: red;
    }
    </style>
""", unsafe_allow_html=True)
#df_energy = load_data_from_db('energy_balance')
df_energy =  df_db_csv = pd.read_csv('data/updated-database-results.csv') #load_data_from_db('energy_balance')

st.caption("_User_")
st.subheader('Emelie Chandni Jutvik')

with st.sidebar:
    st.image("zeus_logo_test.png")  
    bmr = calc_bmr(50, 170, 42)
    date_now =  date_time_now()   
    selected_date_input = st.date_input("Select a date", date_now, key='head_selector')

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard",
    "🏃🏽‍♀️ Activity Registration", 
    "🍲 Meal Registration",
    "🗄️ Database",
    "📝 Logg",
    ])
with tab1:
    selected_date = datetime_to_string(selected_date_input)
    current_date, text_month, text_weekday = text_dates(selected_date)

    df_energy_date = df_energy[df_energy['date'] == selected_date]
    sum_energy_output = calc_daily_energy_output(df_energy_date, bmr)
    
    if len(df_energy_date) != 0:
        # NUTRITION
        df_nutrition_acc = nutrition_content(df_energy_date)
        df_nutritions_labeled = nutrition_differ(df_energy_date)
        
        # ACTIVITY
        df_activity_irl = add_summary_to_dataset(df_energy_date)
    
        df_energy_plot = energy_differ(df_energy_date)
        energy_in, energy_out, energy_balance, deficite_text = energy_balance_at_current_time(df_energy_date)

    col = st.columns((5.5, 5.5, 5.5), gap='medium') 
    with col[0]:                    
        if len(df_energy_date) == 0:
            st.markdown('#### Date of exploration') 
            st.caption("The selected date is _:blue[" + str(current_date) + ' ' + text_month + " (" + text_weekday + ")]_")      
        else:
            st.markdown('#### Date of exploration') 
            st.caption("The selected date is _:blue[" + str(current_date) + ' ' + text_month + " (" + text_weekday + ")]_")               
            st.markdown('#### Overview') 
            st.caption("_:blue[Energy inputs/outputs]_ at selected day")
            st.bar_chart(df_energy_plot, x="time", y="energy", color="label") 
            
            st.markdown('#### Registration list')  
            st.caption("_:blue[Stored registrations]_ from selected day in _:blue[real time]_")
            if len(df_energy_date) > 0:
                df_activity_irl = df_activity_irl[['time', 'summary']]
                edited_df = st.data_editor(
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
                    use_container_width=True)
 
                            
    with col[1]:
        if len(df_energy_date) == 0:
            st.markdown('#### Basal metabolic rate') 
            st.caption("Your body requires _:blue[" + str(bmr) + " kcal]_ at rest")
            
            st.markdown('#### Activity')  
            st.caption("There is _:blue[no data available]_ for the selected day")

            st.markdown('#### Current energy balance') 
            st.caption("There is _:blue[no data available]_ for the selected day")
        else:
            st.markdown('#### Basal metabolic rate') 
            st.caption("Your body requires _:blue[" + str(bmr) + " kcal]_ at rest")
            
            st.markdown('#### Activity')  
            st.caption("_:blue[Stored calendar activities]_ from selected day in _:blue[real time]_")
            st.bar_chart(df_energy_date, x="time", y="energy", color="activity") 
            
            st.markdown('#### Current energy balance') 
            st.caption("_:blue[Energy intake]_ at selected day in _:blue[real time]_")
            col1, col2, col3 = st.columns(3)
            col1.metric("Input energy", energy_in, "+ kcal")
            col2.metric("Output energy", energy_out, "-kcal")
            col3.metric("Deficite", energy_balance, deficite_text)  
        
    with col[2]: 
        if len(df_energy_date) == 0:
            st.markdown('#### Total energy output') 
            st.caption("_:blue[Total energy needed]_ at selected day is _:blue[" + str(int(sum_energy_output)) + " kcal]_")  
            
            st.markdown('#### Nutrition meals') 
            st.caption("There is _:blue[no data available]_ for the selected day")

            st.markdown('#### Current nutrition balance') 
            st.caption("There is _:blue[no data available]_ for the selected day")
        else:
            st.markdown('#### Total energy output') 
            st.caption("_:blue[Total energy needed]_ at selected day is _:blue[" + str(int(sum_energy_output)) + " kcal]_")  

            st.markdown('#### Nutrition meals') 
            if sum(df_nutritions_labeled['nutrient'].values) == 0.0:
                st.caption("There are _:blue[no meals registered]_ for the selected day")
                
            else:
                st.caption("_:blue[Nutrition intake]_ for registered meals at selected day")
                st.bar_chart(df_nutritions_labeled, x="time", y="nutrient", color="label") 
            
            st.markdown('#### Current nutrition balance') 
            if sum(df_nutritions_labeled['nutrient'].values) == 0.0:
                st.caption("There are _:blue[no meals registered]_ for the selected day")
            else:
                st.caption("_:blue[Nutrition intake]_ at selected day in _:blue[real time]_")    
                col1, col2, col3 = st.columns(3)
                col1.metric("Protein", str(df_nutrition_acc['value'].iloc[0]) + ' g', df_nutrition_acc['percent'].iloc[0])
                col2.metric("Carbs", str(df_nutrition_acc['value'].iloc[1]) + ' g', df_nutrition_acc['percent'].iloc[1])
                col3.metric("Fat", str(df_nutrition_acc['value'].iloc[2]) + ' g', df_nutrition_acc['percent'].iloc[2])  
    
with tab2:
    col = st.columns((5.5, 5.5), gap='medium') 
    with col[0]:  
        st.header("Activity Registration")
        create_new_form_activity()

with tab3:
    col = st.columns((5.5, 5.5), gap='medium') 
    with col[0]: 
        st.header("Add recipie")
        st.caption("Type in a _:blue[ recipie name]_ that you want to add to your meal")  
        df_recipie_db = pd.read_csv('data/meal_databas.csv').sort_values(['name'])
        recipie_list = df_recipie_db['name'].unique()
        options_recipie = st.multiselect(
            "Select recipies to add to your meal",
            recipie_list,
            key='find_recipie'
        )
       
        st.header("Add food items")
        st.caption("_:blue[Type in food items]_ that you want to add to your meal")  
        df_food_db = pd.read_csv('data/livsmedelsdatabas.csv')
        food_list = df_food_db['livsmedel'].values
        options = st.multiselect(
            "Select food items to add to your meal",
            food_list,
            key='create_meal'
        )

        st.header("Your meal")
        st.caption("This is the _:blue[ content of your meal]_")  
        temp_store = []
        code = ''
        options_string = ''
        df_recipies = pd.DataFrame([{"Food":'Deleted', "Amount (g)": 0.0}])
        df_meal = pd.DataFrame([{"Food":'', "Amount (g)": 0.0}])
        if (len(options) > 0) or len(options_recipie):
            temp_store_recipies = []
            if len(options_recipie) > 0:
                for i in range(0, len(options_recipie)):
                    df_this_recpie = df_recipie_db[df_recipie_db['name'] == options_recipie[i]]
                    for k in range(0, len(df_this_recpie)):
                        temp_store_recipies.append({
                            "Food": df_this_recpie['livsmedel'].iloc[k], 
                            "Amount (g)": df_this_recpie['amount'].iloc[k]})
                    options_string = options_string + df_this_recpie['name'].iloc[0] + '/'
                df_recipies = pd.DataFrame(temp_store_recipies)
            for i in range(0, len(options)):
                temp_store.append({"Food": options[i], "Amount (g)": 0})
                options_string = options_string + options[i] + '/'
            df_meal = pd.DataFrame(temp_store)
            df_total = pd.concat([df_recipies, df_meal])
            df_total = df_total[df_total['Food'] != 'Deleted']
            df_result_meal = st.data_editor(df_total, key='create_meal_editor', hide_index=True, use_container_width=True)
            print(options_string)
            if len(df_result_meal) > 0:
                df_food_nutrition = locate_eatables(df_result_meal)
                code = code_detector(df_result_meal, df_food_nutrition)
                df_result_meal['code'] = code
        else:
            st.error('Your meal is empty', icon="🚨")
            st.write('Serach for food items to add to your meal.')

    with col[1]:  
        st.header("Food Registration")
        st.caption("_:blue[Register your meal]_ to the dashboard")  
        options_string = options_string[:-1]
        create_new_form_food(code, options_string)

with tab4:
    col = st.columns((5.0, 5.0, 5.0), gap='medium') 
    with col[0]: 
        st.header("Add food item")
        st.caption("_:blue[Add new food item]_ to the database")  
        create_form_add_food_item()
    with col[1]: 
        st.header("Search for food items")
        st.caption("_:blue[Type in food items]_ that you want to add to your recipie")  
        df_food_db = pd.read_csv('data/livsmedelsdatabas.csv')
        food_list = df_food_db['livsmedel'].values
        options = st.multiselect(
            "Select food items to your recipie",
            food_list,
            key='add_meal'
        )
        
        st.header("Create recipie")
        st.caption("This is the _:blue[ content of your recipie]_")  
        temp_store = []
        code = ''
        meal_df = pd.DataFrame([{}])
        if len(options) > 0:
            for i in range(0, len(options)):
                temp_store.append({"Food": options[i], "Amount (g)": 0})
            df_my = pd.DataFrame(temp_store)
            meal_df = st.data_editor(df_my, key='add_meal_editor', hide_index=True, use_container_width=True)
            if len(meal_df) > 0:
                df_food_nutrition = locate_eatables(meal_df)
                code = code_detector(meal_df, df_food_nutrition)
                meal_df['code'] = code
        else:
            st.error('Your recipie is empty', icon="🚨")
            st.write('Serach for food items to add to your recipie.')
    with col[2]:
        st.header("Save recipie")
        st.caption("_:blue[Save your recipie]_ to the database")  
        create_form_add_meal(meal_df, code)        

with tab5:
    
    col = st.columns((5.0, 8.0), gap='medium') 
    with col[0]: 
        st.header("Recipies in database")
        st.caption("These are the stored _:blue[ recipies in your database]_")  
        df_meal_db = pd.read_csv('data/meal_databas.csv')
        summary = df_meal_db.groupby(['name', 'code']).count().sort_values(['favorite', 'name'])
        for i in range(0, len(summary)):
            this_key = 'meal_' + str(i)
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
        st.markdown('#### Registration list')  
        st.caption("_:blue[Stored registrations]_ from selected day in _:blue[real time]_")
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
                use_container_width=False)

            button_pressed = st.button("Delete item", key="button_reg_logg")
            if button_pressed:
                df_drop = edited_df[edited_df.delete == True]
                print(df_drop)
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
                delete_item_from_dataset(selected_date, df_new)
                button_pressed = False
                st.write("Changes where saved...") 
 