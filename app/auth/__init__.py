from flask import Blueprint

bp = Blueprint('auth', __name__, template_folder='../templates/auth')

# Import routes and forms at the end
from app.auth import routes, forms 