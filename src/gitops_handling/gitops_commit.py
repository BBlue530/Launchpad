import os
import tempfile
import subprocess
from datetime import datetime
import yaml
import shutil
from core.variables import *

def commit_helm_chart(helm_chart_url, helm_chart_version, helm_chart_values, cluster_namespace, cluster_release_name):
    gitops_repository = os.environ.get("gitops_repository")
    gitops_pat = os.environ.get("gitops_pat")
    gitops_branch_name = os.environ.get("gitops_branch_name")

    gitops_gpg_priv_key = os.environ.get("gitops_gpg_priv_key")
    gitops_gpg_priv_key_id = os.environ.get("gitops_gpg_priv_key_id")

    gitops_user_name = os.environ.get("gitops_user_name")
    gitops_user_email = os.environ.get("gitops_user_email")

    gitops_repository_with_pat = gitops_repository.replace("https://", f"https://{gitops_pat}@")
    
    with tempfile.TemporaryDirectory() as tmp_repo_dir, tempfile.TemporaryDirectory() as tmp_gpg_dir:
        subprocess.run(["git", "clone", "--branch", gitops_branch_name, gitops_repository_with_pat, tmp_repo_dir], check=True)
        
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        
        helm_chart_metadata = {
            "helm_chart_url": helm_chart_url,
            "helm_chart_version": helm_chart_version,
            "timestamp": timestamp
        }
        
        helm_chart_values_path = os.path.join(tmp_repo_dir, cluster_release_name, gitops_helm_chart_deployment, cluster_namespace, "values.yaml")
        helm_chart_metadata_path = os.path.join(tmp_repo_dir, cluster_release_name, gitops_helm_chart_deployment, cluster_namespace, "metadata.yaml")

        os.makedirs(os.path.dirname(helm_chart_metadata_path), exist_ok=True)
        with open(helm_chart_metadata_path, "w") as f:
            yaml.dump(helm_chart_metadata, f)
        
        os.makedirs(os.path.dirname(helm_chart_values_path), exist_ok=True)
        with open(helm_chart_values_path, "w") as f:
            yaml.dump(helm_chart_values, f)

        chart_name = helm_chart_url.rstrip("/").split("/")[-1]

        backup_helm_chart_values_path = os.path.join(tmp_repo_dir, cluster_release_name, gitops_backup_helm_chart_deployment, cluster_namespace, "values.yaml")
        backup_helm_chart_dir = os.path.join(tmp_repo_dir, cluster_release_name, gitops_backup_helm_chart_deployment, cluster_namespace)

        pull_helm_chart(helm_chart_url, helm_chart_version, chart_name, backup_helm_chart_dir, cluster_namespace, cluster_release_name)

        os.makedirs(os.path.dirname(backup_helm_chart_values_path), exist_ok=True)
        with open(backup_helm_chart_values_path, "w") as f:
            yaml.dump(helm_chart_values, f)

        if gitops_gpg_priv_key and gitops_gpg_priv_key_id:
            gpg_key_path = os.path.join(tmp_gpg_dir, "gpg.priv")

            gitops_gpg_priv_key = gitops_gpg_priv_key.replace('\\n', '\n').strip('"').strip("'")

            with open(gpg_key_path, "w") as f:
                f.write(gitops_gpg_priv_key)

            subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--import", gpg_key_path], check=True)
            subprocess.run(["git", "config", "--local", "user.signingkey", gitops_gpg_priv_key_id], cwd=tmp_repo_dir, check=True)
            subprocess.run(["git", "config", "--local", "commit.gpgsign", "true"], cwd=tmp_repo_dir, check=True)
            subprocess.run(["git", "config", "--local", "gpg.program", "gpg"], cwd=tmp_repo_dir, check=True)

        subprocess.run(["git", "config", "--local", "user.name", gitops_user_name], cwd=tmp_repo_dir, check=True)
        subprocess.run(["git", "config", "--local", "user.email", gitops_user_email], cwd=tmp_repo_dir, check=True)

        subprocess.run(["git", "add", "."], cwd=tmp_repo_dir, check=True)
        commit_cmd = ["git", "commit", "-m", f"bot: Update {cluster_release_name} Helm chart and values"]

        if gitops_gpg_priv_key and gitops_gpg_priv_key_id:
            commit_cmd.insert(2, "-S")

        subprocess.run(commit_cmd, cwd=tmp_repo_dir, check=True)
        
        subprocess.run(["git", "push", "origin", gitops_branch_name], cwd=tmp_repo_dir, check=True)


def pull_helm_chart(helm_chart_url, helm_chart_version, chart_name, helm_chart_dir, cluster_namespace, cluster_release_name):
    os.makedirs(helm_chart_dir, exist_ok=True)
    helm_repo = f"{cluster_release_name}_{cluster_namespace}"

    subprocess.run(["helm", "repo", "add", helm_repo, helm_chart_url], check=True)
    subprocess.run(["helm", "repo", "update"], check=True)

    chart_path = os.path.join(helm_chart_dir, chart_name)
    if os.path.exists(chart_path):
        shutil.rmtree(chart_path)

    pull_helm_chart_cmd = ["helm", "pull", f"{helm_repo}/{chart_name}", "--untar", f"--untardir={helm_chart_dir}"]
    if helm_chart_version:
        pull_helm_chart_cmd.extend(["--version", helm_chart_version])

    subprocess.run(pull_helm_chart_cmd, check=True)
    subprocess.run(["helm", "repo", "remove", helm_repo], check=True)