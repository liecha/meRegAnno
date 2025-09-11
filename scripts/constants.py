# ===================== APP METADATA =====================
APP_NAME = "Lumina"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Personal Health and Nutrition Tracking Application"
APP_ICON = "🔆"

# ===================== DATABASE CONFIGURATION =====================
# Data storage paths
DATA_PATHS = {
    'energy_data': 'data/updated-database-results.csv',
    'food_database': 'data/livsmedelsdatabas.csv',
    'recipe_database': 'data/recipie_databas.csv',
    'meal_database': 'data/meal_databas.csv'
}

# Database table mappings
TABLE_MAPPINGS = {
    'data/updated-database-results.csv': 'energy_balance',
    'data/livsmedelsdatabas.csv': 'livsmedelsdatabas', 
    'data/recipie_databas.csv': 'recipie_databas',
    'data/meal_databas.csv': 'recipie_databas'  # Legacy mapping
}

# ===================== ACTIVITY CONSTANTS =====================
ACTIVITY_TYPES = [
    "Walk", "Run", "Swim", "Bike", "Strength", "Yoga"
]

ACTIVITY_EMOJIS = {
    'Walk': ['🚶‍♂️', '🚶', '👟'],
    'Run': ['🏃‍♂️', '🏃', '💨'],
    'Bike': ['🚴‍♂️', '🚴', '🚲'],
    'Swim': ['🏊‍♂️', '🏊', '🏊‍♀️'],
    'Strength': ['💪', '🏋️‍♂️', '🏋️'],
    'Yoga': ['🧘‍♂️', '🧘', '🧘‍♀️'],
    'FOOD': ['🍽️', '🍴', '🥗']
}

ACTIVITY_COLORS = {
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

# Activity-specific default values
ACTIVITY_DEFAULTS = {
    'Walk': {'has_distance': True, 'has_pace': False, 'has_steps': True},
    'Run': {'has_distance': True, 'has_pace': True, 'has_steps': True},
    'Bike': {'has_distance': True, 'has_pace': True, 'has_steps': False},
    'Swim': {'has_distance': True, 'has_pace': True, 'has_steps': False, 'distance_unit': 'meters'},
    'Strength': {'has_distance': False, 'has_pace': False, 'has_steps': False},
    'Yoga': {'has_distance': False, 'has_pace': False, 'has_steps': False}
}

# ===================== VALIDATION CONSTANTS =====================
# BMR parameter ranges
BMR_LIMITS = {
    'weight': {'min': 30.0, 'max': 300.0, 'warning_low': 40.0, 'warning_high': 150.0},
    'height': {'min': 100.0, 'max': 250.0, 'warning_low': 140.0, 'warning_high': 220.0},
    'age': {'min': 10, 'max': 100, 'warning_low': 15, 'warning_high': 80}
}

# Activity validation limits
ACTIVITY_LIMITS = {
    'energy': {'max': 2000, 'warning_high': 1500},
    'distance': {'max': 100, 'warning_high': 50},  # km
    'pace': {'min': 2, 'max': 20, 'warning_fast': 3, 'warning_slow': 15},  # min/km
    'steps': {'max': 50000, 'warning_high': 30000},
    'duration': {'max_hours': 24}
}

# Swimming specific limits (different from other activities)
SWIMMING_LIMITS = {
    'distance': {'max': 10000, 'warning_high': 5000},  # meters
    'pace': {'min': 1, 'max': 10, 'warning_fast': 1.5, 'warning_slow': 5}  # min/100m
}

# Nutrition validation limits
NUTRITION_LIMITS = {
    'calories': {'max': 5000, 'warning_high': 3000},
    'protein': {'max': 500, 'warning_high': 200},
    'carbs': {'max': 500, 'warning_high': 300},
    'fat': {'max': 500, 'warning_high': 150},
    'meal_weight': {'min': 50, 'max': 5000, 'warning_low': 100, 'warning_high': 2000}  # grams
}

# ===================== UI CONSTANTS =====================
# Form validation messages
VALIDATION_MESSAGES = {
    'date_required': "📅 Please select a date before submitting",
    'time_required': "🕐 Please select a time before submitting",
    'activity_required': "🏃 Please select an activity type",
    'meal_empty': "🍽️ Please add at least one food item to your meal",
    'name_required': "📝 Name cannot be empty",
    'invalid_duration': "⏱️ Duration must be in format HH:MM:SS",
    'negative_energy': "💪 Energy burned cannot be negative",
    'invalid_nutrition_code': "📋 Nutrition code must be in format: kcal/protein/carb/fat"
}

# Success messages
SUCCESS_MESSAGES = {
    'activity_saved': "Activity registered successfully!",
    'meal_saved': "Meal registered successfully!",
    'recipe_saved': "Recipe saved successfully!",
    'food_item_saved': "Food item added successfully!"
}

# Page names and navigation
PAGE_NAMES = {
    'Dashboard': 'Dashboard',
    'Activity': 'Activity Registration', 
    'Meals': 'Meal Registration',
    'Database': 'Food Database',
    'Log book': 'Log Book',
    'Summary': 'Activity Summary'
}

# Column configurations for data tables
TABLE_COLUMN_CONFIGS = {
    'activity_summary': {
        "time": {"width": "small", "required": True},
        "summary": {"width": "large", "required": True}
    },
    'energy_deficit': {
        "date_text": {"width": "small", "required": True},
        "energy_acc": {"width": "small", "required": True}
    },
    'meal_composition': {
        "Food": {"width": "large", "required": True},
        "Amount (g)": {"width": "small", "required": True}
    },
    'recipe_ingredients': {
        "livsmedel": {"width": "large", "required": True},
        "amount": {"width": "small", "required": True}
    }
}

# ===================== CHART AND VISUALIZATION CONSTANTS =====================
CHART_TYPES = [
    "Energy Burned",
    "Distance", 
    "Weekly Distribution",
    "Energy Balance"
]

TIME_PERIODS = [
    "Day",
    "Week", 
    "Month"
]

# Chart colors and styling
CHART_COLORS = {
    'energy_in': '#32CD32',    # Lime Green
    'energy_out': '#FF4500',   # Orange Red
    'balance_line': '#FF0000'  # Red
}

# ===================== FORM DEFAULTS =====================
DEFAULT_VALUES = {
    'activity_form': {
        'duration': '00:00:00',
        'distance': 0.0,
        'pace': 0.0,
        'energy': 0,
        'steps': 0,
        'note': ''
    },
    'food_form': {
        'meal_code': '',
        'meal_note': '',
        'mark_favorite': False
    },
    'recipe_form': {
        'recipe_name': '',
        'portions': 1,
        'is_favorite': False
    },
    'user_settings': {
        'weight': 50.0,
        'height': 170.0,
        'age': 43
    }
}

# ===================== ERROR HANDLING CONSTANTS =====================
ERROR_CODES = {
    'VALIDATION_ERROR': 'VALIDATION_ERROR',
    'DATABASE_ERROR': 'DATABASE_ERROR', 
    'FILE_ERROR': 'FILE_ERROR',
    'DATA_ERROR': 'DATA_ERROR',
    'GENERAL_ERROR': 'GENERAL_ERROR'
}

# Error retry settings
RETRY_SETTINGS = {
    'max_retries': 3,
    'retry_delay': 1.0,  # seconds
    'backoff_factor': 2.0
}

# ===================== DATA PROCESSING CONSTANTS =====================
# CSV column mappings
CSV_COLUMNS = {
    'energy_balance': [
        'date', 'time', 'label', 'activity', 'distance', 'energy', 
        'pro', 'carb', 'fat', 'note', 'energy_acc', 'protein_acc', 
        'duration', 'pace', 'steps'
    ],
    'food_database': [
        'livsmedel', 'calorie', 'protein', 'carb', 'fat'
    ],
    'recipe_database': [
        'name', 'livsmedel', 'amount', 'code', 'favorite'
    ],
    'meal_database': [
        'date', 'time', 'name', 'livsmedel', 'amount', 'code', 'favorite'
    ]
}

# Data type mappings
DATA_TYPES = {
    'energy_balance': {
        'energy': 'int64',
        'pro': 'float64',
        'carb': 'float64', 
        'fat': 'float64',
        'distance': 'float64',
        'pace': 'float64',
        'steps': 'int64'
    }
}

# ===================== NUTRITION CALCULATION CONSTANTS =====================
# Macronutrient calories per gram
MACRO_CALORIES = {
    'protein': 4,
    'carbohydrates': 4,
    'fat': 9,
    'alcohol': 7  # if needed later
}

# Daily recommended values (can be customized per user)
DAILY_RECOMMENDATIONS = {
    'protein_percent': {'min': 10, 'max': 35},
    'carb_percent': {'min': 45, 'max': 65},
    'fat_percent': {'min': 20, 'max': 35}
}

# ===================== SESSION STATE KEYS =====================
SESSION_STATE_KEYS = {
    'user_settings': 'user_settings',
    'activity_form': 'activity_form',
    'food_form': 'food_form',
    'meal_creation': 'meal_creation',
    'recipe_creation': 'recipe_creation',
    'navigation': 'navigation',
    'notifications': 'notifications',
    'data_state': 'data_state'
}

# ===================== BACKUP AND RECOVERY CONSTANTS =====================
BACKUP_SETTINGS = {
    'max_backups_per_context': 5,
    'backup_expiry_hours': 24,
    'auto_backup_interval': 300  # seconds
}

# ===================== LOGGING CONFIGURATION =====================
LOG_SETTINGS = {
    'log_file': 'app_errors.log',
    'log_level': 'ERROR',
    'max_log_size': 10 * 1024 * 1024,  # 10MB
    'backup_count': 5
}

# ===================== HELPER FUNCTIONS =====================
def get_activity_emoji(activity: str, index: int = 0) -> str:
    """Get emoji for activity type"""
    emojis = ACTIVITY_EMOJIS.get(activity, ['⚡'])
    return emojis[min(index, len(emojis) - 1)]

def get_activity_color(activity: str) -> str:
    """Get color for activity type"""
    return ACTIVITY_COLORS.get(activity, '#808080')

def get_validation_limit(category: str, field: str, limit_type: str) -> float:
    """Get validation limit for a specific field"""
    limits = ACTIVITY_LIMITS.get(field, {})
    if category == 'swimming' and field in SWIMMING_LIMITS:
        limits = SWIMMING_LIMITS[field]
    return limits.get(limit_type, 0)

def get_table_config(table_type: str) -> dict:
    """Get column configuration for data tables"""
    return TABLE_COLUMN_CONFIGS.get(table_type, {})

def get_default_value(form_type: str, field: str):
    """Get default value for form field"""
    return DEFAULT_VALUES.get(form_type, {}).get(field)

# ===================== FEATURE FLAGS =====================
FEATURE_FLAGS = {
    'enable_database_mode': True,
    'enable_meal_copying': True,
    'enable_recipe_portions': True,
    'enable_advanced_validation': True,
    'enable_error_recovery': True,
    'enable_form_persistence': True,
    'enable_notifications': True,
    'show_debug_info': False,
    'enable_export_import': False  # Future feature
}

# ===================== API ENDPOINTS (if using external services) =====================
API_ENDPOINTS = {
    'nutrition_api': None,  # Placeholder for future nutrition API
    'backup_service': None,  # Placeholder for cloud backup
    'analytics': None  # Placeholder for analytics
}

# Export key constants for easy importing
__all__ = [
    'APP_NAME', 'ACTIVITY_TYPES', 'ACTIVITY_EMOJIS', 'ACTIVITY_COLORS',
    'VALIDATION_MESSAGES', 'SUCCESS_MESSAGES', 'PAGE_NAMES', 'CHART_TYPES', 'TIME_PERIODS',
    'DEFAULT_VALUES', 'ERROR_CODES', 'CSV_COLUMNS', 'FEATURE_FLAGS',
    'get_activity_emoji', 'get_activity_color', 'get_validation_limit', 
    'get_table_config', 'get_default_value'
]