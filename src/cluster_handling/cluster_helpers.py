import subprocess
import json

def get_latest_deployment(cluster_release_name, cluster_namespace, kubeconfig_path):
    cmd = [
        "helm", "history", cluster_release_name,
        "-n", cluster_namespace,
        "--kubeconfig", kubeconfig_path,
        "-o", "json"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"revision": 0, "chart": None}

    history = json.loads(result.stdout)
    if not history:
        return {"revision": 0, "chart": None}

    latest = history[-1]
    return {
        "revision": int(latest["revision"]),
        "chart": latest["chart"]
    }