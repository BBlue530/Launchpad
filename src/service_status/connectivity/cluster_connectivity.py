import os
import subprocess
import tempfile
import base64
import yaml
from helpers.logs import connectivity_log
from core.variables import name_key, cluster_name, url_key, cluster_log_endpoint, module_key, cluster_module_name, state_key, default_state, connected_key, default_connected_state, message_key, default_message, logs_key

def check_cluster_connectivity():
    cluster_connectivity = {name_key: cluster_name, url_key: cluster_log_endpoint, module_key: cluster_module_name, state_key: default_state, connected_key: default_connected_state, message_key: default_message, logs_key: []}
    logs = []
    cluster_connectivity[logs_key] = logs

    connectivity_log(logs, "info", cluster_module_name, "Starting Kubernetes connectivity validation")

    cluster_api_server = os.environ.get("cluster_api_server")
    cluster_token = os.environ.get("cluster_token")
    cluster_ca_cert = os.environ.get("cluster_ca_cert")

    if not cluster_api_server or not cluster_token or not cluster_ca_cert:
        cluster_connectivity[message_key] = "Missing cluster environment variables"
        cluster_connectivity[state_key] = "error"
        cluster_connectivity[connected_key] = False
        connectivity_log(logs, "error", cluster_module_name, "Missing required cluster environment variables")
        return cluster_connectivity

    try:
        ca_cert_bytes = base64.b64decode(cluster_ca_cert)

    except Exception:
        cluster_connectivity[message_key] = "Invalid CA certificate encoding"
        cluster_connectivity[state_key] = "error"
        cluster_connectivity[connected_key] = False
        connectivity_log(logs, "error", cluster_module_name, "Failed to decode CA certificate (base64)")
        return cluster_connectivity

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
            "contexts": [{
                "name": "context",
                "context": {
                    "cluster": "cluster",
                    "user": "user",
                },
            }],
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

        try:
            subprocess.run(["kubectl", "get", "--raw", "/version", "--kubeconfig", kubeconfig_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            connectivity_log(logs, "info", cluster_module_name, "Kubernetes API server reachable")

        except subprocess.CalledProcessError as e:
            cluster_connectivity[message_key] = "Cluster unreachable or authentication failed"
            cluster_connectivity[state_key] = "error"
            cluster_connectivity[connected_key] = False

            stderr = e.stderr.decode().strip()
            connectivity_log(logs, "error", cluster_module_name, f"Kubectl API probe failed: {stderr}")
            return cluster_connectivity
        
        except subprocess.TimeoutExpired:
            cluster_connectivity[message_key] = "Cluster connection timed out"
            cluster_connectivity[state_key] = "error"
            cluster_connectivity[connected_key] = False
            connectivity_log(logs, "error", cluster_module_name, "Cluster API probe timed out")
            return cluster_connectivity

        try:
            subprocess.run(["kubectl", "auth", "can-i", "create", "deployments", "--all-namespaces", "--kubeconfig", kubeconfig_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            connectivity_log(logs, "info", cluster_module_name, "RBAC permission validated (create deployments)")

        except subprocess.CalledProcessError as e:
            cluster_connectivity[message_key] = "Cluster reachable but insufficient permissions"
            cluster_connectivity[state_key] = "warning"
            cluster_connectivity[connected_key] = False

            stderr = e.stderr.decode().strip()
            connectivity_log(logs, "warn", cluster_module_name, f"RBAC validation failed: {stderr or 'permission denied'}")
            return cluster_connectivity

        try:
            subprocess.run(["kubectl", "get", "namespaces", "--kubeconfig", kubeconfig_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            connectivity_log(logs, "info", cluster_module_name, "Namespace listing successful")

        except subprocess.CalledProcessError as e:
            cluster_connectivity[message_key] = "Authenticated but cannot list namespaces"
            cluster_connectivity[state_key] = "warning"
            cluster_connectivity[connected_key] = False
            
            stderr = e.stderr.decode().strip()
            connectivity_log(logs, "warn", cluster_module_name, f"Namespace listing failed: {stderr or 'unknown kubectl error'}")
            return cluster_connectivity

    cluster_connectivity[message_key] = "Cluster reachable and permissions validated"
    cluster_connectivity[state_key] = "ok"
    cluster_connectivity[connected_key] = True
    connectivity_log(logs, "info", cluster_module_name, "Cluster connectivity validation completed successfully")

    return cluster_connectivity