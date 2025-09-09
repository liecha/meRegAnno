import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import io

from scripts.data_dashboard import datetime_to_string
from scripts.data_dashboard import time_to_string
from scripts.data_dashboard import basal_energy

def get_supabase_connection():
    """Get or create Supabase connection"""
    return st.connection("supabase", type=SupabaseConnection)

def load_activity_data():
    """Load energy balance data from Supabase - simplified version"""
    conn = get_supabase_connection()
    try:
        # Simple fetch - let's not overcomplicate with pagination for now
        response = conn.table("energy_balance").select("*").order("date", "time").execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            if not df.empty:
                # Handle date and time conversion
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                if 'time' in df.columns:
                    try:
                        df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.strftime('%H:%M')
                    except:
                        df['time'] = df['time'].astype(str).str[:5]
                # Sort by date and time
                df = df.sort_values(['date', 'time'])
            return df
        else:
            return pd.DataFrame(columns=['date', 'time', 'label', 'activity', 'distance', 
                                        'energy', 'pro', 'carb', 'fat', 'note', 
                                        'energy_acc', 'protein_acc'])
    except Exception as e:
        st.error(f"Error loading energy data: {str(e)}")
        return pd.DataFrame(columns=['date', 'time', 'label', 'activity', 'distance', 
                                    'energy', 'pro', 'carb', 'fat', 'note', 
                                    'energy_acc', 'protein_acc'])

def fetch_data_from_storage(path_to_df_to_fetch):
    df_fetched = pd.read_csv(path_to_df_to_fetch)
    print('Data was fetched from data storage...')
    return df_fetched

def save_data_to_storage(df_to_store, path):
    df_to_store.to_csv(path, index=False)
    print('Data was saved to data storage...')

def calc_accumulated_energy(df_data):
    ls_dates = df_data.groupby(['date']).count().index.to_list()
    storage = []
    for j in range(0, len(ls_dates)):
        df_day = df_data[df_data['date'] == ls_dates[j]]
        ls_calories = df_day['energy'].values
        ls_protein = df_day['pro'].values
        ls_acc_calories = [ls_calories[0]]
        ls_acc_protein = [ls_protein[0]]
        for i in range(0, len(ls_calories) - 1):           
            counting_calories = ls_acc_calories[i] + ls_calories[i + 1]
            counting_protein = ls_acc_protein[i] + ls_protein[i + 1]
            ls_acc_calories.append(counting_calories) 
            ls_acc_protein.append(counting_protein)
        df_day.insert(6, 'energy_acc', ls_acc_calories)
        df_day.insert(8, 'protein_acc', ls_acc_protein)
        storage.append(df_day)
    df_energy_acc = pd.concat(storage)
    return df_energy_acc

def add_new_data_to_dataset_csv(df_db_csv, df_new_post, date_new_post, bmr):
    df_new  = df_db_csv[df_db_csv['date'] == date_new_post]
    if len(df_new) == 0:
        print('Add this new day to the dataset because it is a NEW day.')
        df_basal_energy = basal_energy(date_new_post, bmr)       
        df_new_post = df_new_post[df_new_post['date'] == date_new_post]   
        df_concat = pd.concat([df_basal_energy, df_new_post]).sort_values(['time']).fillna(0) 
        df_concat = df_concat[['date', 'time', 'label', 'activity', 'distance', 'energy', 'pro', 'carb', 'fat', 'note']]  
        df_concat_acc = calc_accumulated_energy(df_concat)
        df_energy_new = pd.concat([df_db_csv, df_concat_acc])
    else:
        print('Add this new activity ONLY because the day has already been added to the dataset.')
        df_db_csv = df_db_csv.drop(['energy_acc', 'protein_acc'], axis=1)
        df_concat_acc = pd.concat([df_db_csv, df_new_post]).sort_values(['date', 'time'])
        df_energy_new = calc_accumulated_energy(df_concat_acc).sort_values(['date', 'time'])
    return df_energy_new

def delete_item_from_dataset(selected_date, df_new, bmr):
    df_db = fetch_data_from_storage('data/updated-database-results.csv')
    df_db = df_db[df_db.date != selected_date]
    df_basal_energy = basal_energy(selected_date, bmr)      
    df_new_post = df_new[df_new['date'] == selected_date]   
    df_concat = pd.concat([df_basal_energy, df_new_post]).sort_values(['time']).fillna(0) 
    df_concat = df_concat[['date', 'time', 'label', 'activity', 'distance', 'energy', 'pro', 'carb', 'fat', 'note', 'summary']]  
    df_concat_acc = calc_accumulated_energy(df_concat)
    df_energy_new = pd.concat([df_db, df_concat_acc]).sort_values(['date', 'time'])
    save_data_to_storage(df_energy_new, 'data/updated-database-results.csv')

def add_registration(data: dict, bmr):
    df_registration = pd.DataFrame([data])
    this_date = df_registration['date'].iloc[0]
    this_time = df_registration['time'].iloc[0]
    date_str = datetime_to_string(this_date)
    time_str = time_to_string(this_time)
    
    new_data = {
        'date': date_str,
        'time': time_str,
        'label': df_registration['label'].iloc[0],
        'energy': df_registration['energy'].iloc[0],
        'pro': df_registration['pro'].iloc[0],
        'carb': df_registration['carb'].iloc[0],
        'fat': df_registration['fat'].iloc[0],
        'activity': df_registration['activity'].iloc[0],
        'distance': df_registration['distance'].iloc[0],
        'note': df_registration['note'].iloc[0]
    }

    df_new_post = pd.DataFrame([new_data])
    df_new_post.to_csv('data/new-post-results.csv', index=False)
    date_new_post = df_new_post['date'].iloc[0]
    
    df_db_csv = fetch_data_from_storage('data/updated-database-results.csv')
    df_energy_new = add_new_data_to_dataset_csv(df_db_csv, df_new_post, date_new_post, bmr)  
    save_data_to_storage(df_energy_new, 'data/updated-database-results.csv')  
    print('Result uploaded in csv-file...')
    st.rerun()