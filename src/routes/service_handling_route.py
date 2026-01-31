from flask import render_template, request, Blueprint, redirect, url_for, flash
from core.variables import *

service_handling_bp = Blueprint("service_handling", __name__)

@service_handling_bp.route('/add_service')
def add_service():
    message = None

    if not message:
        message = request.args.get('message')
    return render_template("add_service.html", system_status=system_status, user=user, message=message)

@service_handling_bp.route("/add_service_form", methods=["POST"])
def add_service_form():
    helm_chart_url = request.form.get("helm_chart_url")
    helm_chart_values = request.form.get("helm_chart_values")

    if helm_chart_url == "fail":
        flash(
            "Failure of input stuff and things happen",
            "message-status-false"
        )
    else:
        flash(
            "Success of input stuff and things happen",
            "message-status-true"
        )
    
    print("Helm Chart Url:")
    print(helm_chart_url)
    print("Helm Chart Values:")
    print(helm_chart_values)

    return redirect(url_for("service_handling.add_service"))