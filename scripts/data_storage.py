# Updated data_storage.py
import streamlit as st
from st_supabase_connection import SupabaseConnection
import pandas as pd
import io

from scripts.data_dashboard import datetime_to_string
from scripts.data_dashboard import time_to_string
from scripts.data_dashboard import basal_energy

# Configuration: This will be set from the main app
USE_DATABASE = False  # Default value, will be overridden from main app

def get_supabase_connection():
    """Get or create Supabase connection"""
    return st.connection("supabase", type=SupabaseConnection)

# ===================== DATABASE FUNCTIONS =====================

def fetch_all_from_database(table_name):
    """Fetch ALL data from a Supabase table (not just 1000 rows)"""
    conn = get_supabase_connection()
    try:
        # Fetch data in chunks to get all records
        all_data = []
        offset = 0
        chunk_size = 1000
        
        while True:
            response = conn.table(table_name).select("*").range(offset, offset + chunk_size - 1).execute()
            
            if not response.data:
                break
                
            all_data.extend(response.data)
            
            # If we got less than chunk_size, we've reached the end
            if len(response.data) < chunk_size:
                break
                
            offset += chunk_size
        
        if all_data:
            df = pd.DataFrame(all_data)
            
            # Handle date and time formatting for energy_balance table
            if table_name == "energy_balance" and not df.empty:
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m-%d')
                if 'time' in df.columns:
                    try:
                        df['time'] = pd.to_datetime(df['time'], format='%H:%M:%S').dt.strftime('%H:%M')
                    except:
                        df['time'] = df['time'].astype(str).str[:5]
                df = df.sort_values(['date', 'time'])
            
            print(f'Data was fetched from database table: {table_name} ({len(df)} rows)')
            return df
        else:
            # Return empty dataframe with appropriate columns
            return get_empty_dataframe(table_name)
            
    except Exception as e:
        st.error(f"Error loading data from {table_name}: {str(e)}")
        return get_empty_dataframe(table_name)

def save_all_to_database(df, table_name):
    """Replace all data in a Supabase table with new dataframe - FAST method"""
    conn = get_supabase_connection()
    try:
        # FAST Method: Bulk delete all records at once
        print(f"Clearing table {table_name}...")
        
        # Try different bulk delete approaches
        delete_successful = False
        
        # Method 1: Delete all with a simple condition that matches all rows
        try:
            # This deletes all rows where id is not null (which should be all rows)
            delete_response = conn.table(table_name).delete().not_.is_('id', 'null').execute()
            delete_successful = True
            print(f"Bulk delete successful using not null condition")
        except Exception as e1:
            print(f"Method 1 failed: {e1}")
            
            # Method 2: Try with a condition that should match all rows
            try:
                delete_response = conn.table(table_name).delete().gte('id', 0).execute()
                delete_successful = True
                print(f"Bulk delete successful using gte 0 condition")
            except Exception as e2:
                print(f"Method 2 failed: {e2}")
                
                # Method 3: Use RPC call for truncate (requires custom function in Supabase)
                try:
                    truncate_response = conn.rpc('truncate_table', {'table_name': table_name}).execute()
                    delete_successful = True
                    print(f"Truncate successful using RPC")
                except Exception as e3:
                    print(f"Method 3 (RPC truncate) failed: {e3}")
                    print("Consider creating a custom RPC function in Supabase for truncating tables")
        
        if not delete_successful:
            raise Exception("All delete methods failed. Check your database permissions.")
        
        # Insert new data in bulk
        if not df.empty:
            # Remove any 'id' column if it exists (let Supabase auto-generate)
            df_to_insert = df.copy()
            if 'id' in df_to_insert.columns:
                df_to_insert = df_to_insert.drop('id', axis=1)
            
            # Convert dataframe to list of dictionaries
            data_to_insert = df_to_insert.to_dict('records')
            
            print(f"Inserting {len(data_to_insert)} records in chunks...")
            
            # Insert data in reasonably sized chunks
            chunk_size = 500  # Larger chunks for faster insertion
            chunks_total = (len(data_to_insert) + chunk_size - 1) // chunk_size
            
            for i in range(0, len(data_to_insert), chunk_size):
                chunk = data_to_insert[i:i + chunk_size]
                chunk_num = i // chunk_size + 1
                
                try:
                    insert_response = conn.table(table_name).insert(chunk).execute()
                    print(f"Inserted chunk {chunk_num}/{chunks_total}: {len(chunk)} records")
                except Exception as chunk_error:
                    print(f"Error inserting chunk {chunk_num}: {chunk_error}")
                    # Try smaller chunks if this fails
                    if len(chunk) > 100:
                        print(f"Retrying chunk {chunk_num} with smaller sub-chunks...")
                        for j in range(0, len(chunk), 100):
                            sub_chunk = chunk[j:j + 100]
                            conn.table(table_name).insert(sub_chunk).execute()
                            print(f"  Inserted sub-chunk: {len(sub_chunk)} records")
                    else:
                        raise chunk_error
        
        print(f'Data was saved to database table: {table_name} ({len(df)} rows) - FAST METHOD')
        
    except Exception as e:
        st.error(f"Error saving data to {table_name}: {str(e)}")
        print(f"Detailed error: {e}")
        
        # If database operation fails, provide more detailed error info
        if "insufficient_privilege" in str(e):
            st.error("Database permission error. Check your Supabase policies and API key permissions.")
        elif "relation" in str(e) and "does not exist" in str(e):
            st.error(f"Table {table_name} does not exist in your database.")
        else:
            st.error("Database operation failed. Check console for details.")

def get_empty_dataframe(table_name):
    """Return empty dataframe with correct columns for each table"""
    if table_name == "energy_balance":
        return pd.DataFrame(columns=['date', 'time', 'label', 'activity', 'distance', 
                                   'energy', 'pro', 'carb', 'fat', 'note', 
                                   'energy_acc', 'protein_acc', 'duration', 'pace', 'steps'])
    elif table_name == "livsmedelsdatabas":
        return pd.DataFrame(columns=['livsmedel', 'calorie', 'protein', 'carb', 'fat'])
    elif table_name == "recipie_databas":
        return pd.DataFrame(columns=['name', 'livsmedel', 'amount', 'code', 'favorite'])
    else:
        return pd.DataFrame()

# ===================== CSV FUNCTIONS =====================

def fetch_from_csv(path_to_df_to_fetch):
    """Fetch data from CSV file"""
    try:
        df_fetched = pd.read_csv(path_to_df_to_fetch)
        return df_fetched
    except FileNotFoundError:
        st.error(f"CSV file not found: {path_to_df_to_fetch}")
        # Return empty dataframe based on file name
        if "energy" in path_to_df_to_fetch or "database-results" in path_to_df_to_fetch:
            return get_empty_dataframe("energy_balance")
        elif "livsmedelsdatabas" in path_to_df_to_fetch:
            return get_empty_dataframe("livsmedelsdatabas")
        elif "recipie" in path_to_df_to_fetch or "meal" in path_to_df_to_fetch:
            return get_empty_dataframe("recipie_databas")
        else:
            return pd.DataFrame()

def save_to_csv(df_to_store, path):
    """Save dataframe to CSV file"""
    df_to_store.to_csv(path, index=False)
    print(f'Data was saved to CSV: {path}')

# ===================== UNIFIED INTERFACE FUNCTIONS =====================

def fetch_data_from_storage(path_or_table):
    """Unified function to fetch data from either CSV or database"""
    # Access the global USE_DATABASE variable
    global USE_DATABASE
    
    if USE_DATABASE:
        # Map file paths to table names
        table_mapping = {
            'data/updated-database-results.csv': 'energy_balance',
            'data/livsmedelsdatabas.csv': 'livsmedelsdatabas', 
            'data/recipie_databas.csv': 'recipie_databas',
            'data/meal_databas.csv': 'recipie_databas'  # Legacy name mapping
        }
        
        table_name = table_mapping.get(path_or_table, path_or_table)
        return fetch_all_from_database(table_name)
    else:
        return fetch_from_csv(path_or_table)

def save_data_to_storage(df_to_store, path_or_table):
    """Unified function to save data to either CSV or database"""
    # Access the global USE_DATABASE variable
    global USE_DATABASE
    
    if USE_DATABASE:
        # Map file paths to table names
        table_mapping = {
            'data/updated-database-results.csv': 'energy_balance',
            'data/livsmedelsdatabas.csv': 'livsmedelsdatabas',
            'data/recipie_databas.csv': 'recipie_databas',
            'data/meal_databas.csv': 'recipie_databas'  # Legacy name mapping
        }
        
        table_name = table_mapping.get(path_or_table, path_or_table)
        save_all_to_database(df_to_store, table_name)
    else:
        save_to_csv(df_to_store, path_or_table)

# ===================== LEGACY FUNCTIONS (keeping for compatibility) =====================

def load_activity_data():
    """Load energy balance data - legacy function"""
    return fetch_data_from_storage('data/updated-database-results.csv')

def load_food_database():
    """Load food database - legacy function"""
    return fetch_data_from_storage('data/livsmedelsdatabas.csv')

def load_recipie_database():
    """Load meal/recipe database - legacy function"""
    return fetch_data_from_storage('data/recipie_databas.csv')

# ===================== EXISTING FUNCTIONS (unchanged) =====================

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
    """Updated function to handle new columns"""
    df_new  = df_db_csv[df_db_csv['date'] == date_new_post]
    if len(df_new) == 0:
        df_basal_energy = basal_energy(date_new_post, bmr)       
        df_new_post = df_new_post[df_new_post['date'] == date_new_post]   
        df_concat = pd.concat([df_basal_energy, df_new_post]).sort_values(['time']).fillna({
            'duration': '00:00:00',
            'pace': 0.0,
            'steps': 0,
            'distance': 0.0,
            'pro': 0.0,
            'carb': 0.0,
            'fat': 0.0,
            'note': ''
        })
        df_concat = df_concat[['date', 'time', 'label', 'activity', 'distance', 'energy', 
                              'pro', 'carb', 'fat', 'note', 'duration', 'pace', 'steps']]  
        df_concat_acc = calc_accumulated_energy(df_concat)
        df_energy_new = pd.concat([df_db_csv, df_concat_acc])
    else:
        # Remove accumulated columns before concatenation
        cols_to_drop = ['energy_acc', 'protein_acc']
        cols_to_drop = [col for col in cols_to_drop if col in df_db_csv.columns]
        if cols_to_drop:
            df_db_csv = df_db_csv.drop(cols_to_drop, axis=1)
        
        df_concat_acc = pd.concat([df_db_csv, df_new_post]).sort_values(['date', 'time'])
        # Fill missing values for new columns
        df_concat_acc = df_concat_acc.fillna({
            'duration': '00:00:00',
            'pace': 0.0,
            'steps': 0,
            'distance': 0.0,
            'pro': 0.0,
            'carb': 0.0,
            'fat': 0.0,
            'note': ''
        })
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
    """Add new registration without CSV file dependency"""
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
        'distance': df_registration['distance'].iloc[0] if 'distance' in df_registration.columns else 0.0,
        'duration': df_registration['duration'].iloc[0] if 'duration' in df_registration.columns else '00:00:00',
        'pace': df_registration['pace'].iloc[0] if 'pace' in df_registration.columns else 0.0,
        'steps': df_registration['steps'].iloc[0] if 'steps' in df_registration.columns else 0,
        'note': df_registration['note'].iloc[0]
    }

    df_new_post = pd.DataFrame([new_data])
    date_new_post = df_new_post['date'].iloc[0]
    
    df_db_csv = fetch_data_from_storage('data/updated-database-results.csv')
    
    # Add missing columns if they don't exist
    if 'duration' not in df_db_csv.columns:
        df_db_csv['duration'] = '00:00:00'
    if 'pace' not in df_db_csv.columns:
        df_db_csv['pace'] = 0.0
    if 'steps' not in df_db_csv.columns:
        df_db_csv['steps'] = 0
    
    df_energy_new = add_new_data_to_dataset_csv(df_db_csv, df_new_post, date_new_post, bmr)  
    save_data_to_storage(df_energy_new, 'data/updated-database-results.csv')  
    
    # Access the global USE_DATABASE variable
    global USE_DATABASE
    storage_type = "database" if USE_DATABASE else "CSV file"
    print(f'Registration added successfully to {storage_type}...')
    st.rerun()
    
def save_meal_to_database(date_str, time_str, meal_name, df_meal_items, code, favorite=False):
    """
    Save a meal with all its components to the meal_databas.csv file
    
    Parameters:
    - date_str: Date in YYYY-MM-DD format
    - time_str: Time in HH:MM format  
    - meal_name: Name/description of the meal
    - df_meal_items: DataFrame with columns 'Food' and 'Amount (g)'
    - code: The calculated nutrition code (kcal/pro/carb/fat)
    - favorite: Boolean indicating if meal is marked as favorite
    """
    try:
        # Load existing meal database
        try:
            df_meal_db = fetch_data_from_storage('data/meal_databas.csv')
        except:
            # Create empty dataframe if file doesn't exist
            df_meal_db = pd.DataFrame(columns=['date', 'time', 'name', 'livsmedel', 'amount', 'code', 'favorite'])
        
        # Prepare meal entries for each food item
        meal_entries = []
        for i in range(len(df_meal_items)):
            meal_entry = {
                'date': date_str,
                'time': time_str,
                'name': meal_name,
                'livsmedel': df_meal_items['Food'].iloc[i],
                'amount': df_meal_items['Amount (g)'].iloc[i],
                'code': code,
                'favorite': favorite
            }
            meal_entries.append(meal_entry)

        print(meal_entries)
        
        # Convert to DataFrame and append to existing database
        df_new_meal = pd.DataFrame(meal_entries)
        df_updated_meal_db = pd.concat([df_meal_db, df_new_meal], ignore_index=True)
        
        # Save updated database
        save_data_to_storage(df_updated_meal_db, 'data/meal_databas.csv')
        
        print(f'Meal "{meal_name}" automatically saved to meal log with {len(meal_entries)} food items')
        
    except Exception as e:
        print(f'Error saving meal to database: {e}')
        # Don't show error to user since this is automatic logging
        # st.error(f'Failed to save meal to database: {e}')