from flask import request, Blueprint, render_template
from helpers.logs import log_handling
from service_status.external_connectivity import system_connectivity_status
from core.variables import *

connectivity_observability_handling_bp = Blueprint("connectivity_observability_handling", __name__)

@connectivity_observability_handling_bp.route(connectivity_observability_endpoint)
def cluster_observability():
    message = None
    external_connection = request.args.get("external_connection")

    connectivity_status = []

    if not message:
        message = request.args.get('message')

    if not external_connection:
        connectivity_status = system_connectivity_status
    else:
        for connectivity in system_connectivity_status:
            if connectivity.get(name_key) == external_connection:
                connectivity_status.append(connectivity)
                break

    log_handling({
        "message": f"Connectivity observability endpoint called",
        "level": "info",
        "module": "connectivity_observability",
        "client_ip": request.remote_addr,
    })

    return render_template("connectivity_observability.html", system_status=system_connectivity_status, connectivity_status=connectivity_status, user=user, message=message)