from flask import jsonify
from functools import wraps

def validate_request(required_fields=None):
    """
    Decorator to validate request data
    
    Args:
        required_fields (list): List of required field names in the request JSON
    
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get JSON data from request
            data = request.get_json()
            
            # Check if JSON data is present
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Request must contain valid JSON'
                }), 400
                
            # Check required fields if specified
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    return jsonify({
                        'success': False,
                        'error': f'Missing required fields: {", ".join(missing_fields)}'
                    }), 400
                    
            # All validations passed, proceed to the handler
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator


def sanitize_input(data):
    """
    Sanitize and validate input data
    
    Args:
        data (dict): Input data to sanitize
        
    Returns:
        dict: Sanitized data
    """
    if not isinstance(data, dict):
        return {}
    
    # Sanitize string values (basic example)
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Remove potentially harmful characters or patterns
            sanitized[key] = value.strip()
        elif isinstance(value, dict):
            # Recursively sanitize nested dictionaries
            sanitized[key] = sanitize_input(value)
        elif isinstance(value, list):
            # Sanitize items in lists
            if all(isinstance(item, dict) for item in value):
                sanitized[key] = [sanitize_input(item) for item in value]
            elif all(isinstance(item, str) for item in value):
                sanitized[key] = [item.strip() for item in value]
            else:
                sanitized[key] = value
        else:
            # Keep other types as is
            sanitized[key] = value
            
    return sanitized