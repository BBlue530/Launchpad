from flask import request, Blueprint, render_template
from cluster_handling.list_namespaces import list_all_namespaces, list_unique_release_namespaces, list_unique_release_name_namespace_services
from service_status.external_connectivity import system_connectivity_status
from core.variables import *

observability_handling_bp = Blueprint("observability_handling", __name__)

@observability_handling_bp.route(cluster_observability_endpoint)
def cluster_observability():
    message = None
    release_name = request.args.get("release_name")
    namespace = request.args.get("namespace")

    all_release_namespaces = {}
    all_release_namespace_services = {}

    if not message:
        message = request.args.get('message')

    all_namespaces = list_all_namespaces()
    all_release_namespaces = list_unique_release_namespaces(all_namespaces)

    if release_name and namespace:
        all_release_namespace_services = list_unique_release_name_namespace_services(all_namespaces, release_name, namespace)

    return render_template("cluster_observability_release_names.html", system_status=system_connectivity_status, all_release_namespace_services=all_release_namespace_services, all_release_namespaces=all_release_namespaces, user=user, message=message)