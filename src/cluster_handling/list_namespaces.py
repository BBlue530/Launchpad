import os
import tempfile
import base64
import yaml
from helpers.time_format import format_timestamp, age_to_minutes
from helpers.kubectl import run_kubectl
from core.variables import cluster_service_endpoint, cluster_error_message, cluster_warning_message, cluster_neutral_message, cluster_ok_message

def list_all_namespaces():
    cluster_api_server = os.environ.get("cluster_api_server")
    cluster_token = os.environ.get("cluster_token")
    cluster_ca_cert = os.environ.get("cluster_ca_cert")

    ca_cert_bytes = base64.b64decode(cluster_ca_cert)

    with tempfile.TemporaryDirectory() as tmpdir:
        ca_path = os.path.join(tmpdir, "ca.crt")
        kubeconfig_path = os.path.join(tmpdir, "kubeconfig.yaml")

        with open(ca_path, "wb") as f:
            f.write(ca_cert_bytes)

        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": "cluster",
                "cluster": {
                    "server": cluster_api_server,
                    "certificate-authority": ca_path,
                },
            }],
            "contexts": [
                {
                    "name": "context",
                    "context": {
                        "cluster": "cluster",
                        "user": "user",
                    },
                }
            ],
            "current-context": "context",
            "users": [{
                "name": "user",
                "user": {
                    "token": cluster_token,
                },
            }],
        }

        with open(kubeconfig_path, "w") as f:
            yaml.safe_dump(kubeconfig, f)
            
        services = run_kubectl(kubeconfig_path, ["get", "svc", "-A", "-o", "json"])
        endpoint_slices = run_kubectl(kubeconfig_path, ["get", "endpointslices", "-A", "-o", "json"])

        endpoint_map = {}

        for ep in (endpoint_slices.get("items") or []):

            namespace = ep["metadata"]["namespace"]

            service_name = (
                ep.get("metadata", {})
                .get("labels", {})
                .get("kubernetes.io/service-name")
            )

            if not service_name:
                continue

            key = f"{namespace}/{service_name}"

            for endpoint in (ep.get("endpoints") or []):

                if endpoint.get("conditions", {}).get("ready", True):

                    endpoint_map[key] = True
                    break

        all_namespaces = []

        for svc in services["items"]:

            metadata = svc.get("metadata", {})
            labels = metadata.get("labels", {})

            namespace = metadata.get("namespace")
            name = metadata.get("name")
            release_name = labels.get("app.kubernetes.io/instance")

            key = f"{namespace}/{name}"

            age = format_timestamp(svc["metadata"]["creationTimestamp"])

            spec = svc.get("spec", {})
            status = svc.get("status", {})

            svc_type = spec.get("type", "ClusterIP")
            cluster_ip = spec.get("clusterIP")
            selector = spec.get("selector")

            has_endpoints = endpoint_map.get(key, False)

            state = "ok"
            message = "Service healthy"

            if svc["metadata"].get("deletionTimestamp"):
                state = "neutral"
                message = "Service terminating"

            elif svc_type == "ExternalName":
                state = "neutral"
                message = "External service"

            elif svc_type == "LoadBalancer":

                ingress = (
                    status.get("loadBalancer", {})
                    .get("ingress")
                )

                if not ingress:
                    state = "warning"
                    message = "LoadBalancer pending"

                elif not has_endpoints:
                    state = "error"
                    message = "No backend endpoints"

            elif cluster_ip == "None":

                if has_endpoints:
                    state = "ok"
                    message = "Headless service healthy"
                else:
                    state = "neutral"
                    message = "Headless service"

            elif selector is None:

                if has_endpoints:
                    state = "ok"
                    message = "Manual service healthy"
                else:
                    state = "warning"
                    message = "No endpoints (manual service)"

            else:

                if has_endpoints:
                    state = "ok"
                    message = "Service healthy"
                else:
                    state = "error"
                    message = "No active endpoints"

            all_namespaces.append({
                "release_name": release_name,
                "name": key,
                "namespace": namespace,
                "age": age,
                "state": state,
                "message": message,
                "url": "/tmp_url"
            })

        return all_namespaces
    
def list_unique_namespaces(all_namespaces):
    unique_namespaces = {}

    for entry in all_namespaces:
        if entry["namespace"] not in unique_namespaces:
            unique_namespaces[entry["namespace"]] = {
                "release_name": entry.get("release_name"),
                "namespace": entry.get("namespace"),
                "age": entry.get("age"),
                "state": entry.get("state"),
                "url": f"{cluster_service_endpoint}{entry.get('release_name')}/{entry.get('namespace')}"
            }

        stored_age = age_to_minutes(unique_namespaces[entry["namespace"]]["age"])
        entry_age = age_to_minutes(entry.get("age"))

        if entry_age > stored_age:
            unique_namespaces[entry["namespace"]]["age"] = entry.get("age")
        
        if entry.get("state") == "error" or unique_namespaces[entry["namespace"]]["state"] == "error":
            unique_namespaces[entry["namespace"]]["state"] = "error"
            unique_namespaces[entry["namespace"]]["message"] = cluster_error_message

        elif entry.get("state") == "warning" or unique_namespaces[entry["namespace"]]["state"]  == "warning":
            unique_namespaces[entry["namespace"]]["state"] = "warning"
            unique_namespaces[entry["namespace"]]["message"] = cluster_warning_message

        elif entry.get("state") == "neutral" or unique_namespaces[entry["namespace"]]["state"]  == "neutral":
            unique_namespaces[entry["namespace"]]["state"] = "neutral"
            unique_namespaces[entry["namespace"]]["message"] = cluster_neutral_message

        elif entry.get("state") == "ok" or unique_namespaces[entry["namespace"]]["state"]  == "ok":
            unique_namespaces[entry["namespace"]]["state"] = "ok"
            unique_namespaces[entry["namespace"]]["message"] = cluster_ok_message

    return list(unique_namespaces.values())
    
def list_all_namespaces_test():
    # Mock data
    all_namespaces = []

    mock_cluster = [
        ("ci-test", "default", "default/frontend", "5d", "ok", "Service healthy"),
        ("ci-test", "default", "default/backend", "5d", "error", "No active endpoints"),
        ("ci-prod", "kube-system", "kube-system/coredns", "30d", "ok", "Service healthy"),
        ("ci-prod", "monitoring", "monitoring/prometheus", "12d", "warning", "LoadBalancer pending"),
        ("ci-dev", "dev", "dev/api", "2d", "neutral", "External service"),
        ("ci-dev", "dev", "dev/headless-db", "1d", "ok", "Headless service healthy"),
        ("ci-dev", "dev", "dev/manual-service", "3d", "warning", "No endpoints (manual service)"),
    ]

    for release_name, namespace, key, age, state, message in mock_cluster:

        all_namespaces.append({
            "release_name": release_name,
            "name": key,
            "namespace": namespace,
            "age": age,
            "state": state,
            "message": message,
            "url": "/tmp_url"
        })

    return all_namespaces