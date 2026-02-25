import os
import tempfile
import base64
import yaml
from helpers.time_format import format_timestamp, age_to_minutes
from helpers.kubectl import run_kubectl
from helpers.state_check import check_state
from core.variables import cluster_observability_endpoint

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
            release_namespace = f"{namespace}/{release_name}"
            
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
                "release_namespace": release_namespace,
                "service_name": key,
                "namespace": namespace,
                "age": age,
                "state": state,
                "message": message,
                "url": "/tmp_url"
            })

        return all_namespaces
    
def list_unique_release_namespaces(all_namespaces):
    unique_release_namespaces = {}

    for entry in all_namespaces:
        if entry["release_namespace"] not in unique_release_namespaces:
            unique_release_namespaces[entry["release_namespace"]] = {
                "release_namespace": entry.get("release_namespace"),
                "namespace": entry.get("namespace"),
                "age": entry.get("age"),
                "state": entry.get("state"),
                "url": f"{cluster_observability_endpoint}?release_name={entry.get('release_name')}&namespace={entry.get('namespace')}"
            }

        stored_age = age_to_minutes(unique_release_namespaces[entry["release_namespace"]]["age"])
        entry_age = age_to_minutes(entry.get("age"))

        if entry_age > stored_age:
            unique_release_namespaces[entry["release_namespace"]]["age"] = entry.get("age")
        
        state_message, stored_state = check_state(unique_release_namespaces[entry["release_namespace"]]["state"], entry.get("state"))

        unique_release_namespaces[entry["release_namespace"]]["state"] = stored_state
        unique_release_namespaces[entry["release_namespace"]]["message"] = state_message

    return list(unique_release_namespaces.values())

def list_unique_release_name_namespace_services(all_namespaces, release_name, namespace):
    release_name_namespace_services = {}

    for entry in all_namespaces:
        if entry["release_name"] == release_name and entry["namespace"] == namespace:
            if entry["service_name"] not in release_name_namespace_services:
                release_name_namespace_services[entry["service_name"]] = {
                    "service_name": entry.get("service_name"),
                    "age": entry.get("age"),
                    "state": entry.get("state"),
                    "message": entry.get("message"),
                    "url": entry.get("url")
                }

    return list(release_name_namespace_services.values())