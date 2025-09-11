# state_management.py - Centralized Session State Management for meRegAnno App
import streamlit as st
import pandas as pd
from datetime import datetime, date, time
from typing import Dict, Any, Optional, List, Union
import json

class StateManager:
    """Centralized state management for the meRegAnno app"""
    
    def __init__(self):
        self.state_defaults = {
            # User settings
            'user_settings': {
                'weight': 50.0,
                'height': 170.0,
                'age': 43,
                'bmr': 1187
            },
            
            # Activity form state
            'activity_form': {
                'selected_date': None,
                'selected_time': None,
                'activity_type': '',
                'duration': '00:00:00',
                'distance': 0.0,
                'pace': 0.0,
                'energy': 0,
                'steps': 0,
                'note': '',
                'validation_errors': [],
                'form_dirty': False
            },
            
            # Food/meal form state
            'food_form': {
                'selected_date': None,
                'selected_time': None,
                'meal_code': '',
                'meal_note': '',
                'mark_favorite': False,
                'current_meal_items': None,
                'validation_errors': [],
                'form_dirty': False
            },
            
            # Meal creation state
            'meal_creation': {
                'selected_recipes': [],
                'recipe_portions': {},
                'selected_foods': [],
                'meal_composition': None,
                'copied_meal_items': [],
                'selected_previous_meal': None,
                'show_meal_modal': False
            },
            
            # Recipe creation state
            'recipe_creation': {
                'recipe_name': '',
                'selected_foods': [],
                'recipe_composition': None,
                'portions': 1,
                'is_favorite': False,
                'validation_errors': [],
                'form_dirty': False
            },
            
            # Food database state
            'food_database': {
                'new_food_name': '',
                'new_food_calories': 0.0,
                'new_food_protein': 0.0,
                'new_food_carb': 0.0,
                'new_food_fat': 0.0,
                'validation_errors': [],
                'form_dirty': False
            },
            
            # App navigation state
            'navigation': {
                'current_page': 'Dashboard',
                'previous_page': None,
                'page_history': []
            },
            
            # Error and notification state
            'notifications': {
                'error_messages': [],
                'warning_messages': [],
                'success_messages': [],
                'info_messages': []
            },
            
            # Data loading state
            'data_state': {
                'last_data_refresh': None,
                'data_loading': False,
                'data_error': None
            },
            
            # Summary page state
            'summary': {
                'period_type': 'Day',
                'selected_activities': [],
                'chart_type': 'Energy Burned'
            }
        }
    
    def initialize_state(self):
        """Initialize all session state variables with defaults if they don't exist"""
        for category, defaults in self.state_defaults.items():
            if category not in st.session_state:
                st.session_state[category] = defaults.copy()
            else:
                # Add any missing keys from defaults
                for key, value in defaults.items():
                    if key not in st.session_state[category]:
                        st.session_state[category][key] = value
    
    def get_state(self, category: str, key: str = None, default=None):
        """
        Get a state value safely
        
        Args:
            category: State category (e.g., 'activity_form')
            key: Specific key within category (optional)
            default: Default value if not found
        
        Returns:
            State value or default
        """
        if category not in st.session_state:
            return default
        
        if key is None:
            return st.session_state[category]
        
        return st.session_state[category].get(key, default)
    
    def set_state(self, category: str, key: str = None, value: Any = None, **kwargs):
        """
        Set state value(s)
        
        Args:
            category: State category
            key: Specific key (if updating single value)
            value: Value to set (if updating single value)
            **kwargs: Multiple key-value pairs to update
        """
        if category not in st.session_state:
            st.session_state[category] = {}
        
        if key is not None and value is not None:
            st.session_state[category][key] = value
        
        # Update multiple values
        for k, v in kwargs.items():
            st.session_state[category][k] = v
    
    def update_state(self, category: str, updates: Dict[str, Any]):
        """
        Update multiple state values in a category
        
        Args:
            category: State category
            updates: Dictionary of key-value pairs to update
        """
        if category not in st.session_state:
            st.session_state[category] = {}
        
        st.session_state[category].update(updates)
    
    def clear_state(self, category: str, keys: Union[str, List[str]] = None):
        """
        Clear state values
        
        Args:
            category: State category
            keys: Specific key(s) to clear, or None to clear all
        """
        if category not in st.session_state:
            return
        
        if keys is None:
            # Clear entire category
            st.session_state[category] = self.state_defaults.get(category, {}).copy()
        elif isinstance(keys, str):
            # Clear single key
            if keys in st.session_state[category]:
                default_value = self.state_defaults.get(category, {}).get(keys)
                st.session_state[category][keys] = default_value
        elif isinstance(keys, list):
            # Clear multiple keys
            defaults = self.state_defaults.get(category, {})
            for key in keys:
                if key in st.session_state[category]:
                    st.session_state[category][key] = defaults.get(key)
    
    def mark_form_dirty(self, category: str):
        """Mark a form as having unsaved changes"""
        self.set_state(category, 'form_dirty', True)
    
    def mark_form_clean(self, category: str):
        """Mark a form as saved/clean"""
        self.set_state(category, 'form_dirty', False)
    
    def is_form_dirty(self, category: str) -> bool:
        """Check if a form has unsaved changes"""
        return self.get_state(category, 'form_dirty', False)
    
    def add_notification(self, message: str, notification_type: str = 'info'):
        """
        Add a notification message
        
        Args:
            message: Notification message
            notification_type: Type of notification ('error', 'warning', 'success', 'info')
        """
        key = f"{notification_type}_messages"
        current_messages = self.get_state('notifications', key, [])
        current_messages.append({
            'message': message,
            'timestamp': datetime.now(),
            'read': False
        })
        self.set_state('notifications', key, current_messages)
    
    def get_notifications(self, notification_type: str = None, unread_only: bool = False) -> List[Dict]:
        """
        Get notification messages
        
        Args:
            notification_type: Filter by type ('error', 'warning', 'success', 'info')
            unread_only: Only return unread notifications
        
        Returns:
            List of notification dictionaries
        """
        if notification_type:
            key = f"{notification_type}_messages"
            messages = self.get_state('notifications', key, [])
        else:
            # Get all notifications
            messages = []
            for msg_type in ['error', 'warning', 'success', 'info']:
                key = f"{msg_type}_messages"
                type_messages = self.get_state('notifications', key, [])
                for msg in type_messages:
                    msg['type'] = msg_type
                messages.extend(type_messages)
        
        if unread_only:
            messages = [msg for msg in messages if not msg.get('read', False)]
        
        return messages
    
    def clear_notifications(self, notification_type: str = None):
        """Clear notification messages"""
        if notification_type:
            key = f"{notification_type}_messages"
            self.set_state('notifications', key, [])
        else:
            # Clear all notifications
            self.update_state('notifications', {
                'error_messages': [],
                'warning_messages': [],
                'success_messages': [],
                'info_messages': []
            })
    
    def set_page(self, page_name: str):
        """Set current page and update navigation history"""
        current_page = self.get_state('navigation', 'current_page')
        page_history = self.get_state('navigation', 'page_history', [])
        
        if current_page and current_page != page_name:
            page_history.append(current_page)
            # Keep only last 10 pages in history
            if len(page_history) > 10:
                page_history = page_history[-10:]
        
        self.update_state('navigation', {
            'previous_page': current_page,
            'current_page': page_name,
            'page_history': page_history
        })
    
    def get_previous_page(self) -> Optional[str]:
        """Get the previous page name"""
        return self.get_state('navigation', 'previous_page')
    
    def save_form_backup(self, category: str, form_data: Dict[str, Any]):
        """Save form data as backup in case of errors"""
        backup_key = f"{category}_backup"
        backup_data = {
            'data': form_data,
            'timestamp': datetime.now().isoformat(),
            'page': self.get_state('navigation', 'current_page')
        }
        st.session_state[backup_key] = backup_data
    
    def restore_form_backup(self, category: str) -> Optional[Dict[str, Any]]:
        """Restore form data from backup"""
        backup_key = f"{category}_backup"
        if backup_key in st.session_state:
            backup_data = st.session_state[backup_key]
            return backup_data.get('data')
        return None
    
    def clear_form_backup(self, category: str):
        """Clear form backup data"""
        backup_key = f"{category}_backup"
        if backup_key in st.session_state:
            del st.session_state[backup_key]
    
    def export_state(self) -> Dict[str, Any]:
        """Export current state for debugging or backup"""
        exportable_state = {}
        for category in self.state_defaults.keys():
            if category in st.session_state:
                exportable_state[category] = st.session_state[category].copy()
        return exportable_state
    
    def import_state(self, state_data: Dict[str, Any]):
        """Import state data"""
        for category, data in state_data.items():
            if category in self.state_defaults:
                st.session_state[category] = data
    
    def validate_state_integrity(self) -> List[str]:
        """Validate state integrity and return any issues found"""
        issues = []
        
        for category, defaults in self.state_defaults.items():
            if category not in st.session_state:
                issues.append(f"Missing state category: {category}")
                continue
            
            current_state = st.session_state[category]
            if not isinstance(current_state, dict):
                issues.append(f"Invalid state type for {category}: expected dict, got {type(current_state)}")
                continue
            
            # Check for missing required keys
            for key in defaults.keys():
                if key not in current_state:
                    issues.append(f"Missing key '{key}' in category '{category}'")
        
        return issues
    
    def reset_to_defaults(self, categories: Union[str, List[str]] = None):
        """Reset state to defaults"""
        if categories is None:
            categories = list(self.state_defaults.keys())
        elif isinstance(categories, str):
            categories = [categories]
        
        for category in categories:
            if category in self.state_defaults:
                st.session_state[category] = self.state_defaults[category].copy()

# Global state manager instance
state_manager = StateManager()

# Convenience functions for common operations
def init_state():
    """Initialize all state - call this at app startup"""
    state_manager.initialize_state()

def get_user_settings() -> Dict[str, Any]:
    """Get user settings (weight, height, age, BMR)"""
    return state_manager.get_state('user_settings', default={})

def update_user_settings(**kwargs):
    """Update user settings"""
    state_manager.update_state('user_settings', kwargs)

def get_form_state(form_type: str) -> Dict[str, Any]:
    """Get form state for a specific form type"""
    return state_manager.get_state(form_type, default={})

def update_form_state(form_type: str, **kwargs):
    """Update form state"""
    state_manager.update_state(form_type, kwargs)
    state_manager.mark_form_dirty(form_type)

def clear_form_state(form_type: str):
    """Clear form state"""
    state_manager.clear_state(form_type)

def save_form_backup(form_type: str, form_data: Dict[str, Any]):
    """Save form backup"""
    state_manager.save_form_backup(form_type, form_data)

def restore_form_backup(form_type: str) -> Optional[Dict[str, Any]]:
    """Restore form backup"""
    return state_manager.restore_form_backup(form_type)

def add_success_message(message: str):
    """Add success notification"""
    state_manager.add_notification(message, 'success')

def add_error_message(message: str):
    """Add error notification"""
    state_manager.add_notification(message, 'error')

def add_warning_message(message: str):
    """Add warning notification"""
    state_manager.add_notification(message, 'warning')

def add_info_message(message: str):
    """Add info notification"""
    state_manager.add_notification(message, 'info')

def show_notifications():
    """Display all unread notifications in Streamlit"""
    notifications = state_manager.get_notifications(unread_only=True)
    
    for notification in notifications:
        msg_type = notification.get('type', 'info')
        message = notification['message']
        
        if msg_type == 'error':
            st.error(message)
        elif msg_type == 'warning':
            st.warning(message)
        elif msg_type == 'success':
            st.success(message)
        else:
            st.info(message)
        
        # Mark as read
        notification['read'] = True

def clear_all_notifications():
    """Clear all notifications"""
    state_manager.clear_notifications()

# Context manager for form state management
class FormStateManager:
    """Context manager for handling form state automatically"""
    
    def __init__(self, form_type: str, auto_backup: bool = True):
        self.form_type = form_type
        self.auto_backup = auto_backup
        self.initial_state = None
    
    def __enter__(self):
        self.initial_state = get_form_state(self.form_type)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and self.auto_backup:
            # Error occurred, save backup
            current_state = get_form_state(self.form_type)
            save_form_backup(self.form_type, current_state)
        elif exc_type is None:
            # Success, clear backup
            state_manager.clear_form_backup(self.form_type)

# Export main functions and classes
__all__ = [
    'StateManager', 'state_manager', 'FormStateManager',
    'init_state', 'get_user_settings', 'update_user_settings',
    'get_form_state', 'update_form_state', 'clear_form_state',
    'save_form_backup', 'restore_form_backup',
    'add_success_message', 'add_error_message', 'add_warning_message', 'add_info_message',
    'show_notifications', 'clear_all_notifications'
]