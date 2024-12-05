# Import libraries
import streamlit as st
import pandas as pd
import datetime
import altair as alt

import io

from scripts.data_storage import delete_item_from_dataset

from scripts.data_dashboard import date_time_now
from scripts.data_dashboard import datetime_to_string
from scripts.data_dashboard import translate_dates_to_text
from scripts.data_dashboard import calc_bmr
from scripts.data_dashboard import energy_differ
from scripts.data_dashboard import calc_daily_energy_output
from scripts.data_dashboard import  calc_energy_deficite
from scripts.data_dashboard import energy_balance_at_current_time
from scripts.data_dashboard import nutrition_content
from scripts.data_dashboard import nutrition_differ
from scripts.data_dashboard import add_summary_to_dataset 

from scripts.nutritions import locate_eatables
from scripts.nutritions import code_detector

from scripts.forms import create_new_form_activity
from scripts.forms import create_new_form_food
from scripts.forms import create_form_add_recipie_to_database
from scripts.forms import create_form_add_food_item_to_database

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
#df_energy = load_data_from_db('energy_balance')
df_energy =  df_db_csv = pd.read_csv('data/updated-database-results.csv')

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
        create_new_form_activity()
        

def create_page_meal_registration():
    col = st.columns((5.5, 5.5), gap='medium') 
    with col[0]: 
        st.markdown("#### Add recipie")
        st.caption("Type in a _:blue[ recipie name]_ that you want to add to your meal")  
        df_recipie_db = pd.read_csv('data/meal_databas.csv').sort_values(['name'])
        recipie_list = df_recipie_db['name'].unique()

        st.multiselect(
            "Select recipies to add to your meal",
            recipie_list,
            key='find_recipie'
        )

        if "options_recipie" not in st.session_state:
            st.session_state.options_recipie = []
        options_recipie = st.session_state.find_recipie

        st.markdown("#### Add food items")
        st.caption("_:blue[Type in food items]_ that you want to add to your meal")  
        df_food_db = pd.read_csv('data/livsmedelsdatabas.csv')
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
                code = code_detector(df_result_meal, df_food_nutrition, 1)
                df_result_meal['code'] = code
        else:
            st.error('Your meal is empty', icon="🚨")
            st.write('Serach for food items to add to your meal.')

    with col[1]:  
        st.markdown("#### Food Registration")
        st.caption("_:blue[Register your meal]_ to the dashboard")  
        options_string = options_string[:-1]
        create_new_form_food(code, options_string)

def create_page_database():
    col = st.columns((5.0, 5.0, 5.0), gap='medium') 
    with col[0]: 
        st.markdown("#### Add food item")
        st.caption("_:blue[Add new food item]_ to the database")  
        create_form_add_food_item_to_database()
    with col[1]: 
        st.markdown("#### Search for food items")
        st.caption("_:blue[Type in food items]_ that you want to add to your recipie")  
        df_food_db = pd.read_csv('data/livsmedelsdatabas.csv')
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
        df_meal_db = pd.read_csv('data/meal_databas.csv')
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
                delete_item_from_dataset(selected_date_delete, df_new)
                st.rerun()

        st.markdown('#### Delete recipies in database')  
        st.caption("_:blue[Select recipie]_ that you aim to _:blue[delete]_")
        df_meal_db = pd.read_csv('data/meal_databas.csv')
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
                df_meal_db_update.to_csv('data/meal_databas.csv', index=False)
            
            def submit_change():
                st.session_state.button_change_recipie_logg = False
                df_meal_db_update_change = df_meal_db[df_meal_db['name'] != selected_recipie]
                df_add_update = pd.concat([df_meal_db_update_change, edited_df_recipie])
                df_add_update.to_csv('data/meal_databas.csv', index=False)

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
    bmr = calc_bmr(50, 170, 42)
    date_now =  date_time_now()  
    selected_date_input = st.date_input("Select a date", date_now, key='head_selector') 
    selected_date = datetime_to_string(selected_date_input)
    page_names_to_funcs = {
        "Dashboard": create_dashobard,
        "Activity": create_page_activity_registration,
        "Meals": create_page_meal_registration,
        "Database": create_page_database,
        "Log book": create_page_logg_book
    }

demo_name = st.sidebar.selectbox("Select a page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()
 