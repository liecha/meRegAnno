# error_handling.py - Comprehensive Error Management Module for meRegAnno App
import streamlit as st
import pandas as pd
import traceback
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List, Callable
from contextlib import contextmanager
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app_errors.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base exception for application errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.details = details or {}
        super().__init__(message)

class DatabaseError(AppError):
    """Database-related errors"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, "DATABASE_ERROR", details)

class ValidationError(AppError):
    """Validation-related errors"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class FileOperationError(AppError):
    """File operation errors"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, "FILE_ERROR", details)

class DataProcessingError(AppError):
    """Data processing errors"""
    def __init__(self, message: str, details: Dict = None):
        super().__init__(message, "DATA_ERROR", details)

class ErrorHandler:
    """Main error handler class for the application"""
    
    def __init__(self):
        self.error_counts = {}
        self.last_errors = {}
        
    def log_error(self, error: Exception, context: str = None):
        """Log error details for debugging"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context,
            'traceback': traceback.format_exc()
        }
        
        logger.error(f"Error in {context}: {error_info}")
        
        # Track error frequency
        error_key = f"{context}:{type(error).__name__}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = error_info
    
    def show_user_error(self, error: Exception, context: str = None, show_details: bool = False):
        """Show user-friendly error message in Streamlit"""
        
        # Log the error first
        self.log_error(error, context)
        
        # Determine user-friendly message based on error type
        if isinstance(error, DatabaseError):
            self._show_database_error(error, show_details)
        elif isinstance(error, ValidationError):
            self._show_validation_error(error, show_details)
        elif isinstance(error, FileOperationError):
            self._show_file_error(error, show_details)
        elif isinstance(error, DataProcessingError):
            self._show_data_error(error, show_details)
        else:
            self._show_generic_error(error, context, show_details)
    
    def _show_database_error(self, error: DatabaseError, show_details: bool = False):
        """Handle database errors"""
        st.error("Database Connection Issue")
        
        if "connection" in error.message.lower():
            st.warning(
                "Unable to connect to the database. "
                "The app will continue using local file storage. "
                "Please check your internet connection or database settings."
            )
        elif "permission" in error.message.lower():
            st.error(
                "Database permission error. "
                "Please check your database access rights."
            )
        elif "timeout" in error.message.lower():
            st.warning(
                "Database operation timed out. "
                "Please try again in a moment."
            )
        else:
            st.error(
                "A database error occurred. "
                "Your data has been saved locally as a backup."
            )
        
        if show_details:
            with st.expander("Technical Details"):
                st.code(error.message)
    
    def _show_validation_error(self, error: ValidationError, show_details: bool = False):
        """Handle validation errors"""
        st.error("Input Validation Error")
        st.error(error.message)
        
        if error.details:
            st.info("Please correct the following issues:")
            for field, issue in error.details.items():
                st.write(f"• {field}: {issue}")
    
    def _show_file_error(self, error: FileOperationError, show_details: bool = False):
        """Handle file operation errors"""
        st.error("File Operation Error")
        
        if "not found" in error.message.lower():
            st.warning(
                "A required file was not found. "
                "The app will create a new file automatically."
            )
        elif "permission" in error.message.lower():
            st.error(
                "File permission error. "
                "Please check that the app has write access to the data directory."
            )
        else:
            st.error(
                "An error occurred while accessing files. "
                "Please ensure the data directory is accessible."
            )
        
        if show_details:
            with st.expander("Technical Details"):
                st.code(error.message)
    
    def _show_data_error(self, error: DataProcessingError, show_details: bool = False):
        """Handle data processing errors"""
        st.error("Data Processing Error")
        
        if "nutrition" in error.message.lower():
            st.warning(
                "There was an issue calculating nutrition information. "
                "Please verify your food items are in the database."
            )
        elif "calculation" in error.message.lower():
            st.error(
                "Error in calculations. "
                "Please check your input values and try again."
            )
        else:
            st.error(
                "An error occurred while processing your data. "
                "Please try again or contact support if the issue persists."
            )
        
        if show_details:
            with st.expander("Technical Details"):
                st.code(error.message)
    
    def _show_generic_error(self, error: Exception, context: str = None, show_details: bool = False):
        """Handle generic errors"""
        st.error("An unexpected error occurred")
        
        context_msg = f" while {context}" if context else ""
        st.error(f"Something went wrong{context_msg}. Please try again.")
        
        # Provide helpful suggestions based on context
        if context:
            if "registration" in context.lower():
                st.info("Try refreshing the page and re-entering your data.")
            elif "database" in context.lower():
                st.info("The app will continue using local storage.")
            elif "calculation" in context.lower():
                st.info("Please verify your input values.")
        
        if show_details:
            with st.expander("Technical Details"):
                st.code(str(error))

# Global error handler instance
error_handler = ErrorHandler()

# Decorator for handling errors in functions
def handle_errors(context: str = None, show_user_error: bool = True, fallback_value=None):
    """
    Decorator to automatically handle errors in functions
    
    Args:
        context: Context description for error logging
        show_user_error: Whether to show error to user
        fallback_value: Value to return if error occurs
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                func_context = context or f"function {func.__name__}"
                
                if show_user_error:
                    error_handler.show_user_error(e, func_context)
                else:
                    error_handler.log_error(e, func_context)
                
                return fallback_value
        return wrapper
    return decorator

# Context manager for handling errors in code blocks
@contextmanager
def error_context(context: str, show_user_error: bool = True, reraise: bool = False):
    """
    Context manager for handling errors in code blocks
    
    Args:
        context: Context description
        show_user_error: Whether to show error to user
        reraise: Whether to reraise the exception after handling
    """
    try:
        yield
    except Exception as e:
        if show_user_error:
            error_handler.show_user_error(e, context)
        else:
            error_handler.log_error(e, context)
        
        if reraise:
            raise

# Database operation error handlers
def handle_database_operation(operation_name: str):
    """Handle database operations with automatic error handling"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Convert to appropriate error type
                if "connection" in str(e).lower() or "timeout" in str(e).lower():
                    raise DatabaseError(f"Database connection failed during {operation_name}: {str(e)}")
                elif "permission" in str(e).lower() or "privilege" in str(e).lower():
                    raise DatabaseError(f"Database permission error during {operation_name}: {str(e)}")
                else:
                    raise DatabaseError(f"Database error during {operation_name}: {str(e)}")
        return wrapper
    return decorator

# File operation error handlers
def handle_file_operation(operation_name: str):
    """Handle file operations with automatic error handling"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                raise FileOperationError(f"File not found during {operation_name}: {str(e)}")
            except PermissionError as e:
                raise FileOperationError(f"Permission denied during {operation_name}: {str(e)}")
            except Exception as e:
                raise FileOperationError(f"File operation failed during {operation_name}: {str(e)}")
        return wrapper
    return decorator

# Validation error helpers
def safe_validate(validation_func: Callable, *args, **kwargs):
    """
    Safely run validation function and return user-friendly results
    
    Args:
        validation_func: Validation function to run
        *args, **kwargs: Arguments for validation function
    
    Returns:
        Validation result or None if error occurred
    """
    try:
        return validation_func(*args, **kwargs)
    except Exception as e:
        error_handler.show_user_error(
            ValidationError(f"Validation failed: {str(e)}"),
            "input validation"
        )
        return None

# Streamlit-specific error handling
def show_error_state(error_message: str, details: str = None, suggestions: List[str] = None):
    """
    Show a comprehensive error state in Streamlit
    
    Args:
        error_message: Main error message
        details: Additional details
        suggestions: List of suggestions for user
    """
    st.error(error_message)
    
    if details:
        with st.expander("More details"):
            st.write(details)
    
    if suggestions:
        st.info("What you can try:")
        for suggestion in suggestions:
            st.write(f"• {suggestion}")

def show_retry_button(key: str, callback: Callable = None):
    """
    Show a retry button for failed operations
    
    Args:
        key: Unique key for the button
        callback: Function to call when retry is clicked
    """
    if st.button("Retry", key=f"retry_{key}"):
        if callback:
            try:
                callback()
                st.success("Operation completed successfully!")
                st.rerun()
            except Exception as e:
                error_handler.show_user_error(e, "retry operation")

# Data validation and error recovery
def safe_dataframe_operation(df: pd.DataFrame, operation: Callable, fallback_df: pd.DataFrame = None):
    """
    Safely perform operations on DataFrames with error handling
    
    Args:
        df: Input DataFrame
        operation: Function to perform on DataFrame
        fallback_df: Fallback DataFrame if operation fails
    
    Returns:
        Result of operation or fallback DataFrame
    """
    if df is None or df.empty:
        st.warning("No data available for this operation")
        return fallback_df or pd.DataFrame()
    
    try:
        return operation(df)
    except Exception as e:
        error_handler.show_user_error(
            DataProcessingError(f"Data operation failed: {str(e)}"),
            "data processing"
        )
        return fallback_df or df

# Form validation helpers
def validate_form_submission(validation_results: List, form_name: str = "form"):
    """
    Validate form submission and show appropriate messages
    
    Args:
        validation_results: List of validation results
        form_name: Name of the form for error messages
    
    Returns:
        bool: True if form can be submitted
    """
    has_errors = False
    error_count = 0
    warning_count = 0
    
    for result in validation_results:
        if result and hasattr(result, 'errors'):
            for error in result.errors:
                st.error(error)
                has_errors = True
                error_count += 1
        
        if result and hasattr(result, 'warnings'):
            for warning in result.warnings:
                st.warning(warning)
                warning_count += 1
    
    if has_errors:
        st.error(f"Cannot submit {form_name} - please fix {error_count} error(s) above")
        return False
    
    if warning_count > 0:
        st.info(f"Form has {warning_count} warning(s) but can still be submitted")
    
    return True

# Loading and progress indicators
@contextmanager
def loading_indicator(message: str = "Processing..."):
    """
    Context manager to show loading indicator during operations
    
    Args:
        message: Loading message to display
    """
    progress_placeholder = st.empty()
    try:
        with progress_placeholder:
            st.info(f"{message}")
        yield
    finally:
        progress_placeholder.empty()

# Recovery and backup helpers
def create_error_recovery_point(data: Dict[str, Any], context: str):
    """
    Create a recovery point for data in case of errors
    
    Args:
        data: Data to backup
        context: Context for the backup
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_key = f"backup_{context}_{timestamp}"
        st.session_state[backup_key] = data
        
        # Keep only last 5 backups per context
        backup_keys = [k for k in st.session_state.keys() if k.startswith(f"backup_{context}_")]
        if len(backup_keys) > 5:
            oldest_key = sorted(backup_keys)[0]
            del st.session_state[oldest_key]
            
    except Exception as e:
        logger.error(f"Failed to create recovery point: {e}")

def restore_from_recovery_point(context: str) -> Optional[Dict[str, Any]]:
    """
    Restore data from the most recent recovery point
    
    Args:
        context: Context to restore from
    
    Returns:
        Restored data or None if no recovery point exists
    """
    try:
        backup_keys = [k for k in st.session_state.keys() if k.startswith(f"backup_{context}_")]
        if backup_keys:
            latest_key = sorted(backup_keys)[-1]
            return st.session_state.get(latest_key)
    except Exception as e:
        logger.error(f"Failed to restore from recovery point: {e}")
    
    return None

# Error reporting and diagnostics
def show_error_diagnostics():
    """Show error diagnostics page for debugging"""
    st.header("Error Diagnostics")
    
    if error_handler.error_counts:
        st.subheader("Error Frequency")
        error_df = pd.DataFrame([
            {"Context": k.split(':')[0], "Error Type": k.split(':')[1], "Count": v}
            for k, v in error_handler.error_counts.items()
        ])
        st.dataframe(error_df)
        
        st.subheader("Recent Errors")
        for error_key, error_info in error_handler.last_errors.items():
            with st.expander(f"{error_key} - {error_info['timestamp']}"):
                st.json(error_info)
    else:
        st.success("No errors recorded in this session")

# Export error handling functions for easy importing
__all__ = [
    'AppError', 'DatabaseError', 'ValidationError', 'FileOperationError', 'DataProcessingError',
    'ErrorHandler', 'error_handler',
    'handle_errors', 'error_context', 'handle_database_operation', 'handle_file_operation',
    'safe_validate', 'show_error_state', 'show_retry_button', 'safe_dataframe_operation',
    'validate_form_submission', 'loading_indicator', 'create_error_recovery_point',
    'restore_from_recovery_point', 'show_error_diagnostics'
]