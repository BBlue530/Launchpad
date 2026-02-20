import os
import subprocess
import tempfile
import base64
import yaml
import json

def deploy_service(helm_chart_url, helm_chart_name, helm_chart_version, helm_chart_values, cluster_namespace, cluster_release_name):
    result_json = {}

    cluster_api_server = os.environ.get("cluster_api_server")
    cluster_token = os.environ.get("cluster_token")
    cluster_ca_cert = os.environ.get("cluster_ca_cert")

    ca_cert_bytes = base64.b64decode(cluster_ca_cert)

    with tempfile.TemporaryDirectory() as tmpdir:
        ca_path = os.path.join(tmpdir, "ca.crt")
        kubeconfig_path = os.path.join(tmpdir, "kubeconfig.yaml")
        values_path = os.path.join(tmpdir, "values.yaml")

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
                    "namespace": cluster_namespace,
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

        with open(values_path, "w") as f:
            yaml.safe_dump(helm_chart_values, f)

        helm_install_cmd = [
            "helm", "upgrade", "--install",
            cluster_release_name,
        ]

        if helm_chart_url.startswith("oci://"):
            helm_install_cmd.append(helm_chart_url)

        elif ".tgz" in helm_chart_url:
            helm_install_cmd.append(helm_chart_url)

        else:
            helm_install_cmd.extend([
                helm_chart_name,
                "--repo", helm_chart_url
            ])

        helm_install_cmd.extend([
            "--namespace", cluster_namespace,
            "--create-namespace",
            "--timeout", "10m",
            "-f", values_path,
            "--kubeconfig", kubeconfig_path,
        ])

        if helm_chart_version:
            helm_install_cmd.extend(["--version", helm_chart_version])

        before = get_latest_deployment(cluster_release_name, cluster_namespace, kubeconfig_path)

        try:
            result = subprocess.run(helm_install_cmd, check=True, capture_output=True, text=True)

            result_json["success"] = (result.returncode == 0)
            result_json["stdout"] = result.stdout

        except subprocess.CalledProcessError as e:
            result_json["success"] = False
            result_json["stdout"] = e.stdout
            result_json["stderr"] = e.stderr
            result_json["returncode"] = e.returncode
        
        after = get_latest_deployment(cluster_release_name, cluster_namespace, kubeconfig_path)

        result_json["commit_changes"] = after["revision"] > before["revision"]

        return result_json
    
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