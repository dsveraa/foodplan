from functools import wraps
from flask import abort, session

def moderator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_role = session.get('role')
        
        if user_role != 'moderator':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
