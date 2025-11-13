from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles):
    """Allow access only to users with given roles."""
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            if current_user.role not in roles and current_user.role != "Admin":
                abort(403)

            return fn(*args, **kwargs)
        return decorated_view
    return wrapper
