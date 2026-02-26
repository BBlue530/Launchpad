import os
import subprocess
import tempfile
from cluster_handling.cluster_helpers import get_latest_deployment
from core.variables import gitops_backup_helm_chart_deployment

def helm_chart_deploy_backup(helm_chart_name, helm_chart_version, cluster_namespace, cluster_release_name, values_path, kubeconfig_path):
    result_json = {}

    gitops_repository = os.environ.get("gitops_repository")
    gitops_pat = os.environ.get("gitops_pat")
    gitops_branch_name = os.environ.get("gitops_branch_name")

    gitops_repository_with_pat = gitops_repository.replace("https://", f"https://{gitops_pat}@")

    result = subprocess.run(["git", "ls-remote", "--heads", gitops_repository_with_pat, gitops_branch_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

    if result.stdout:
        with tempfile.TemporaryDirectory() as tmp_dir:
            subprocess.run(["git", "clone", "--branch", gitops_branch_name, gitops_repository_with_pat, tmp_dir], check=True)

            backup_helm_chart_dir = os.path.join(tmp_dir, gitops_backup_helm_chart_deployment, f"{helm_chart_name}_{helm_chart_version}", helm_chart_name)

            helm_install_cmd = [
                "helm",
                "upgrade",
                "--install", cluster_release_name, backup_helm_chart_dir,
                "--namespace", cluster_namespace,
                "--create-namespace",
                "--kubeconfig", kubeconfig_path,
            ]

            if values_path:
                helm_install_cmd.extend(["-f", values_path])

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