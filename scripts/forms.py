import streamlit as st
import pandas as pd

from scripts.data_dashboard import date_time_now

from scripts.data_storage import add_registration

def create_new_form_activity():
    date_now =  date_time_now()   
    col = st.columns((2.5, 2.5), gap='medium') 
    with col[0]:  
        this_date = st.date_input("Select a date", date_now, key="act")
        st.write("Selected date: ", this_date)
    with col[1]: 
        this_time = st.time_input("Select a time", value=None, key="act_time")
        st.write("Selected time: ", this_time)
    form_activity = st.form(key="activity", clear_on_submit=True)
    with form_activity:
        this_activity = st.selectbox("Choose activity", ("","Walk", "Run", "Swim", "Bike", "Strength"))
        this_distance = st.text_input("Distance (km)")
        this_energy = st.text_input("Energy burned (kcal)")
        this_note = st.text_input("Details")
        submit_activity = st.form_submit_button("Submit")
        if submit_activity:
            add_registration(
                {     
                    "date": this_date, 
                    "time": this_time,
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
def create_new_form_food(code, options):
    date_now =  date_time_now() 
    col = st.columns((2.5, 2.5), gap='medium') 
    with col[0]:  
        this_date = st.date_input("Select a date", date_now, key="foo_date")
        st.write("Selected date: ", this_date)
    with col[1]: 
        this_time = st.time_input("What time did you eat", value=None, key="foo_time")
        st.write("Selected time: ", this_time)
    form_food = st.form(key="form_create_meal", clear_on_submit=True)
    with form_food:
        this_code = st.text_input("Meal code (kcal/pro/carb/fat)", code)
        food_split = this_code.split('/')
        this_note = st.text_input("Details", options)
        submit_food = st.form_submit_button("Submit")    
        if submit_food:
            add_registration(
                {
                    "date": this_date, 
                    "time": this_time,
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

def create_form_add_meal(meal_df, code):
    form_recipie = st.form(key="form_add_meal", clear_on_submit=True)
    with form_recipie:
        this_name = st.text_input("Name of recipie")
        st.text_input("Meal code (kcal/pro/carb/fat)", code)
        save_favorite = st.checkbox("⭐️ Save recipie as favorite ")
        submit_recipie = st.form_submit_button("Save recipie")    
        if submit_recipie:
            df_meal_db = pd.read_csv('data/meal_databas.csv')
            if save_favorite == True:
                meal_df['favorite'] = True
            else:  
                meal_df['favorite'] = False
            meal_df['name'] = this_name
            meal_df = meal_df.rename(columns={"Food": "livsmedel", "Amount (g)": "amount"})
            meal_df = meal_df[['name', 'livsmedel' , 'amount', 'code', 'favorite']]
            add_meal = pd.concat([df_meal_db, meal_df])
            add_meal.to_csv('data/meal_databas.csv', index=False)

def create_form_add_food_item():
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
                'calorie': this_energy,
                'protein': this_pro,
                'carb': this_carb,
                'fat': this_fat
            }
            df_new_food_item = pd.DataFrame([new_food_item])
            df_food_db = pd.read_csv('data/livsmedelsdatabas.csv')
            df_add_food_item = pd.concat([df_food_db, df_new_food_item])
            df_add_food_item.to_csv('data/livsmedelsdatabas.csv', index=False)