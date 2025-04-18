from flask import Blueprint

bp = Blueprint('admin', __name__, template_folder='../templates/admin', url_prefix='/admin')

# Import routes, forms, etc. at the end
from app.admin import routes, forms 