from flask import render_template, request, Blueprint
from service_status.external_connectivity import system_connectivity_status
from core.variables import *

home_bp = Blueprint("home", __name__)

@home_bp.route('/')
def index():
    message = None

    if not message:
        message = request.args.get('message')
    return render_template("index.html", system_status=system_connectivity_status, user=user, message=message)