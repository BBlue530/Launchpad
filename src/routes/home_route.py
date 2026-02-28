from flask import render_template, request, Blueprint
from helpers.logs import log_handling
from service_status.external_connectivity import system_connectivity_status
from core.variables import *

home_bp = Blueprint("home", __name__)

@home_bp.route('/')
def index():
    message = None

    if not message:
        message = request.args.get('message')

    log_handling({
        "message": f"Index endpoint called",
        "level": "info",
        "module": "index",
        "client_ip": request.remote_addr,
    })

    return render_template("index.html", system_status=system_connectivity_status, user=user, message=message)