from flask import url_for

def get_static_url(filename):
    return url_for('static', filename=filename) if filename else None
