import os
import subprocess
import tempfile
import base64
from datetime import datetime
import yaml
from core.variables import cluster_name, cluster_log_endpoint, cluster_module_name, state_key, message_key, logs_key

def check_cluster_connectivity():
    cluster_connectivity = {"name": cluster_name, "url": cluster_log_endpoint, "module": cluster_module_name, state_key: "neutral", message_key: "Not checked", logs_key: []}
    logs = []
    cluster_connectivity[logs_key] = logs

    cluster_api_server = os.environ.get("cluster_api_server")
    cluster_token = os.environ.get("cluster_token")
    cluster_ca_cert = os.environ.get("cluster_ca_cert")

    ca_cert_bytes = base64.b64decode(cluster_ca_cert)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")


    if not cluster_api_server or not cluster_token or not cluster_ca_cert:
        cluster_connectivity["state"] = "error"
        cluster_connectivity["message"] = "Missing cluster environment variables"
        logs.append(f"missing env vars at [{timestamp}]")
        return cluster_connectivity

    try:
        ca_cert_bytes = base64.b64decode(cluster_ca_cert)
    except Exception:
        cluster_connectivity["state"] = "error"
        cluster_connectivity["message"] = "Invalid CA certificate encoding"
        logs.append("CA base64 decode failed")
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
            logs.append(f"API reachable at [{timestamp}]")
        except subprocess.CalledProcessError as e:
            cluster_connectivity["state"] = "error"
            cluster_connectivity["message"] = "Cluster unreachable or authentication failed"
            logs.append(e.stderr.decode())
            return cluster_connectivity
        except subprocess.TimeoutExpired:
            cluster_connectivity["state"] = "error"
            cluster_connectivity["message"] = "Cluster connection timed out"
            logs.append("cluster connection timed out")
            return cluster_connectivity

        try:
            subprocess.run(["kubectl", "auth", "can-i", "create", "deployments", "--all-namespaces", "--kubeconfig", kubeconfig_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            logs.append("Permissions validated")
        except subprocess.CalledProcessError:
            cluster_connectivity["state"] = "warning"
            cluster_connectivity["message"] = "Cluster reachable but insufficient permissions"
            logs.append("permissions check failed")
            return cluster_connectivity

        try:
            subprocess.run(["kubectl", "get", "namespaces", "--kubeconfig", kubeconfig_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
            logs.append("Namespace listing successful")
        except subprocess.CalledProcessError:
            cluster_connectivity["state"] = "warning"
            cluster_connectivity["message"] = "Authenticated but cannot list namespaces"
            logs.append("authenticated but cannot list namespaces")
            return cluster_connectivity

    cluster_connectivity["state"] = "ok"
    cluster_connectivity["message"] = "Cluster reachable and permissions validated"
    logs.append("cluster reachable and permissions validated")

    return cluster_connectivity