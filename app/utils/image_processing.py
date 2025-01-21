ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png', 'gif', 'webp'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
