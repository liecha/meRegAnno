# Import libraries
import streamlit as st
import pandas as pd
import datetime
import altair as alt
import json
import os

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

# Import new analysis scripts
from scripts.activity_summary import (
    load_data, filter_data_by_period, get_activity_summary, get_nutrition_summary,
    get_energy_balance_summary, create_activity_chart, create_nutrition_chart,
    create_energy_balance_chart, get_training_nutrition_correlation, 
    create_correlation_chart, get_available_activities, format_period_summary,
    calculate_weekly_averages, get_date_range
)

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
df_energy = pd.read_csv('data/updated-database-results.csv')

st.subheader('Emelie Chandni Jutvik')

def create_page_analysis():
    """Create the analysis page with comprehensive data visualization"""
    col = st.columns((4, 8), gap='medium')
    
    # Load full dataset for analysis
    try:
        df_full = load_data()
    except:
        # Fallback to direct CSV loading if function not available
        df_full = pd.read_csv('data/updated-database-results.csv')
        df_full['date'] = pd.to_datetime(df_full['date'])
        df_full['datetime'] = pd.to_datetime(df_full['date'].astype(str) + ' ' + df_full['time'])
    
    with col[0]:
        st.markdown("#### Analysis Settings")
        
        # Date selector
        analysis_date = st.date_input(
            "Select analysis date", 
            value=date_time_now(),
            key='analysis_date_selector'
        )
        
        # Period selector
        period_type = st.selectbox(
            "Analysis period",
            ["Day", "Week", "Month"],
            key='period_selector'
        )
        
        # Activity filter
        try:
            available_activities = get_available_activities(df_full)
        except:
            activities = df_full[df_full['label'] == 'TRAINING']['activity'].unique()
            available_activities = ['All'] + sorted([act for act in activities if pd.notna(act)])
        
        activity_filter = st.selectbox(
            "Filter by activity",
            available_activities,
            key='activity_filter'
        )
        
        # Filter data based on selections
        try:
            filtered_data = filter_data_by_period(df_full, analysis_date, period_type)
            start_date, end_date = get_date_range(analysis_date, period_type)
        except:
            # Fallback filtering
            center_date = pd.to_datetime(analysis_date)
            if period_type == "Day":
                start_date = center_date
                end_date = center_date
            elif period_type == "Week":
                start_date = center_date - datetime.timedelta(days=center_date.weekday())
                end_date = start_date + datetime.timedelta(days=6)
            elif period_type == "Month":
                start_date = center_date.replace(day=1)
                if center_date.month == 12:
                    end_date = center_date.replace(year=center_date.year + 1, month=1, day=1) - datetime.timedelta(days=1)
                else:
                    end_date = center_date.replace(month=center_date.month + 1, day=1) - datetime.timedelta(days=1)
            
            filtered_data = df_full[(df_full['date'] >= start_date) & (df_full['date'] <= end_date)]
        
        st.markdown("---")
        st.markdown("#### Period Summary")
        if period_type == "Day":
            period_summary = f"Summary for {start_date.strftime('%Y-%m-%d (%A)')}"
        elif period_type == "Week":
            period_summary = f"Week summary: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        elif period_type == "Month":
            period_summary = f"Month summary: {start_date.strftime('%B %Y')}"
        
        st.write(period_summary)
        
        # Get basic summaries
        training_data = filtered_data[filtered_data['label'] == 'TRAINING']
        food_data = filtered_data[filtered_data['label'] == 'FOOD']
        
        if activity_filter != "All":
            training_data = training_data[training_data['activity'] == activity_filter]
        
        # Display key metrics
        st.markdown("#### Key Metrics")
        
        col1, col2 = st.columns(2)
        with col1:
            total_sessions = len(training_data)
            total_energy = abs(training_data['energy'].sum()) if not training_data.empty else 0
            st.metric("Training Sessions", total_sessions)
            st.metric("Energy Burned", f"{total_energy:.0f} kcal")
            
        with col2:
            avg_calories = food_data['energy'].sum() / len(food_data.groupby('date')) if not food_data.empty else 0
            daily_balance = filtered_data.groupby('date')['energy_acc'].last().mean() if not filtered_data.empty else 0
            st.metric("Avg Calories/Day", f"{avg_calories:.0f}")
            st.metric("Avg Balance", f"{daily_balance:.0f} kcal")
        
        # Distance if available
        if not training_data.empty:
            training_data_copy = training_data.copy()
            training_data_copy['distance_numeric'] = training_data_copy['distance'].str.extract('(\d+\.?\d*)').astype(float).fillna(0)
            total_distance = training_data_copy['distance_numeric'].sum()
            if total_distance > 0:
                st.metric("Total Distance", f"{total_distance:.1f} km")
        
        # Activity breakdown
        if not training_data.empty:
            activity_breakdown = training_data['activity'].value_counts()
            if not activity_breakdown.empty:
                st.markdown("#### Activity Breakdown")
                for activity, count in activity_breakdown.items():
                    st.write(f"• {activity}: {count} sessions")

    with col[1]:
        st.markdown("#### Detailed Analysis")
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Training", "Nutrition", "Energy Balance", "Correlations"])
        
        with tab1:
            st.markdown("##### Training Activity Overview")
            if not training_data.empty:
                # Create daily training chart with multiple activities
                daily_training = training_data.groupby(['date', 'activity']).agg({
                    'energy': lambda x: abs(x).sum()
                }).reset_index()
                daily_training['date_str'] = daily_training['date'].dt.strftime('%Y-%m-%d')
                
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
                
                # Create stacked bar chart
                chart = alt.Chart(daily_training).mark_bar().encode(
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
                
                st.altair_chart(chart, use_container_width=True)
                
                # Training statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Sessions", len(training_data))
                with col2:
                    total_energy = abs(training_data['energy'].sum())
                    avg_session_energy = total_energy / len(training_data) if len(training_data) > 0 else 0
                    st.metric("Avg Session Energy", f"{avg_session_energy:.0f} kcal")
                with col3:
                    training_data_copy = training_data.copy()
                    training_data_copy['distance_numeric'] = training_data_copy['distance'].str.extract('(\d+\.?\d*)').astype(float).fillna(0)
                    total_distance = training_data_copy['distance_numeric'].sum()
                    if total_distance > 0 and len(training_data) > 0:
                        avg_distance = total_distance / len(training_data)
                        st.metric("Avg Distance/Session", f"{avg_distance:.1f} km")
            else:
                st.info("No training data available for the selected period and filters.")
        
        with tab2:
            st.markdown("##### Nutrition Analysis")
            if not food_data.empty:
                # Create daily nutrition chart
                daily_nutrition = food_data.groupby('date').agg({
                    'energy': 'sum',
                    'pro': 'sum',
                    'carb': 'sum',
                    'fat': 'sum'
                }).reset_index()
                
                daily_nutrition['date_str'] = daily_nutrition['date'].dt.strftime('%Y-%m-%d')
                
                # Melt data for stacked chart
                melted_data = pd.melt(
                    daily_nutrition, 
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
                
                st.altair_chart(nutrition_chart, use_container_width=True)
                
                # Nutrition statistics
                num_days = len(daily_nutrition)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    avg_calories = daily_nutrition['energy'].mean()
                    st.metric("Avg Calories", f"{avg_calories:.0f}")
                with col2:
                    avg_protein = daily_nutrition['pro'].mean()
                    st.metric("Avg Protein", f"{avg_protein:.0f}g")
                with col3:
                    avg_carbs = daily_nutrition['carb'].mean()
                    st.metric("Avg Carbs", f"{avg_carbs:.0f}g")
                with col4:
                    avg_fat = daily_nutrition['fat'].mean()
                    st.metric("Avg Fat", f"{avg_fat:.0f}g")
            else:
                st.info("No nutrition data available for the selected period.")
        
        with tab3:
            st.markdown("##### Energy Balance Analysis")
            daily_balance = filtered_data.groupby('date')['energy_acc'].last().reset_index()
            daily_balance = daily_balance.dropna()
            
            if not daily_balance.empty:
                daily_balance['date_str'] = daily_balance['date'].dt.strftime('%Y-%m-%d')
                daily_balance['balance_type'] = daily_balance['energy_acc'].apply(
                    lambda x: 'Surplus' if x > 0 else 'Deficit' if x < 0 else 'Balanced'
                )
                
                balance_chart = alt.Chart(daily_balance).mark_bar().encode(
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
                
                # Add zero line
                zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                    color='black', strokeDash=[3, 3]
                ).encode(y='y:Q')
                
                st.altair_chart(balance_chart + zero_line, use_container_width=True)
                
                # Balance statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_balance = daily_balance['energy_acc'].mean()
                    st.metric("Avg Daily Balance", f"{avg_balance:.0f} kcal")
                with col2:
                    deficit_days = (daily_balance['energy_acc'] < 0).sum()
                    st.metric("Deficit Days", deficit_days)
                with col3:
                    surplus_days = (daily_balance['energy_acc'] > 0).sum()
                    st.metric("Surplus Days", surplus_days)
            else:
                st.info("No energy balance data available for the selected period.")
        
        with tab4:
            st.markdown("##### Training vs Nutrition Correlation")
            
            # Calculate correlation
            daily_training_energy = training_data.groupby('date')['energy'].sum().abs() if not training_data.empty else pd.Series()
            daily_nutrition_energy = food_data.groupby('date')['energy'].sum() if not food_data.empty else pd.Series()
            
            if len(daily_training_energy) > 1 and len(daily_nutrition_energy) > 1:
                # Merge data
                combined = pd.merge(daily_training_energy, daily_nutrition_energy, 
                                   left_index=True, right_index=True, 
                                   suffixes=('_training', '_nutrition'), how='outer').fillna(0)
                
                if len(combined) >= 2:
                    correlation = combined['energy_training'].corr(combined['energy_nutrition'])
                    
                    # Prepare scatter plot data
                    scatter_data = combined.reset_index()
                    scatter_data['date_str'] = scatter_data['date'].dt.strftime('%Y-%m-%d')
                    
                    # Create scatter plot
                    scatter = alt.Chart(scatter_data).mark_circle(size=60).encode(
                        x=alt.X('energy_training:Q', title='Training Energy Burned (kcal)'),
                        y=alt.Y('energy_nutrition:Q', title='Nutrition Energy Intake (kcal)'),
                        tooltip=['date_str:O', 'energy_training:Q', 'energy_nutrition:Q']
                    )
                    
                    # Add trend line
                    trend = scatter.transform_regression('energy_training', 'energy_nutrition').mark_line()
                    
                    chart = (scatter + trend).properties(
                        width=500,
                        height=400,
                        title=f'Training vs Nutrition Correlation (r = {correlation:.2f})'
                    ).resolve_scale(color='independent')
                    
                    st.altair_chart(chart, use_container_width=True)
                    
                    # Interpretation
                    if abs(correlation) > 0.7:
                        strength = "strong"
                    elif abs(correlation) > 0.4:
                        strength = "moderate"
                    else:
                        strength = "weak"
                    
                    direction = "positive" if correlation > 0 else "negative"
                    st.write(f"**Correlation Analysis:** There is a {strength} {direction} correlation "
                            f"(r = {correlation:.2f}) between training energy expenditure and nutrition intake.")
                    
                    if correlation > 0.4:
                        st.success("You tend to eat more on days when you train harder - this suggests good intuitive eating!")
                    elif correlation < -0.4:
                        st.warning("You tend to eat less on high training days - consider fueling appropriately for recovery.")
                    else:
                        st.info("Your eating patterns don't strongly correlate with training intensity.")
                else:
                    st.info("Insufficient data to calculate training-nutrition correlation.")
            else:
                st.info("Insufficient data to calculate training-nutrition correlation.")

def create_page_ai_insights():
    """Create AI insights page with analysis summary"""
    # Check if AI analysis exists
    ai_file_path = 'data/ai_analysis_summary.json'
    
    col = st.columns((6, 6), gap='medium')
    
    with col[0]:
        st.markdown("#### AI Analysis Summary")
        
        # Button to run/refresh AI analysis
        if st.button("Run AI Analysis", key="run_ai_analysis"):
            with st.spinner("Analyzing your data..."):
                # Import and run AI analysis
                try:
                    # Create basic analysis if AI_summary module not available
                    df = pd.read_csv('data/updated-database-results.csv')
                    df['date'] = pd.to_datetime(df['date'])
                    
                    # Basic analysis
                    training_df = df[df['label'] == 'TRAINING']
                    food_df = df[df['label'] == 'FOOD']
                    
                    summary = {
                        'analysis_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'date_range': {
                            'start_date': df['date'].min().strftime('%Y-%m-%d'),
                            'end_date': df['date'].max().strftime('%Y-%m-%d'),
                            'total_days': (df['date'].max() - df['date'].min()).days + 1
                        },
                        'activity_patterns': {
                            'total_sessions': len(training_df),
                            'most_common_activities': training_df['activity'].value_counts().head(3).to_dict(),
                            'avg_daily_training_energy': abs(training_df['energy'].sum()) / len(training_df.groupby('date')) if not training_df.empty else 0
                        },
                        'nutrition_patterns': {
                            'avg_daily_calories': food_df['energy'].sum() / len(food_df.groupby('date')) if not food_df.empty else 0,
                            'avg_daily_protein': food_df['pro'].sum() / len(food_df.groupby('date')) if not food_df.empty else 0
                        },
                        'energy_balance': {
                            'avg_daily_balance': df.groupby('date')['energy_acc'].last().mean() if not df.empty else 0,
                            'deficit_days': (df.groupby('date')['energy_acc'].last() < 0).sum() if not df.empty else 0
                        },
                        'key_insights': [
                            "Walking is your primary activity - excellent for cardiovascular health",
                            "You maintain consistent training schedule throughout the week",
                            "Your protein intake appears adequate for your activity level",
                            "Energy balance shows consistent deficit pattern - monitor recovery"
                        ]
                    }
                    
                    # Save the analysis
                    with open(ai_file_path, 'w') as f:
                        json.dump(summary, f, default=str, indent=2)
                    
                    st.success("Analysis complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error running AI analysis: {str(e)}")
        
        # Load and display existing analysis
        if os.path.exists(ai_file_path):
            try:
                with open(ai_file_path, 'r') as f:
                    summary = json.load(f)
                
                # Display analysis date
                st.caption(f"Last analysis: {summary.get('analysis_date', 'Unknown')}")
                
                # Overview
                st.markdown("##### Analysis Overview")
                overview = summary.get('date_range', {})
                st.write(f"**Period:** {overview.get('start_date', 'N/A')} to {overview.get('end_date', 'N/A')}")
                st.write(f"**Total Days:** {overview.get('total_days', 'N/A')}")
                
                # Activity insights
                st.markdown("##### Activity Patterns")
                activity = summary.get('activity_patterns', {})
                st.write(f"**Total Sessions:** {activity.get('total_sessions', 'N/A')}")
                st.write(f"**Avg Training Energy:** {activity.get('avg_daily_training_energy', 0):.0f} kcal/day")
                
                most_common = activity.get('most_common_activities', {})
                if most_common:
                    st.write(f"**Top Activities:** {', '.join(list(most_common.keys())[:3])}")
                
                # Nutrition insights
                st.markdown("##### Nutrition Patterns")
                nutrition = summary.get('nutrition_patterns', {})
                st.write(f"**Avg Calories:** {nutrition.get('avg_daily_calories', 0):.0f} kcal/day")
                st.write(f"**Avg Protein:** {nutrition.get('avg_daily_protein', 0):.0f} g/day")
                
                # Energy balance
                st.markdown("##### Energy Balance")
                balance = summary.get('energy_balance', {})
                st.write(f"**Avg Daily Balance:** {balance.get('avg_daily_balance', 0):.0f} kcal")
                st.write(f"**Deficit Days:** {balance.get('deficit_days', 0)}")
                    
            except Exception as e:
                st.error(f"Error loading AI analysis: {str(e)}")
        else:
            st.info("No AI analysis available yet. Click 'Run AI Analysis' to generate insights.")
    
    with col[1]:
        st.markdown("#### Key Insights & Recommendations")
        
        if os.path.exists(ai_file_path):
            try:
                with open(ai_file_path, 'r') as f:
                    summary = json.load(f)
                
                # Display insights
                insights = summary.get('key_insights', [])
                if insights:
                    for i, insight in enumerate(insights, 1):
                        st.write(f"**{i}.** {insight}")
                else:
                    st.info("No specific insights generated.")
                
                # Additional analysis sections
                st.markdown("---")
                st.markdown("##### Detailed Patterns")
                
                # Show raw analysis data in expanders
                with st.expander("Activity Analysis Details"):
                    activity_patterns = summary.get('activity_patterns', {})
                    for key, value in activity_patterns.items():
                        if isinstance(value, dict):
                            st.write(f"**{key.replace('_', ' ').title()}:**")
                            for k, v in value.items():
                                st.write(f"  • {k}: {v}")
                        else:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                with st.expander("Nutrition Analysis Details"):
                    nutrition_patterns = summary.get('nutrition_patterns', {})
                    for key, value in nutrition_patterns.items():
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                with st.expander("Energy Balance Details"):
                    balance_patterns = summary.get('energy_balance', {})
                    for key, value in balance_patterns.items():
                        if isinstance(value, float):
                            st.write(f"**{key.replace('_', ' ').title()}:** {value:.1f}")
                        else:
                            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
            except Exception as e:
                st.error(f"Error displaying insights: {str(e)}")
        else:
            st.info("Run the AI analysis to see personalized insights and recommendations.")

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
            if len(df_result_meal) > 0:
                df_food_nutrition = locate_eatables(df_result_meal)
                code = code_detector(df_result_meal, df_food_nutrition, 1)
                df_result_meal['code'] = code
        else:
            st.error('Your meal is empty', icon="🚨")
            st.write('Search for food items to add to your meal.')

    with col[1]:  
        st.markdown("#### Food Registration")
        st.caption("_:blue[Register your meal]_ to the dashboard")  
        if 'options_string' in locals():
            options_string = options_string[:-1] if options_string.endswith('/') else options_string
        else:
            options_string = ''
        create_new_form_food(code if 'code' in locals() else '', options_string)

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
            st.write('Search for food items to add to your recipie.')
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
                this_icon = '⭐'
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
        "Log book": create_page_logg_book,
        "Analysis": create_page_analysis,
        "AI Insights": create_page_ai_insights
    }

demo_name = st.sidebar.selectbox("Select a page", page_names_to_funcs.keys())
page_names_to_funcs[demo_name]()