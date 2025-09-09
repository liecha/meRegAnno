import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import statistics

def load_and_prepare_data():
    """Load and prepare the fitness/nutrition data for analysis"""
    df = pd.read_csv('data/updated-database-results.csv')
    df['date'] = pd.to_datetime(df['date'])
    df['datetime'] = pd.to_datetime(df['date'].astype(str) + ' ' + df['time'])
    return df

def analyze_activity_patterns(df):
    """Analyze activity patterns and trends"""
    results = {}
    
    # Filter for training activities
    training_df = df[df['label'] == 'TRAINING'].copy()
    
    # Activity frequency analysis
    activity_counts = training_df['activity'].value_counts()
    results['most_common_activities'] = activity_counts.head(5).to_dict()
    
    # Weekly activity analysis
    training_df['week'] = training_df['date'].dt.isocalendar().week
    training_df['year'] = training_df['date'].dt.year
    weekly_sessions = training_df.groupby(['year', 'week']).size()
    results['avg_weekly_sessions'] = weekly_sessions.mean()
    results['weekly_consistency'] = weekly_sessions.std()
    
    # Energy expenditure analysis
    daily_training_energy = training_df.groupby('date')['energy'].sum()
    results['avg_daily_training_energy'] = daily_training_energy.mean()
    results['training_energy_trend'] = analyze_trend(daily_training_energy)
    
    # Distance analysis for cardio activities
    distance_activities = training_df[training_df['distance'].notna() & (training_df['distance'] != '0')]
    if not distance_activities.empty:
        # Extract numeric distance values
        distance_activities['distance_km'] = distance_activities['distance'].str.extract('(\d+\.?\d*)').astype(float)
        results['avg_weekly_distance'] = distance_activities.groupby(
            distance_activities['date'].dt.to_period('W')
        )['distance_km'].sum().mean()
    
    return results

def analyze_nutrition_patterns(df):
    """Analyze nutrition patterns and eating habits"""
    results = {}
    
    # Filter for food entries
    food_df = df[df['label'] == 'FOOD'].copy()
    
    # Daily nutrition analysis
    daily_nutrition = food_df.groupby('date').agg({
        'energy': 'sum',
        'pro': 'sum',
        'carb': 'sum',
        'fat': 'sum'
    })
    
    results['avg_daily_calories'] = daily_nutrition['energy'].mean()
    results['avg_daily_protein'] = daily_nutrition['pro'].mean()
    results['avg_daily_carbs'] = daily_nutrition['carb'].mean()
    results['avg_daily_fat'] = daily_nutrition['fat'].mean()
    
    # Nutrition consistency
    results['calorie_consistency'] = daily_nutrition['energy'].std()
    results['protein_consistency'] = daily_nutrition['pro'].std()
    
    # Meal timing analysis
    food_df['hour'] = food_df['datetime'].dt.hour
    meal_timing = food_df['hour'].value_counts().sort_index()
    results['peak_eating_hours'] = meal_timing.nlargest(3).index.tolist()
    
    return results

def analyze_energy_balance(df):
    """Analyze overall energy balance and trends"""
    results = {}
    
    # Daily energy balance
    daily_balance = df.groupby('date')['energy_acc'].last()
    results['avg_daily_balance'] = daily_balance.mean()
    results['balance_trend'] = analyze_trend(daily_balance)
    
    # Deficit/surplus days
    deficit_days = (daily_balance < 0).sum()
    surplus_days = (daily_balance > 0).sum()
    total_days = len(daily_balance)
    
    results['deficit_day_percentage'] = (deficit_days / total_days) * 100
    results['surplus_day_percentage'] = (surplus_days / total_days) * 100
    
    # Weekly patterns
    df['weekday'] = df['date'].dt.dayofweek
    weekday_balance = df.groupby(['date', 'weekday'])['energy_acc'].last().groupby('weekday').mean()
    results['weekday_patterns'] = weekday_balance.to_dict()
    
    return results

def analyze_training_nutrition_correlation(df):
    """Analyze correlation between training and nutrition"""
    results = {}
    
    # Daily aggregations
    daily_training = df[df['label'] == 'TRAINING'].groupby('date')['energy'].sum()
    daily_nutrition = df[df['label'] == 'FOOD'].groupby('date').agg({
        'energy': 'sum',
        'pro': 'sum'
    })
    
    # Merge training and nutrition data
    combined = pd.merge(daily_training, daily_nutrition, left_index=True, right_index=True, suffixes=('_training', '_food'))
    
    if not combined.empty:
        # Correlation analysis
        training_nutrition_corr = combined['energy_training'].corr(combined['energy_food'])
        training_protein_corr = combined['energy_training'].corr(combined['pro'])
        
        results['training_nutrition_correlation'] = training_nutrition_corr
        results['training_protein_correlation'] = training_protein_corr
        
        # High training days analysis
        high_training_threshold = combined['energy_training'].quantile(0.75)
        high_training_days = combined[combined['energy_training'] >= high_training_threshold]
        
        results['high_training_avg_calories'] = high_training_days['energy_food'].mean()
        results['high_training_avg_protein'] = high_training_days['pro'].mean()
        results['regular_day_avg_calories'] = combined[combined['energy_training'] < high_training_threshold]['energy_food'].mean()
    
    return results

def analyze_trend(series):
    """Analyze trend in a time series (simple linear trend)"""
    if len(series) < 2:
        return "insufficient_data"
    
    x = np.arange(len(series))
    y = series.values
    
    # Remove NaN values
    mask = ~np.isnan(y)
    if sum(mask) < 2:
        return "insufficient_data"
    
    x_clean = x[mask]
    y_clean = y[mask]
    
    # Calculate slope
    slope = np.polyfit(x_clean, y_clean, 1)[0]
    
    if abs(slope) < 0.1:
        return "stable"
    elif slope > 0:
        return "increasing"
    else:
        return "decreasing"

def generate_insights(df):
    """Generate actionable insights based on the data"""
    insights = []
    
    # Analyze patterns
    activity_analysis = analyze_activity_patterns(df)
    nutrition_analysis = analyze_nutrition_patterns(df)
    balance_analysis = analyze_energy_balance(df)
    correlation_analysis = analyze_training_nutrition_correlation(df)
    
    # Generate specific insights
    if activity_analysis.get('weekly_consistency', 0) < 1:
        insights.append("Your training schedule is very consistent - great for building sustainable habits!")
    elif activity_analysis.get('weekly_consistency', 0) > 2:
        insights.append("Consider establishing a more consistent training routine for better results.")
    
    if balance_analysis.get('deficit_day_percentage', 0) > 70:
        insights.append("You're maintaining a caloric deficit most days - monitor energy levels and recovery.")
    
    if nutrition_analysis.get('avg_daily_protein', 0) < 80:
        insights.append("Consider increasing protein intake to support training and recovery.")
    
    # Training-specific insights
    walk_sessions = df[df['activity'] == 'Walk'].shape[0]
    total_sessions = df[df['label'] == 'TRAINING'].shape[0]
    if total_sessions > 0 and (walk_sessions / total_sessions) > 0.6:
        insights.append("Walking is your primary activity - consider adding strength training for balanced fitness.")
    
    # Nutrition timing insights
    peak_hours = nutrition_analysis.get('peak_eating_hours', [])
    if 4 in peak_hours or 5 in peak_hours:
        insights.append("Early morning eating detected - this could be related to your training schedule.")
    
    return insights

def create_comprehensive_summary():
    """Create a comprehensive summary of all analyses"""
    df = load_and_prepare_data()
    
    # Date range analysis
    date_range = {
        'start_date': df['date'].min(),
        'end_date': df['date'].max(),
        'total_days': (df['date'].max() - df['date'].min()).days + 1
    }
    
    # Run all analyses
    activity_analysis = analyze_activity_patterns(df)
    nutrition_analysis = analyze_nutrition_patterns(df)
    balance_analysis = analyze_energy_balance(df)
    correlation_analysis = analyze_training_nutrition_correlation(df)
    insights = generate_insights(df)
    
    # Compile summary
    summary = {
        'date_range': date_range,
        'activity_patterns': activity_analysis,
        'nutrition_patterns': nutrition_analysis,
        'energy_balance': balance_analysis,
        'training_nutrition_correlation': correlation_analysis,
        'actionable_insights': insights,
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return summary

def format_summary_for_display(summary):
    """Format the summary for nice display in the app"""
    formatted = {}
    
    # Overview section
    date_range = summary['date_range']
    formatted['overview'] = {
        'period': f"{date_range['start_date'].strftime('%Y-%m-%d')} to {date_range['end_date'].strftime('%Y-%m-%d')}",
        'total_days': date_range['total_days']
    }
    
    # Activity insights
    activity = summary['activity_patterns']
    formatted['activity_insights'] = {
        'weekly_sessions': f"{activity.get('avg_weekly_sessions', 0):.1f} sessions/week",
        'consistency': "High" if activity.get('weekly_consistency', 0) < 1.5 else "Moderate" if activity.get('weekly_consistency', 0) < 3 else "Variable",
        'avg_training_energy': f"{activity.get('avg_daily_training_energy', 0):.0f} kcal/day",
        'top_activities': list(activity.get('most_common_activities', {}).keys())[:3]
    }
    
    # Nutrition insights
    nutrition = summary['nutrition_patterns']
    formatted['nutrition_insights'] = {
        'avg_calories': f"{nutrition.get('avg_daily_calories', 0):.0f} kcal/day",
        'avg_protein': f"{nutrition.get('avg_daily_protein', 0):.0f} g/day",
        'consistency': "High" if nutrition.get('calorie_consistency', 0) < 200 else "Moderate" if nutrition.get('calorie_consistency', 0) < 400 else "Variable"
    }
    
    # Energy balance insights
    balance = summary['energy_balance']
    formatted['balance_insights'] = {
        'avg_balance': f"{balance.get('avg_daily_balance', 0):.0f} kcal/day",
        'deficit_days': f"{balance.get('deficit_day_percentage', 0):.0f}%",
        'trend': balance.get('balance_trend', 'stable').title()
    }
    
    # Key insights
    formatted['key_insights'] = summary['actionable_insights']
    
    return formatted

if __name__ == "__main__":
    # Generate and save summary
    summary = create_comprehensive_summary()
    formatted_summary = format_summary_for_display(summary)
    
    # Save raw summary for programmatic access
    import json
    with open('data/ai_analysis_summary.json', 'w') as f:
        json.dump(summary, f, default=str, indent=2)
    
    # Print formatted summary
    print("=== AI ANALYSIS SUMMARY ===")
    print(f"Analysis Period: {formatted_summary['overview']['period']}")
    print(f"Total Days Analyzed: {formatted_summary['overview']['total_days']}")
    print("\n--- ACTIVITY PATTERNS ---")
    for key, value in formatted_summary['activity_insights'].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\n--- NUTRITION PATTERNS ---")
    for key, value in formatted_summary['nutrition_insights'].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\n--- ENERGY BALANCE ---")
    for key, value in formatted_summary['balance_insights'].items():
        print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\n--- KEY INSIGHTS ---")
    for i, insight in enumerate(formatted_summary['key_insights'], 1):
        print(f"{i}. {insight}")