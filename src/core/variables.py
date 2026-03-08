cluster_observability_endpoint = "/observability/cluster"
connectivity_observability_endpoint = "/observability/connectivity"

gitops_name = "Gitops"
gitops_logs_endpoint = f"{connectivity_observability_endpoint}?external_connection={gitops_name}"
gitops_module_name = "gitops.repository"

cluster_name = "K8S"
cluster_log_endpoint = f"{connectivity_observability_endpoint}?external_connection={cluster_name}"
cluster_module_name = "k8s.cluster"

db_name = "Database"
db_log_endpoint = "/logs/connectivity/database"
db_module_name = "database.postgresql"

name_key = "name"
url_key = "url"
module_key = "module"
state_key = "state"
message_key = "message"
logs_key = "logs"
connected_key = "connected"

default_state = "neutral"
default_connected_state = False
default_message = "Not checked"

cluster_error_message = "Namespace has one or more failing services."
cluster_warning_message = "Degraded performance or partial failures detected."
cluster_neutral_message = "Status is still initializing."
cluster_ok_message = "All services are operating normally."

# Still placeholder here. Will be real when real login logic gets added
user = {
    "username": "jdoe",
    "userpic": None
}

app_config_path = "app-config.yaml"

gitops_helm_chart_deployment = "charts"

gitops_backup_helm_chart_deployment = "backup_charts"