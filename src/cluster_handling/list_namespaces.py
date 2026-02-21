import os
import tempfile
import base64
import yaml
from helpers.time_format import format_timestamp
from helpers.kubectl import run_kubectl

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

            namespace = svc["metadata"]["namespace"]
            name = svc["metadata"]["name"]

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
                "name": key,
                "namespace": namespace,
                "age": age,
                "state": state,
                "message": message,
                "url": "/tmp_url"
            })

        return all_namespaces