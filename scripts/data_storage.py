import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import io

from scripts.data_dashboard import basal_energy
from scripts.data_dashboard import calc_accumulated_energy
from scripts.data_dashboard import datetime_to_string
from scripts.data_dashboard import time_to_string

def connect_to_db():
    # Create engine to connect to database
    engine = create_engine(
        'postgresql+psycopg2://postgres:1dunSG7x@localhost:5432/energy')
    return engine

def load_data_from_db(table_name):
    # ENERGY
    # LOADING DATA 
    # df_energy = pd.read_csv('data/updated-database-results.csv')
    conn = st.connection("postgresql", type="sql")
    df_energy = conn.query('SELECT * FROM ' + table_name + ';', ttl="10m")
    return df_energy

def change_db():
    df_energy_cleaning = pd.read_csv('data/updated-database-results_clean.csv')
    df_energy_cleaning = df_energy_cleaning.drop(['energy_acc', 'protein_acc'], axis=1)
    df_energy_acc_new = calc_accumulated_energy(df_energy_cleaning)
    df_energy_acc_new.to_csv('data/updated-database-results_clean.csv', index=False)
    #write_to_db('data/updated-database-results_clean.csv')

def add_new_data_to_dataset_csv(df_db_csv, df_new_post, date_new_post):
    df_new  = df_db_csv[df_db_csv['date'] == date_new_post]
    if len(df_new) == 0:
        print('Add this new day to the dataset because it is a NEW day.')
        df_basal_energy = basal_energy(date_new_post)       
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

def delete_item_from_dataset(selected_date, df_new):
    df_db = pd.read_csv('data/updated-database-results.csv')
    df_db = df_db[df_db.date != selected_date]
    df_basal_energy = basal_energy(selected_date)       
    df_new_post = df_new[df_new['date'] == selected_date]   
    df_concat = pd.concat([df_basal_energy, df_new_post]).sort_values(['time']).fillna(0) 
    df_concat = df_concat[['date', 'time', 'label', 'activity', 'distance', 'energy', 'pro', 'carb', 'fat', 'note', 'summary']]  
    df_concat_acc = calc_accumulated_energy(df_concat)
    df_energy_new = pd.concat([df_db, df_concat_acc]).sort_values(['date', 'time'])
    df_energy_new.to_csv('data/updated-database-results.csv', index=False)

def store_in_db(table_name):
    engine = connect_to_db()
    df_db = pd.read_csv('data/updated-database-results.csv') 
    print('Drop table from database and create a new empty table...')
    df_db.head(0).to_sql(table_name, engine, if_exists='replace',index=False)    
    conn = engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    df_db.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    cur.copy_from(output, table_name, null='') # null values become 0 
    print('New data was push to the database...')
    conn.commit()  
    cur.close()
    conn.close()

def add_registration(data: dict, table_name):
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
    
    df_db_csv = pd.read_csv('data/updated-database-results.csv') 
    df_energy_new = add_new_data_to_dataset_csv(df_db_csv, df_new_post, date_new_post)    
    df_energy_new.to_csv('data/updated-database-results.csv', index=False)
    print('Result uploaded in csv-file...')
    #store_in_db(table_name)
    #print('Result uploaded in database...')
    st.rerun()