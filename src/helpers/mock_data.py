def list_all_namespaces_mock():
    # Mock data
    all_namespaces = []

    mock_cluster = [
        # nginx namespace
        ("nginx-dev", "nginx", "nginx/nginx-dev", "nginx-api", "14d", "ok", "Service healthy"),
        ("nginx-dev", "nginx", "nginx/nginx-dev", "nginx-web", "14d", "ok", "Service healthy"),
        ("nginx-dev", "nginx", "nginx/nginx-dev", "nginx-worker", "12d", "warning", "LoadBalancer pending"),
        ("nginx-staging", "nginx", "nginx/nginx-staging", "nginx-api", "10d", "ok", "Service healthy"),
        ("nginx-staging", "nginx", "nginx/nginx-staging", "nginx-web", "10d", "error", "No active endpoints"),

        # ingress namespace
        ("ingress-prod", "ingress", "ingress/ingress-prod", "ingress-controller", "20d", "ok", "Service healthy"),
        ("ingress-prod", "ingress", "ingress/ingress-prod", "ingress-api", "18d", "ok", "Service healthy"),
        ("ingress-prod", "ingress", "ingress/ingress-prod", "ingress-webhook", "17d", "neutral", "Service terminating"),
        ("ingress-staging", "ingress", "ingress/ingress-staging", "ingress-dashboard", "15d", "warning", "No endpoints (manual service)"),

        # redis namespace
        ("redis-prod", "redis", "redis/redis-prod", "redis-master", "30d", "ok", "Headless service healthy"),
        ("redis-prod", "redis", "redis/redis-prod", "redis-replica", "28d", "neutral", "Headless service"),
        ("redis-staging", "redis", "redis/redis-staging", "redis-master", "12d", "ok", "Headless service healthy"),

        # payments namespace
        ("payments-prod", "payments", "payments/payments-prod", "payments-api", "12d", "ok", "Service healthy"),
        ("payments-prod", "payments", "payments/payments-prod", "payments-worker", "12d", "ok", "Service healthy"),
        ("auth-prod", "auth", "auth/auth-prod", "auth-api", "1h", "neutral", "Service terminating"),

        # external integration namespace
        ("external-db", "integrations", "integrations/external-db", "db-service", "45d", "neutral", "External service"),
        ("notifications", "integrations", "integrations/notifications", "notifications-api", "10d", "error", "No active endpoints"),

        # nginx-prod namespace. The fat boy
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-api", "14d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-web", "14d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-worker", "12d", "warning", "LoadBalancer pending"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-cache", "13d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-db", "20d", "error", "No active endpoints"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-auth", "10d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-metrics", "15d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-logger", "8d", "warning", "LoadBalancer pending"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-scheduler", "7d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-notifier", "12d", "neutral", "Service terminating"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-gateway", "18d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-proxy", "16d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-dashboard", "14d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-admin", "14d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-search", "10d", "error", "No active endpoints"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-analytics", "12d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-reporter", "15d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-backup", "20d", "neutral", "Service terminating"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-tracer", "8d", "ok", "Service healthy"),
        ("nginx-prod", "nginx", "nginx/nginx-prod", "nginx-cdn", "10d", "ok", "Service healthy"),
    ]

    for release_name, namespace, release_namespace, service_name, age, state, message in mock_cluster:

        all_namespaces.append({
            "release_name": release_name,
            "release_namespace": release_namespace,
            "service_name": service_name,
            "namespace": namespace,
            "age": age,
            "state": state,
            "message": message,
            "url": "/tmp_url"
        })

    return all_namespaces