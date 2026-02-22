gitops_name = "Gitops"
gitops_logs_endpoint = "/logs/connectivity/gitops"
gitops_module_name = "gitops.repository"

cluster_name = "K8S"
cluster_log_endpoint = "/logs/connectivity/k8s"
cluster_module_name = "k8s.cluster"

db_name = "Database"
db_log_endpoint = "/logs/connectivity/database"
db_module_name = "database.postgresql"

state_key = "state"
message_key = "message"
logs_key = "logs"

cluster_service_endpoint = "/cluster/service/"

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