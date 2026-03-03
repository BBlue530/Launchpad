from flask import flash
import os
import tempfile
import subprocess
from datetime import datetime
import yaml
import shutil
import json
from core.variables import *

def commit_helm_chart(helm_chart_url, helm_chart_name, helm_chart_version, helm_chart_values, cluster_namespace, cluster_release_name, deploy_backup_helm_chart, force_deploy_helm_chart):
    gitops_repository = os.environ.get("gitops_repository")
    gitops_pat = os.environ.get("gitops_pat")
    gitops_branch_name = os.environ.get("gitops_branch_name")

    gitops_gpg_priv_key = os.environ.get("gitops_gpg_priv_key")
    gitops_gpg_priv_key_id = os.environ.get("gitops_gpg_priv_key_id")

    gitops_user_name = os.environ.get("gitops_user_name")
    gitops_user_email = os.environ.get("gitops_user_email")

    gitops_repository_with_pat = gitops_repository.replace("https://", f"https://{gitops_pat}@")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    result = subprocess.run(["git", "ls-remote", "--heads", gitops_repository_with_pat, gitops_branch_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

    if not result.stdout:
        with tempfile.TemporaryDirectory() as tmp_create_branch:

            subprocess.run(["git", "clone", "--depth", "1", gitops_repository_with_pat, tmp_create_branch],check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)

            gpg_sign_config(gitops_gpg_priv_key_id, gitops_gpg_priv_key, tmp_create_branch)

            subprocess.run(["git", "config", "--local", "user.name", gitops_user_name], cwd=tmp_create_branch, check=True)
            subprocess.run(["git", "config", "--local", "user.email", gitops_user_email], cwd=tmp_create_branch, check=True)

            subprocess.run(["git", "checkout", "-b", gitops_branch_name], cwd=tmp_create_branch, check=True)

            subprocess.run(["git", "commit", "--allow-empty", "-m", "bot: Initial branch creation"], cwd=tmp_create_branch, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            subprocess.run(["git", "push", "-u", "origin", gitops_branch_name], cwd=tmp_create_branch, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
    
    with tempfile.TemporaryDirectory() as tmp_repo_dir, tempfile.TemporaryDirectory() as tmp_gpg_dir:

        subprocess.run(["git", "clone", "--branch", gitops_branch_name, gitops_repository_with_pat, tmp_repo_dir], check=True)

        release_namespace = f"{cluster_namespace}/{cluster_release_name}"
        
        backup_helm_chart_dir = os.path.join(tmp_repo_dir, gitops_backup_helm_chart_deployment, f"{helm_chart_name}_{helm_chart_version}")

        helm_chart_values_path = os.path.join(tmp_repo_dir, gitops_helm_chart_deployment, cluster_release_name, release_namespace, "values.yaml")
        helm_chart_metadata_path = os.path.join(tmp_repo_dir, gitops_helm_chart_deployment, cluster_release_name, release_namespace, "metadata.yaml")

        if not deploy_backup_helm_chart:
            pulled_helm_chart_version = pull_helm_chart(helm_chart_url, helm_chart_version, helm_chart_name, backup_helm_chart_dir, cluster_namespace, cluster_release_name)
            if not pulled_helm_chart_version:
                return
        else:
            pulled_helm_chart_version = helm_chart_version
            
        helm_chart_metadata = {
            "helm_chart_url": helm_chart_url,
            "helm_chart_name": helm_chart_name,
            "helm_chart_version": pulled_helm_chart_version,
            "timestamp": timestamp,
            "backup_helm_chart_deployed": False,
            "force_deploy_helm_chart": False
        }

        if deploy_backup_helm_chart:
            helm_chart_metadata["backup_helm_chart_deployed"] = True

        if force_deploy_helm_chart:
            helm_chart_metadata["backup_helforce_deploy_helm_chartm_chart_deployed"] = True

        os.makedirs(os.path.dirname(helm_chart_metadata_path), exist_ok=True)
        with open(helm_chart_metadata_path, "w") as f:
            yaml.dump(helm_chart_metadata, f)
        
        os.makedirs(os.path.dirname(helm_chart_values_path), exist_ok=True)
        with open(helm_chart_values_path, "w") as f:
            yaml.dump(helm_chart_values, f)
            
        gpg_sign_config(gitops_gpg_priv_key_id, gitops_gpg_priv_key, tmp_repo_dir, tmp_gpg_dir)

        subprocess.run(["git", "config", "--local", "user.name", gitops_user_name], cwd=tmp_repo_dir, check=True)
        subprocess.run(["git", "config", "--local", "user.email", gitops_user_email], cwd=tmp_repo_dir, check=True)

        subprocess.run(["git", "add", "."], cwd=tmp_repo_dir, check=True)
        commit_cmd = ["git", "commit", "-m", f"bot({release_namespace}): Update Helm chart and values [{timestamp}]."]

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
        pulled_helm_chart_version = helm_chart_version

    else:
        search_helm_chart_version_cmd = [
            "helm",
            "search",
            "repo", f"{helm_repo}/{chart_name}",
            "--versions",
            "-o", "json",
        ]

        search_result = subprocess.run(search_helm_chart_version_cmd, capture_output=True, text=True, check=True)
        charts = json.loads(search_result.stdout)

        if not charts:
            flash(
                f"Deployment failed for [{cluster_namespace}]: Chart version not found in pulled repository.",
                "message-status-false"
            )
            return False

        pulled_helm_chart_version = charts[0]["version"]
        pull_helm_chart_cmd.extend(["--version", pulled_helm_chart_version])

    subprocess.run(pull_helm_chart_cmd, check=True)
    subprocess.run(["helm", "repo", "remove", helm_repo], check=True)

    return pulled_helm_chart_version

def gpg_sign_config(gitops_gpg_priv_key_id, gitops_gpg_priv_key, tmp_repo_dir, tmp_gpg_dir):
    if gitops_gpg_priv_key and gitops_gpg_priv_key_id:
        gpg_key_path = os.path.join(tmp_gpg_dir, "gpg.priv")

        gitops_gpg_priv_key = gitops_gpg_priv_key.replace('\\n', '\n').strip('"').strip("'")

        with open(gpg_key_path, "w") as f:
            f.write(gitops_gpg_priv_key)

        subprocess.run(["gpg", "--batch", "--pinentry-mode", "loopback", "--import", gpg_key_path], check=True)
        subprocess.run(["git", "config", "--local", "user.signingkey", gitops_gpg_priv_key_id], cwd=tmp_repo_dir, check=True)
        subprocess.run(["git", "config", "--local", "commit.gpgsign", "true"], cwd=tmp_repo_dir, check=True)
        subprocess.run(["git", "config", "--local", "gpg.program", "gpg"], cwd=tmp_repo_dir, check=True)
    else:
        subprocess.run(["git", "config", "--local", "commit.gpgsign", "false"], cwd=tmp_repo_dir, check=True)