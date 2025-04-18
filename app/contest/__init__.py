from flask import Blueprint

bp = Blueprint('contest', __name__, template_folder='../templates/contest')

# Import routes and forms at the end
from app.contest import routes, forms 