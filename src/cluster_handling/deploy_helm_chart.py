import subprocess
from cluster_handling.cluster_helpers import get_latest_deployment

def helm_chart_deploy(helm_chart_url, helm_chart_name, helm_chart_version, cluster_namespace, cluster_release_name, values_path, kubeconfig_path):
    result_json = {}

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
        "--kubeconfig", kubeconfig_path,
    ])
    
    if values_path:
        helm_install_cmd.extend(["-f", values_path])

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