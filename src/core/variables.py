# Temp vars and will be replaced later on with real generated data
system_status = [
    {"name": "API", "url": "/test_1", "module": "api.internal", "state": "ok", "message": "API OK"},
    {"name": "Auth", "url": "/test_2", "module": "auth.internal", "state": "error", "message": "Auth Error"},
    {"name": "Cache", "url": "/test_3", "module": "redis.internal", "state": "neutral", "message": "Cache Processing"},
]

#system_status = [
#    {"name": "Gitops", "url": "/logs/connectivity/gitops", "module": "gitops.repository", "state": state, "message": message, "logs": logs},
#    {"name": "K8S", "url": "/logs/connectivity/k8s", "module": "k8s.cluster", "state": "error", "state": state, "message": message, "logs": logs},
#    {"name": "Database", "url": "/logs/connectivity/database", "module": "database.postgresql", "state": state, "message": message, "logs": logs},
#]

user = {
    "username": "jdoe",
    "userpic": None
}

app_config_path = "app-config.yaml"

gitops_helm_chart_deployment = "charts"

gitops_backup_helm_chart_deployment = "backup_charts"