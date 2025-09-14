import pandas as pd
import altair as alt
from datetime import timedelta
import re

def standardize_activity_name(activity):
    """Standardize activity names to consistent format"""
    if pd.isna(activity):
        return activity
    
    activity_upper = str(activity).upper()
    
    # Mapping of various spellings to standard names
    activity_mapping = {
        'WALK': 'Walk',
        'RUN': 'Run',
        'RUNNING': 'Run',
        'STR': 'Strength',
        'STRENGTH': 'Strength',
        'BIKE': 'Bike',
        'YOGA': 'Yoga',
        'SWIM': 'Swim',
        'BMR': 'Bmr'  # Keep BMR as Bmr for consistency with existing code
    }
    
    return activity_mapping.get(activity_upper, activity)

def get_activity_colors():
    """Define colors for different activities"""
    return {
        'Walk': '#2E8B57',      # Sea Green
        'Run': '#FF4500',       # Orange Red
        'Bike': '#1E90FF',      # Dodger Blue
        'Swim': '#00CED1',      # Dark Turquoise
        'Strength': '#8B008B',  # Dark Magenta
        'Yoga': '#9370DB',      # Medium Purple
        'REST': '#D3D3D3',      # Light Gray
        'FOOD': '#32CD32',      # Lime Green
        'Bmr': '#808080'        # Gray for BMR
    }

def filter_data_by_period(df, period_type, selected_date):
    """Filter data based on period type (day, week, month)"""
    df['date'] = pd.to_datetime(df['date'])
    selected_date = pd.to_datetime(selected_date)
    
    if period_type == "Day":
        return df[df['date'] == selected_date]
    elif period_type == "Week":
        # Get start of week (Monday)
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return df[(df['date'] >= start_of_week) & (df['date'] <= end_of_week)]
    elif period_type == "Month":
        start_of_month = selected_date.replace(day=1)
        if selected_date.month == 12:
            end_of_month = selected_date.replace(year=selected_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_of_month = selected_date.replace(month=selected_date.month + 1, day=1) - timedelta(days=1)
        return df[(df['date'] >= start_of_month) & (df['date'] <= end_of_month)]
    
    return df

def extract_numeric_distance(distance_str):
    """
    Extract numeric value from distance string.
    Examples: '8.93 km' -> 8.93, '0' -> 0.0, '20.0' -> 20.0
    """
    if pd.isna(distance_str):
        return 0.0
    
    # Convert to string if not already
    distance_str = str(distance_str)
    
    # Handle different distance formats from your data
    if distance_str == '0' or distance_str == '0.0':
        return 0.0
    
    # Extract numeric part using regex
    match = re.search(r'(\d+\.?\d*)', distance_str)
    if match:
        return float(match.group(1))
    else:
        return 0.0

def convert_duration_to_minutes(duration_str):
    """
    Convert duration string to minutes.
    Examples: '00:45:30' -> 45.5, '01:30:00' -> 90.0
    """
    if pd.isna(duration_str) or duration_str == '00:00:00' or duration_str == '':
        return 0.0
    
    duration_str = str(duration_str)
    
    # Handle HH:MM:SS format
    try:
        parts = duration_str.split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            total_minutes = hours * 60 + minutes + seconds / 60.0
            return round(total_minutes, 2)
    except (ValueError, IndexError):
        pass
    
    return 0.0

def extract_numeric_pace(pace_str):
    """
    Extract pace in minutes per km from pace string.
    Examples: "5'23''" -> 5.38, "6.37" -> 6.37
    """
    if pd.isna(pace_str) or pace_str == 0.0 or pace_str == '0.0':
        return 0.0
    
    pace_str = str(pace_str)
    
    # Handle format like "5'23''"
    if "'" in pace_str:
        # Extract minutes and seconds
        parts = pace_str.replace("''", "").split("'")
        if len(parts) == 2:
            try:
                minutes = int(parts[0])
                seconds = int(parts[1])
                return round(minutes + seconds / 60.0, 2)
            except ValueError:
                pass
    
    # Handle decimal format
    try:
        return float(pace_str)
    except ValueError:
        return 0.0

def get_training_summary(df, selected_activities):
    """
    Generate training summary for selected activities with proper distance handling.
    Updated to handle new columns: duration, pace, steps
    """
    if df.empty:
        return pd.DataFrame()
    
    # Standardize activity names before filtering
    df_copy = df.copy()
    df_copy['activity'] = df_copy['activity'].apply(standardize_activity_name)
    
    # Filter for training activities only
    training_df = df_copy[
        (df_copy['label'] == 'TRAINING') & 
        (df_copy['activity'].isin(selected_activities))
    ].copy()
    
    if training_df.empty:
        return pd.DataFrame()
    
    # Clean the distance column - extract numeric values
    training_df['distance_numeric'] = training_df['distance'].apply(extract_numeric_distance)
    
    # Handle duration - convert to minutes for summary
    training_df['duration_minutes'] = training_df['duration'].apply(convert_duration_to_minutes)
    
    # Handle steps - ensure it's numeric
    training_df['steps_numeric'] = pd.to_numeric(training_df['steps'], errors='coerce').fillna(0)
    
    # Handle pace
    training_df['pace_numeric'] = training_df['pace'].apply(extract_numeric_pace)
    
    # Perform aggregation with cleaned numeric columns
    summary = training_df.groupby('activity').agg({
        'distance_numeric': ['count', 'sum', 'mean'],
        'energy': ['sum', 'mean'],
        'duration_minutes': ['sum', 'mean'],
        'steps_numeric': 'sum',
        'pace_numeric': 'mean',
        'note': 'first'
    }).round(2)
    
    # Flatten column names
    summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
    
    # Rename columns for better display
    summary = summary.rename(columns={
        'distance_numeric_count': 'Sessions',
        'distance_numeric_sum': 'Total Distance (km)',
        'distance_numeric_mean': 'Avg Distance (km)',
        'energy_sum': 'Total Energy (kcal)',
        'energy_mean': 'Avg Energy (kcal)',
        'duration_minutes_sum': 'Total Duration (min)',
        'duration_minutes_mean': 'Avg Duration (min)',
        'steps_numeric_sum': 'Total Steps',
        'pace_numeric_mean': 'Avg Pace (min/km)',
        'note_first': 'Sample Note'
    })
    
    # Convert energy to positive values for display (they're stored as negative)
    summary['Total Energy (kcal)'] = abs(summary['Total Energy (kcal)'])
    summary['Avg Energy (kcal)'] = abs(summary['Avg Energy (kcal)'])
    
    return summary.reset_index()

def get_weekly_summary(df):
    """
    Generate weekly summary of all activities.
    """
    if df.empty:
        return pd.DataFrame()
    
    # Convert date to datetime and extract week
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    df_copy['week'] = df_copy['date'].dt.isocalendar().week
    df_copy['year'] = df_copy['date'].dt.year
    df_copy['week_year'] = df_copy['year'].astype(str) + '-W' + df_copy['week'].astype(str).str.zfill(2)
    
    # Standardize activity names
    df_copy['activity'] = df_copy['activity'].apply(standardize_activity_name)
    
    # Clean distance for proper aggregation
    df_copy['distance_numeric'] = df_copy['distance'].apply(extract_numeric_distance)
    
    # Filter out BMR entries for training summary
    training_df = df_copy[df_copy['label'] == 'TRAINING'].copy()
    
    if training_df.empty:
        return pd.DataFrame()
    
    # Group by week and activity
    weekly_summary = training_df.groupby(['week_year', 'activity']).agg({
        'distance_numeric': ['count', 'sum'],
        'energy': 'sum'
    }).round(2)
    
    # Flatten column names
    weekly_summary.columns = ['_'.join(col).strip() for col in weekly_summary.columns.values]
    
    # Rename columns
    weekly_summary = weekly_summary.rename(columns={
        'distance_numeric_count': 'Sessions',
        'distance_numeric_sum': 'Distance (km)',
        'energy_sum': 'Energy (kcal)'
    })
    
    # Convert energy to positive values
    weekly_summary['Energy (kcal)'] = abs(weekly_summary['Energy (kcal)'])
    
    return weekly_summary.reset_index()

def get_daily_energy_balance(df):
    """
    Calculate daily energy balance (intake - expenditure).
    """
    if df.empty:
        return pd.DataFrame()
    
    # Convert date to datetime
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    
    # Group by date and calculate daily totals
    daily_balance = df_copy.groupby('date').agg({
        'energy': 'sum',  # This will be net energy (negative for expenditure, positive for intake)
        'pro': 'sum',     # Total protein
        'carb': 'sum',    # Total carbs
        'fat': 'sum'      # Total fat
    }).round(1)
    
    # Rename columns
    daily_balance = daily_balance.rename(columns={
        'energy': 'Net Energy (kcal)',
        'pro': 'Protein (g)',
        'carb': 'Carbs (g)',
        'fat': 'Fat (g)'
    })
    
    return daily_balance.reset_index()

def get_nutrition_summary(df):
    """
    Generate nutrition summary for food intake only.
    """
    if df.empty:
        return pd.DataFrame(), pd.Series()
    
    # Filter for food entries only
    food_df = df[df['label'] == 'FOOD'].copy()
    
    if food_df.empty:
        return pd.DataFrame(), pd.Series()
    
    # Convert date to datetime
    food_df['date'] = pd.to_datetime(food_df['date'])
    
    # Group by date and sum nutrition values
    nutrition_summary = food_df.groupby('date').agg({
        'energy': 'sum',
        'pro': 'sum',
        'carb': 'sum',
        'fat': 'sum'
    }).round(1)
    
    # Calculate averages
    avg_nutrition = nutrition_summary.mean().round(1)
    
    # Rename columns
    nutrition_summary = nutrition_summary.rename(columns={
        'energy': 'Energy Intake (kcal)',
        'pro': 'Protein (g)',
        'carb': 'Carbs (g)',
        'fat': 'Fat (g)'
    })
    
    return nutrition_summary.reset_index(), avg_nutrition

def get_food_summary(df):
    """Generate food intake summary"""
    food_df = df[df['label'] == 'FOOD']
    
    if food_df.empty:
        return {
            'total_energy': 0,
            'total_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'meal_count': 0
        }
    
    summary = {
        'total_energy': food_df['energy'].sum(),
        'total_protein': food_df['pro'].sum(),
        'total_carbs': food_df['carb'].sum(),
        'total_fat': food_df['fat'].sum(),
        'meal_count': len(food_df)
    }
    
    return summary

def create_training_chart(df, selected_activities, chart_type="energy"):
    """Create training visualization chart"""
    # Standardize activity names
    df_copy = df.copy()
    df_copy['activity'] = df_copy['activity'].apply(standardize_activity_name)
    
    training_df = df_copy[df_copy['label'] == 'TRAINING'].copy()
    
    if selected_activities:
        training_df = training_df[training_df['activity'].isin(selected_activities)]
    
    if training_df.empty:
        return alt.Chart(pd.DataFrame()).mark_text(text="No data available", fontSize=16, color='gray')
    
    # Get activity colors
    colors = get_activity_colors()
    
    if chart_type == "energy":
        # Convert energy to positive values for visualization
        training_df['energy_positive'] = abs(training_df['energy'])
        
        chart = alt.Chart(training_df).mark_bar().add_selection(
            alt.selection_interval()
        ).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('energy_positive:Q', title='Energy Burned (kcal)'),
            color=alt.Color('activity:N', 
                          scale=alt.Scale(domain=list(colors.keys()), 
                                        range=list(colors.values())),
                          title='Activity'),
            tooltip=['date:T', 'activity:N', 'energy_positive:Q', 'distance:Q', 'note:N']
        ).properties(
            width=600,
            height=300,
            title="Energy Burned by Activity"
        )
    
    elif chart_type == "distance":
        # Clean distance data for visualization
        training_df['distance_numeric'] = training_df['distance'].apply(extract_numeric_distance)
        distance_df = training_df[training_df['distance_numeric'] > 0]
        
        if distance_df.empty:
            return alt.Chart(pd.DataFrame()).mark_text(text="No distance data available", fontSize=16, color='gray')
        
        chart = alt.Chart(distance_df).mark_bar().add_selection(
            alt.selection_interval()
        ).encode(
            x=alt.X('date:T', title='Date'),
            y=alt.Y('distance_numeric:Q', title='Distance (km)'),
            color=alt.Color('activity:N', 
                          scale=alt.Scale(domain=list(colors.keys()), 
                                        range=list(colors.values())),
                          title='Activity'),
            tooltip=['date:T', 'activity:N', 'distance_numeric:Q', 'energy:Q', 'note:N']
        ).properties(
            width=600,
            height=300,
            title="Distance by Activity"
        )
    
    return chart

def create_weekly_summary_chart(df, selected_activities):
    """Create weekly summary chart showing activity distribution"""
    # Standardize activity names
    df_copy = df.copy()
    df_copy['activity'] = df_copy['activity'].apply(standardize_activity_name)
    
    training_df = df_copy[df_copy['label'] == 'TRAINING'].copy()
    
    if selected_activities:
        training_df = training_df[training_df['activity'].isin(selected_activities)]
    
    if training_df.empty:
        return alt.Chart(pd.DataFrame()).mark_text(text="No data available", fontSize=16, color='gray')
    
    # Add day of week
    training_df['date'] = pd.to_datetime(training_df['date'])
    training_df['day_of_week'] = training_df['date'].dt.day_name()
    training_df['weekday_num'] = training_df['date'].dt.dayofweek
    
    # Convert energy to positive values
    training_df['energy_positive'] = abs(training_df['energy'])
    
    # Group by day of week and activity
    weekly_summary = training_df.groupby(['day_of_week', 'weekday_num', 'activity'])['energy_positive'].sum().reset_index()
    weekly_summary = weekly_summary.sort_values('weekday_num')
    
    colors = get_activity_colors()
    
    chart = alt.Chart(weekly_summary).mark_bar().encode(
        x=alt.X('day_of_week:O', title='Day of Week', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
        y=alt.Y('energy_positive:Q', title='Energy Burned (kcal)'),
        color=alt.Color('activity:N', 
                      scale=alt.Scale(domain=list(colors.keys()), 
                                    range=list(colors.values())),
                      title='Activity'),
        tooltip=['day_of_week:O', 'activity:N', 'energy_positive:Q']
    ).properties(
        width=600,
        height=300,
        title="Weekly Activity Distribution"
    )
    
    return chart

def create_energy_balance_chart(df):
    """Create energy balance chart showing input vs output"""
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text(text="No data available", fontSize=16, color='gray')
    
    # Ensure date is datetime
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    
    # Group by date and calculate daily totals
    daily_summary = df_copy.groupby('date').agg({
        'energy': 'sum',
        'energy_acc': 'last'  # Take the last accumulated value of the day
    }).reset_index()
    
    # Separate positive (food) and negative (exercise/BMR) energy
    food_energy = df_copy[df_copy['energy'] > 0].groupby('date')['energy'].sum().fillna(0)
    exercise_energy = abs(df_copy[df_copy['energy'] < 0].groupby('date')['energy'].sum().fillna(0))
    
    daily_summary['energy_in'] = daily_summary['date'].map(food_energy).fillna(0)
    daily_summary['energy_out'] = daily_summary['date'].map(exercise_energy).fillna(0)
    
    # Create the chart data in long format
    chart_data = []
    for _, row in daily_summary.iterrows():
        chart_data.append({
            'date': row['date'],
            'value': row['energy_in'],
            'type': 'Energy In',
            'balance': row['energy_acc']
        })
        chart_data.append({
            'date': row['date'],
            'value': row['energy_out'],
            'type': 'Energy Out',
            'balance': row['energy_acc']
        })
    
    chart_df = pd.DataFrame(chart_data)
    
    if chart_df.empty:
        return alt.Chart(pd.DataFrame()).mark_text(text="No data available", fontSize=16, color='gray')
    
    # Create the chart
    bars = alt.Chart(chart_df).mark_bar().encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('value:Q', title='Energy (kcal)'),
        color=alt.Color('type:N', 
                       scale=alt.Scale(domain=['Energy In', 'Energy Out'], 
                                     range=['#32CD32', '#FF4500']),
                       title='Type'),
        tooltip=['date:T', 'type:N', 'value:Q']
    ).properties(
        width=600,
        height=250
    )
    
    # Add balance line if we have energy_acc data
    if 'energy_acc' in daily_summary.columns and not daily_summary['energy_acc'].isna().all():
        balance_line = alt.Chart(daily_summary).mark_line(
            color='red',
            strokeWidth=2
        ).encode(
            x='date:T',
            y=alt.Y('energy_acc:Q', title='Energy Balance'),
            tooltip=['date:T', 'energy_acc:Q']
        )
        
        chart = alt.layer(bars, balance_line).resolve_scale(
            y='independent'
        ).properties(
            title="Daily Energy Balance"
        )
    else:
        chart = bars.properties(title="Daily Energy In vs Out")
    
    return chart

def create_improved_energy_balance_chart(df):
    """Create clear energy balance chart with proper legend and labeling"""
    if df.empty:
        return alt.Chart(pd.DataFrame()).mark_text(text="No data available", fontSize=16, color='gray')
    
    # Ensure date is datetime
    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'])
    
    # Separate positive (food) and negative (exercise/BMR) energy
    food_energy = df_copy[df_copy['energy'] > 0].groupby('date')['energy'].sum().fillna(0)
    exercise_energy = abs(df_copy[df_copy['energy'] < 0].groupby('date')['energy'].sum().fillna(0))
    
    # Create a clean dataframe for the chart
    chart_data = []
    for date in food_energy.index.union(exercise_energy.index):
        chart_data.append({
            'date': date,
            'Energy (kcal)': food_energy.get(date, 0),
            'Type': 'Food Intake'
        })
        chart_data.append({
            'date': date,
            'Energy (kcal)': exercise_energy.get(date, 0),
            'Type': 'Energy Burned'
        })
    
    chart_df = pd.DataFrame(chart_data)
    
    if chart_df.empty:
        return alt.Chart(pd.DataFrame()).mark_text(text="No data available", fontSize=16, color='gray')
    
    # Create the line chart with proper legend
    chart = alt.Chart(chart_df).mark_line(
        strokeWidth=3,
        point=alt.OverlayMarkDef(size=60)
    ).encode(
        x=alt.X('date:T', title='Date'),
        y=alt.Y('Energy (kcal):Q', title='Energy (kcal)', scale=alt.Scale(zero=False)),
        color=alt.Color(
            'Type:N',
            title='Energy Type',
            scale=alt.Scale(
                domain=['Food Intake', 'Energy Burned'],
                range=['#32CD32', '#FF4500']  # Green for intake, Orange for burned
            ),
            legend=alt.Legend(
                orient='top',
                titleFontSize=12,
                labelFontSize=11,
                symbolStrokeWidth=3,
                symbolSize=100,
                padding=10
            )
        ),
        tooltip=[
            alt.Tooltip('date:T', title='Date'),
            alt.Tooltip('Type:N', title='Type'),
            alt.Tooltip('Energy (kcal):Q', title='Energy', format='.0f')
        ]
    ).properties(
        width=700,
        height=350,
        title="Daily Energy Balance: Food Intake vs Energy Burned"
    )
    
    return chart

def get_available_activities(df):
    """Get list of available training activities"""
    # Standardize activity names before getting unique values
    df_copy = df.copy()
    df_copy['activity'] = df_copy['activity'].apply(standardize_activity_name)
    
    training_df = df_copy[df_copy['label'] == 'TRAINING']
    return sorted(training_df['activity'].unique().tolist())

def format_time_period(period_type, selected_date):
    """Format the time period for display"""
    if period_type == "Day":
        return selected_date.strftime("%Y-%m-%d")
    elif period_type == "Week":
        start_of_week = selected_date - timedelta(days=selected_date.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        return f"{start_of_week.strftime('%Y-%m-%d')} to {end_of_week.strftime('%Y-%m-%d')}"
    elif period_type == "Month":
        return selected_date.strftime("%Y-%m")
    return str(selected_date)

def safe_numeric_conversion(value, default=0.0):
    """Helper function for safe numeric conversion"""
    try:
        if pd.isna(value):
            return default
        str_val = str(value).strip()
        if str_val.lower() in ['', 'nan', 'none']:
            return default
        return float(str_val)
    except (ValueError, TypeError, AttributeError):
        return default

def calculate_energy_balance(df, period_name):
    """
    Calculate energy input vs output for a given dataframe
    
    Args:
        df: DataFrame containing energy data
        period_name: String description of the period
    
    Returns:
        Dictionary with input_energy, output_energy, net_balance, days_with_data
    """
    if df.empty:
        return {
            'period': period_name,
            'input_energy': 0,
            'output_energy': 0,
            'net_balance': 0,
            'days_with_data': 0
        }
    
    # Food posts are input energy (positive values)
    food_data = df[df['label'] == 'FOOD']
    input_energy = food_data['energy'].apply(lambda x: safe_numeric_conversion(x, 0)).sum()
    
    # REST and TRAINING posts are output energy (typically negative values, so we take absolute)
    output_data = df[df['label'].isin(['REST', 'TRAINING'])]
    output_energy = abs(output_data['energy'].apply(lambda x: safe_numeric_conversion(x, 0)).sum())
    
    # Net balance: input - output (negative = deficit, positive = surplus)
    net_balance = input_energy - output_energy
    
    # Count unique days with data
    days_with_data = df['date'].nunique() if 'date' in df.columns else 0
    
    return {
        'period': period_name,
        'input_energy': int(input_energy),
        'output_energy': int(output_energy), 
        'net_balance': int(net_balance),
        'days_with_data': days_with_data
    }

def check_consecutive_days(df, min_days=8):
    """
    Check if we have at least min_days consecutive days of data
    
    Args:
        df: DataFrame containing energy data with 'date' column
        min_days: Minimum number of consecutive days required
    
    Returns:
        Tuple (has_sufficient_consecutive_days, max_consecutive_found)
    """
    if df.empty:
        return False, 0
    
    # Get unique dates and sort them
    unique_dates = pd.to_datetime(df['date']).dt.date.unique()
    unique_dates = sorted(unique_dates)
    
    if len(unique_dates) < min_days:
        return False, len(unique_dates)
    
    # Check for consecutive days
    max_consecutive = 1
    current_consecutive = 1
    
    for i in range(1, len(unique_dates)):
        current_date = unique_dates[i]
        previous_date = unique_dates[i-1]
        
        # Check if dates are consecutive (difference of 1 day)
        if (current_date - previous_date).days == 1:
            current_consecutive += 1
            max_consecutive = max(max_consecutive, current_consecutive)
        else:
            current_consecutive = 1
    
    return max_consecutive >= min_days, max_consecutive

def get_deficit_analysis(df_energy, selected_date_input):
    """
    Get comprehensive deficit analysis for day, week, month, and overall periods
    
    Args:
        df_energy: Main energy dataframe
        selected_date_input: Selected date as datetime object
    
    Returns:
        Dictionary containing deficit analysis for all periods
    """
    from datetime import timedelta
    
    selected_date = pd.to_datetime(selected_date_input)
    
    # Day analysis - filter for selected date
    day_df = df_energy[pd.to_datetime(df_energy['date']).dt.date == selected_date.date()]
    day_balance = calculate_energy_balance(day_df, f"Day ({selected_date.strftime('%Y-%m-%d')})")
    
    # Week analysis - get week data (Monday to Sunday)
    week_start = selected_date - timedelta(days=selected_date.weekday())
    week_end = week_start + timedelta(days=6)
    week_df = df_energy[
        (pd.to_datetime(df_energy['date']).dt.date >= week_start.date()) & 
        (pd.to_datetime(df_energy['date']).dt.date <= week_end.date())
    ]
    week_balance = calculate_energy_balance(
        week_df, 
        f"Week ({week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')})"
    )
    
    # Month analysis - get month data
    month_start = selected_date.replace(day=1)
    if selected_date.month == 12:
        month_end = selected_date.replace(year=selected_date.year+1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = selected_date.replace(month=selected_date.month+1, day=1) - timedelta(days=1)
    
    month_df = df_energy[
        (pd.to_datetime(df_energy['date']).dt.date >= month_start.date()) & 
        (pd.to_datetime(df_energy['date']).dt.date <= month_end.date())
    ]
    month_balance = calculate_energy_balance(
        month_df, 
        f"Month ({month_start.strftime('%Y-%m')})"
    )
    
    # Overall analysis (8+ consecutive days)
    has_consecutive, max_consecutive = check_consecutive_days(df_energy, min_days=8)
    overall_analysis = None
    
    if has_consecutive:
        # Find the most recent consecutive period of 8+ days
        all_dates = sorted(pd.to_datetime(df_energy['date']).dt.date.unique(), reverse=True)
        
        consecutive_dates = [all_dates[0]]
        for i in range(1, len(all_dates)):
            current_date = all_dates[i]
            previous_date = consecutive_dates[-1]
            
            if (previous_date - current_date).days == 1:
                consecutive_dates.append(current_date)
                if len(consecutive_dates) >= 8:
                    break
            else:
                consecutive_dates = [all_dates[i]]
        
        if len(consecutive_dates) >= 8:
            start_date = min(consecutive_dates)
            end_date = max(consecutive_dates)
            
            consecutive_df = df_energy[
                (pd.to_datetime(df_energy['date']).dt.date >= start_date) & 
                (pd.to_datetime(df_energy['date']).dt.date <= end_date)
            ]
            
            overall_balance = calculate_energy_balance(
                consecutive_df, 
                f"{len(consecutive_dates)}-Day Period ({start_date} to {end_date})"
            )
            
            # Calculate daily average
            daily_avg = overall_balance['net_balance'] / len(consecutive_dates)
            
            overall_analysis = {
                'balance': overall_balance,
                'consecutive_days': len(consecutive_dates),
                'daily_average': int(daily_avg),
                'start_date': start_date,
                'end_date': end_date,
                'health_guidance': get_health_guidance(daily_avg)
            }
    
    return {
        'day': day_balance,
        'week': week_balance,
        'month': month_balance,
        'overall': overall_analysis,
        'has_sufficient_data': has_consecutive,
        'max_consecutive_days': max_consecutive
    }

def get_health_guidance(daily_avg):
    """
    Provide health guidance based on daily average deficit/surplus
    
    Args:
        daily_avg: Daily average energy balance (negative = deficit, positive = surplus)
    
    Returns:
        Dictionary with guidance type and message
    """
    if daily_avg < -500:
        return {
            'type': 'warning',
            'message': 'Large daily deficit - consider if this aligns with your health goals'
        }
    elif daily_avg > 500:
        return {
            'type': 'warning', 
            'message': 'Large daily surplus - consider if this aligns with your health goals'
        }
    else:
        return {
            'type': 'success',
            'message': 'Moderate energy balance'
        }