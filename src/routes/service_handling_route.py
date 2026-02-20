from flask import render_template, request, Blueprint, redirect, url_for, flash
import yaml
from cluster_handling.deploy_service import deploy_service
from gitops_handling.gitops_commit import commit_helm_chart
from cluster_handling.list_namespaces import list_all_namespaces
from service_status.external_connectivity import system_connectivity_status
from core.variables import *

service_handling_bp = Blueprint("service_handling", __name__)

@service_handling_bp.route('/add_service')
def add_service():
    message = None

    if not message:
        message = request.args.get('message')

    all_namespaces = list_all_namespaces()
    
    return render_template("add_service.html", system_status=system_connectivity_status, all_namespaces=all_namespaces, user=user, message=message)

@service_handling_bp.route("/add_service_form", methods=["POST"])
def add_service_form():
    helm_chart_url = request.form.get("helm_chart_url")
    helm_chart_name = request.form.get("helm_chart_name")
    helm_chart_version = request.form.get("helm_chart_version")
    helm_chart_values = request.form.get("helm_chart_values")

    cluster_namespace = request.form.get("cluster_namespace")
    cluster_release_name = request.form.get("cluster_release_name")

    rollback_on_failure = request.form.get("rollback_on_failure")

    required_inputs = [helm_chart_url, cluster_namespace, cluster_release_name]
    if not all(required_inputs):
        flash(
            "Missing required deployment fields",
            "message-status-false"
        )
        return redirect(url_for("service_handling.add_service"))

    try:
        helm_chart_values = yaml.safe_load(helm_chart_values) or {}
    except yaml.YAMLError as e:
        flash(
            f"Invalid Helm values YAML: {e}",
            "message-status-false"
        )
        return redirect(url_for("service_handling.add_service"))

    result_json = deploy_service(helm_chart_url, helm_chart_name, helm_chart_version, helm_chart_values, cluster_namespace, cluster_release_name, rollback_on_failure)

    if not result_json or not result_json.get("success"):
        error_msg = (result_json.get("stderr") or result_json.get("stdout") or "unknown error")

        flash(
            f"Deployment failed for [{cluster_namespace}]: {error_msg}",
            "message-status-false",
        )
    else:
        flash(
            f"Deployment of [{cluster_namespace}] succeeded",
            "message-status-true",
        )
    
    if result_json.get("commit_changes"):
        commit_helm_chart(helm_chart_url, helm_chart_name, helm_chart_version, helm_chart_values, cluster_namespace, cluster_release_name)

    return redirect(url_for("service_handling.add_service"))