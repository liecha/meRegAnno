import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import altair as alt
import streamlit as st

def load_data():
    """Load the activity data"""
    df = pd.read_csv('data/updated-database-results.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'])
    return df

def get_date_range(center_date, period_type):
    """Get start and end dates based on period type"""
    center_date = pd.to_datetime(center_date)
    
    if period_type == "Day":
        start_date = center_date
        end_date = center_date
    elif period_type == "Week":
        # Get the Monday of the week containing center_date
        start_date = center_date - timedelta(days=center_date.weekday())
        end_date = start_date + timedelta(days=6)
    elif period_type == "Month":
        start_date = center_date.replace(day=1)
        # Get last day of month
        if center_date.month == 12:
            end_date = center_date.replace(year=center_date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            end_date = center_date.replace(month=center_date.month + 1, day=1) - timedelta(days=1)
    
    return start_date, end_date

def filter_data_by_period(df, center_date, period_type):
    """Filter data based on selected period"""
    start_date, end_date = get_date_range(center_date, period_type)
    return df[(df['date'] >= start_date) & (df['date'] <= end_date)]

def get_activity_summary(df, period_type, activity_filter=None):
    """Get activity summary for the selected period"""
    # Filter by activity type if specified
    if activity_filter and activity_filter != "All":
        df = df[df['activity'] == activity_filter]
    
    # Training activities only
    training_df = df[df['label'] == 'TRAINING'].copy()
    
    if training_df.empty:
        return {
            'total_sessions': 0,
            'total_energy': 0,
            'total_distance': 0,
            'avg_session_energy': 0,
            'activity_breakdown': {},
            'daily_totals': pd.DataFrame()
        }
    
    # Calculate metrics
    total_sessions = len(training_df)
    total_energy = training_df['energy'].sum()
    avg_session_energy = total_energy / total_sessions if total_sessions > 0 else 0
    
    # Distance calculation (extract numeric values)
    training_df['distance_numeric'] = training_df['distance'].str.extract('(\d+\.?\d*)').astype(float).fillna(0)
    total_distance = training_df['distance_numeric'].sum()
    
    # Activity breakdown
    activity_breakdown = training_df['activity'].value_counts().to_dict()
    
    # Daily totals for charting
    daily_totals = training_df.groupby('date').agg({
        'energy': 'sum',
        'distance_numeric': 'sum'
    }).reset_index()
    daily_totals['sessions'] = training_df.groupby('date').size().values
    
    return {
        'total_sessions': total_sessions,
        'total_energy': abs(total_energy),  # Make positive for display
        'total_distance': total_distance,
        'avg_session_energy': abs(avg_session_energy),
        'activity_breakdown': activity_breakdown,
        'daily_totals': daily_totals
    }

def get_nutrition_summary(df, period_type):
    """Get nutrition summary for the selected period"""
    food_df = df[df['label'] == 'FOOD'].copy()
    
    if food_df.empty:
        return {
            'total_calories': 0,
            'avg_daily_calories': 0,
            'total_protein': 0,
            'avg_daily_protein': 0,
            'total_carbs': 0,
            'total_fat': 0,
            'daily_nutrition': pd.DataFrame()
        }
    
    # Calculate totals
    total_calories = food_df['energy'].sum()
    total_protein = food_df['pro'].sum()
    total_carbs = food_df['carb'].sum()
    total_fat = food_df['fat'].sum()
    
    # Daily averages
    daily_nutrition = food_df.groupby('date').agg({
        'energy': 'sum',
        'pro': 'sum',
        'carb': 'sum',
        'fat': 'sum'
    }).reset_index()
    
    num_days = len(daily_nutrition)
    avg_daily_calories = total_calories / num_days if num_days > 0 else 0
    avg_daily_protein = total_protein / num_days if num_days > 0 else 0
    
    return {
        'total_calories': total_calories,
        'avg_daily_calories': avg_daily_calories,
        'total_protein': total_protein,
        'avg_daily_protein': avg_daily_protein,
        'total_carbs': total_carbs,
        'total_fat': total_fat,
        'daily_nutrition': daily_nutrition,
        'num_days': num_days
    }

def get_energy_balance_summary(df):
    """Get energy balance summary"""
    # Get the last energy_acc value for each day (end of day balance)
    daily_balance = df.groupby('date')['energy_acc'].last().reset_index()
    daily_balance = daily_balance.dropna()
    
    if daily_balance.empty:
        return {
            'avg_daily_balance': 0,
            'deficit_days': 0,
            'surplus_days': 0,
            'daily_balance': pd.DataFrame()
        }
    
    avg_balance = daily_balance['energy_acc'].mean()
    deficit_days = (daily_balance['energy_acc'] < 0).sum()
    surplus_days = (daily_balance['energy_acc'] > 0).sum()
    
    return {
        'avg_daily_balance': avg_balance,
        'deficit_days': deficit_days,
        'surplus_days': surplus_days,
        'daily_balance': daily_balance
    }

def create_activity_chart(daily_data, period_type):
    """Create activity visualization chart with colors for different activities"""
    if daily_data.empty:
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("No data available")
        )
    
    # Prepare data for chart
    chart_data = daily_data.copy()
    chart_data['date_str'] = chart_data['date'].dt.strftime('%Y-%m-%d')
    
    # Define color scale for activities
    activity_colors = {
        'WALK': '#1f77b4',      # Blue
        'RUN': '#ff7f0e',       # Orange  
        'BIKE': '#2ca02c',      # Green
        'SWIM': '#d62728',      # Red
        'STRENGTH': '#9467bd',  # Purple
        'YOGA': '#8c564b',      # Brown
        'STR': '#9467bd'        # Purple (same as STRENGTH)
    }
    
    # Create stacked bar chart to show multiple activities per day
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('date_str:O', title='Date', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('energy:Q', title='Energy Burned (kcal)'),
        color=alt.Color('activity:N', 
                       title='Activity Type',
                       scale=alt.Scale(
                           domain=list(activity_colors.keys()),
                           range=list(activity_colors.values())
                       )),
        tooltip=['date_str:O', 'activity:N', 'energy:Q']
    ).properties(
        width=600,
        height=300,
        title=f'Daily Training Energy by Activity - {period_type} View'
    )
    
    return chart

def create_nutrition_chart(daily_nutrition):
    """Create nutrition visualization chart"""
    if daily_nutrition.empty:
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("No data available")
        )
    
    # Prepare data for stacked chart
    chart_data = daily_nutrition.copy()
    chart_data['date_str'] = chart_data['date'].dt.strftime('%Y-%m-%d')
    
    # Melt the data for stacked chart
    melted_data = pd.melt(
        chart_data, 
        id_vars=['date_str'], 
        value_vars=['pro', 'carb', 'fat'],
        var_name='nutrient',
        value_name='grams'
    )
    
    # Create stacked bar chart
    nutrition_chart = alt.Chart(melted_data).mark_bar().encode(
        x=alt.X('date_str:O', title='Date', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('grams:Q', title='Grams'),
        color=alt.Color('nutrient:N', 
                       scale=alt.Scale(domain=['pro', 'carb', 'fat'], 
                                     range=['#ff7f0e', '#2ca02c', '#d62728']),
                       legend=alt.Legend(title="Macronutrients")),
        tooltip=['date_str:O', 'nutrient:N', 'grams:Q']
    ).properties(
        width=600,
        height=300,
        title='Daily Macronutrient Intake'
    )
    
    return nutrition_chart

def create_energy_balance_chart(daily_balance):
    """Create energy balance visualization"""
    if daily_balance.empty:
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("No data available")
        )
    
    chart_data = daily_balance.copy()
    chart_data['date_str'] = chart_data['date'].dt.strftime('%Y-%m-%d')
    chart_data['balance_type'] = chart_data['energy_acc'].apply(
        lambda x: 'Surplus' if x > 0 else 'Deficit' if x < 0 else 'Balanced'
    )
    
    balance_chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('date_str:O', title='Date', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('energy_acc:Q', title='Energy Balance (kcal)'),
        color=alt.Color('balance_type:N',
                       scale=alt.Scale(domain=['Deficit', 'Balanced', 'Surplus'],
                                     range=['#d62728', '#17becf', '#2ca02c']),
                       legend=alt.Legend(title="Balance Type")),
        tooltip=['date_str:O', 'energy_acc:Q', 'balance_type:N']
    ).properties(
        width=600,
        height=300,
        title='Daily Energy Balance'
    )
    
    # Add a zero line
    zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
        color='black', strokeDash=[3, 3]
    ).encode(y='y:Q')
    
    return balance_chart + zero_line

def get_training_nutrition_correlation(df):
    """Analyze correlation between training days and nutrition intake"""
    # Get daily totals
    daily_training = df[df['label'] == 'TRAINING'].groupby('date')['energy'].sum().abs()
    daily_nutrition = df[df['label'] == 'FOOD'].groupby('date').agg({
        'energy': 'sum',
        'pro': 'sum'
    })
    
    # Merge data
    combined = pd.merge(daily_training, daily_nutrition, 
                       left_index=True, right_index=True, 
                       suffixes=('_training', '_nutrition'), how='outer').fillna(0)
    
    if len(combined) < 2:
        return None, pd.DataFrame()
    
    # Calculate correlation
    correlation = combined['energy_training'].corr(combined['energy_nutrition'])
    
    # Prepare data for scatter plot
    scatter_data = combined.reset_index()
    scatter_data['date_str'] = scatter_data['date'].dt.strftime('%Y-%m-%d')
    
    return correlation, scatter_data

def create_correlation_chart(scatter_data, correlation):
    """Create training vs nutrition correlation chart"""
    if scatter_data.empty:
        return alt.Chart(pd.DataFrame()).mark_text().encode(
            text=alt.value("No data available")
        )
    
    # Scatter plot
    scatter = alt.Chart(scatter_data).mark_circle(size=60).encode(
        x=alt.X('energy_training:Q', title='Training Energy Burned (kcal)'),
        y=alt.Y('energy_nutrition:Q', title='Nutrition Energy Intake (kcal)'),
        tooltip=['date_str:O', 'energy_training:Q', 'energy_nutrition:Q']
    )
    
    # Trend line
    trend = scatter.transform_regression('energy_training', 'energy_nutrition').mark_line()
    
    chart = (scatter + trend).properties(
        width=500,
        height=400,
        title=f'Training vs Nutrition Correlation (r = {correlation:.2f})'
    ).resolve_scale(color='independent')
    
    return chart

def get_available_activities(df):
    """Get list of available activities for filtering"""
    activities = df[df['label'] == 'TRAINING']['activity'].unique()
    return ['All'] + sorted([act for act in activities if pd.notna(act)])

def format_period_summary(period_type, start_date, end_date):
    """Format period summary text"""
    if period_type == "Day":
        return f"Summary for {start_date.strftime('%Y-%m-%d (%A)')}"
    elif period_type == "Week":
        return f"Week summary: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    elif period_type == "Month":
        return f"Month summary: {start_date.strftime('%B %Y')}"
    
    return f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

def calculate_weekly_averages(df, center_date):
    """Calculate weekly averages for comparison"""
    # Get 4 weeks of data around the center date
    week_start = center_date - timedelta(days=center_date.weekday() + 21)  # 3 weeks before
    week_end = center_date + timedelta(days=(6 - center_date.weekday()) + 7)  # 1 week after
    
    period_data = df[(df['date'] >= week_start) & (df['date'] <= week_end)]
    
    # Group by week
    period_data['week_start'] = period_data['date'] - pd.to_timedelta(period_data['date'].dt.dayofweek, unit='d')
    
    weekly_stats = {}
    
    # Training stats
    training_weekly = period_data[period_data['label'] == 'TRAINING'].groupby('week_start').agg({
        'energy': lambda x: abs(x).sum(),
        'activity': 'count'
    })
    
    if not training_weekly.empty:
        weekly_stats['avg_weekly_training_energy'] = training_weekly['energy'].mean()
        weekly_stats['avg_weekly_sessions'] = training_weekly['activity'].mean()
    
    # Nutrition stats
    nutrition_weekly = period_data[period_data['label'] == 'FOOD'].groupby('week_start').agg({
        'energy': 'sum',
        'pro': 'sum'
    })
    
    if not nutrition_weekly.empty:
        weekly_stats['avg_weekly_calories'] = nutrition_weekly['energy'].mean()
        weekly_stats['avg_weekly_protein'] = nutrition_weekly['pro'].mean()
    
    return weekly_stats