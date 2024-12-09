import streamlit as st
import pandas as pd

from scripts.data_dashboard import date_time_now
from scripts.data_dashboard import time_now

from scripts.data_storage import add_registration

def create_new_form_activity():
    date_now =  date_time_now()   
    col = st.columns((2.5, 2.5), gap='medium') 
    
    if "my_time" not in st.session_state:
        st.session_state.my_time = None
    
    if "button_disabled" not in st.session_state:
        st.session_state.button_disabled = True
    
    def submit():
        st.session_state.my_time = st.session_state.act_time
        st.session_state.act_time = None

    with col[0]:  
        this_date = st.date_input("Select a date", date_now, key="act")
        st.write("Selected date: ", this_date)
    with col[1]:
        my_time = st.session_state.my_time
        st.time_input("Select a time", value=None, key="act_time")
        st.write("Selected time: ", st.session_state.act_time)
    
    form_activity = st.form(key="activity", clear_on_submit=True)
    with form_activity:
        this_activity = st.selectbox("Choose activity", ("","Walk", "Run", "Swim", "Bike", "Strength", "Yoga"))
        this_distance = st.text_input("Distance (km)")
        this_energy = st.text_input("Energy burned (kcal)")
        this_note = st.text_input("Details")
        #if this_time
        submit_activity = st.form_submit_button("Submit",  on_click=submit) #disabled=st.session_state.button_disabled,
        if submit_activity:
            add_registration(
                {     
                    "date": this_date, 
                    "time": my_time,
                    "label": 'TRAINING', 
                    "energy": -1 * int(this_energy), 
                    "pro": 0, 
                    "carb": 0, 
                    "fat": 0, 
                    "activity": this_activity, 
                    "distance": this_distance,                
                    "note": str(this_note), 
                },
                    'energy_balance'
                )

### FOOD REGISTRATION
def create_new_form_food(code, options_string):
    date_now =  date_time_now() 
    col = st.columns((2.5, 2.5), gap='medium') 
    
    if "my_time" not in st.session_state:
        st.session_state.my_time = None
    if "code" not in st.session_state:
        st.session_state.code = ''
    if "note" not in st.session_state:
        st.session_state.note = ''
    
    def submit():
        st.session_state.my_time = st.session_state.foo_time
        st.session_state.foo_time = None
        st.session_state.code = st.session_state.code_input
        st.session_state.code_input = ''
        st.session_state.note = st.session_state.note_input
        st.session_state.note_input = ''
        st.session_state.options = st.session_state.create_meal
        st.session_state.create_meal = []
        st.session_state.options_recipie = st.session_state.find_recipie
        st.session_state.find_recipie = []
    
    with col[0]:  
        this_date = st.date_input("Select a date", date_now, key="foo_date")
        st.write("Selected date: ", this_date)
    with col[1]: 
        my_time = st.session_state.my_time
        st.time_input("What time did you eat", value=None, key="foo_time")
        st.write("Selected time: ", st.session_state.foo_time)
    form_food = st.form(key="form_create_meal", clear_on_submit=True)
    with form_food:
        this_code = st.session_state.code
        st.text_input("Meal code (kcal/pro/carb/fat)", code, key="code_input")
        food_split = this_code.split('/')
        this_note = st.session_state.note
        st.text_input("Details", options_string, key="note_input")
        submit_food = st.form_submit_button("Submit", on_click=submit)   
        if submit_food:
            add_registration(
                {
                    "date": this_date, 
                    "time": my_time,
                    "label": 'FOOD', 
                    "energy": int(food_split[0]),
                    "pro": int(food_split[1]),
                    "carb": int(food_split[2]),
                    "fat": int(food_split[3]),
                    "activity": 'Eat', 
                    "distance": 0.0, 
                    "note": str(this_note), 
                },
                    'energy_balance'
                )

def create_form_add_food_item_to_database():
    form_food_item = st.form(key="form_add_food_item", clear_on_submit=True)
    with form_food_item:
        this_name = st.text_input("Name of food item", key='this_name')
        this_energy = st.text_input("Energy (kcal / 100 g)", key='this_energy')
        this_pro = st.text_input("Proteins (g / 100 g)",  key='this_pro')
        this_carb = st.text_input("Carbohydrates (g / 100 g)",  key='this_carb')
        this_fat = st.text_input("Fats (g / 100 g)",  key='this_fat')
        submit_food_item = st.form_submit_button("Save food item")    
        if submit_food_item:
            new_food_item = {
                'livsmedel': this_name,
                'calorie': float(this_energy),
                'protein': float(this_pro),
                'carb': float(this_carb),
                'fat': float(this_fat)
            }
            df_new_food_item = pd.DataFrame([new_food_item])
            df_food_db = pd.read_csv('data/livsmedelsdatabas.csv')
            df_add_food_item = pd.concat([df_food_db, df_new_food_item])
            df_add_food_item.to_csv('data/livsmedelsdatabas.csv', index=False)

def create_form_add_recipie_to_database(meal_df, code): 
    if "df_meal_storage" not in st.session_state:
        st.session_state.df_meal_storage = pd.DataFrame([{}])
    
    def submit():
        st.session_state.df_meal_storage = meal_df
        st.session_state.options_database = st.session_state.add_meal
        st.session_state.add_meal = []

    form_recipie = st.form(key="form_add_meal", clear_on_submit=True)
    with form_recipie:
        this_name = st.text_input("Name of recipie")
        st.text_input("Meal code (kcal/pro/carb/fat)", code)
        save_favorite = st.checkbox("⭐️ Save recipie as favorite ")
        submit_recipie = st.form_submit_button("Save recipie", on_click=submit)   
        if submit_recipie:
            df_meal_db = pd.read_csv('data/meal_databas.csv')
            df_stored_meal = st.session_state.df_meal_storage
            if save_favorite == True:
                df_stored_meal['favorite'] = True
            else:  
                df_stored_meal['favorite'] = False
            df_stored_meal['name'] = this_name
            df_stored_meal = df_stored_meal.rename(columns={"Food": "livsmedel", "Amount (g)": "amount"})
            df_stored_meal = df_stored_meal[['name', 'livsmedel' , 'amount', 'code', 'favorite']]
            add_meal = pd.concat([df_meal_db, df_stored_meal])
            add_meal.to_csv('data/meal_databas.csv', index=False)