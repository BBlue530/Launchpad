import subprocess
import os
from datetime import datetime
import tempfile
from helpers.branch_helpers import get_default_branch
from helpers.logs import connectivity_log
from core.variables import name_key, gitops_name, url_key, gitops_logs_endpoint, module_key, gitops_module_name, state_key, default_state, connected_key, default_connected_state, message_key, default_message, logs_key

def check_gitops_connectivity():
    gitops_connectivity = {name_key: gitops_name, url_key: gitops_logs_endpoint, module_key: gitops_module_name, state_key: default_state, connected_key: default_connected_state, message_key: default_message, logs_key: []}
    logs = []
    gitops_connectivity[logs_key] = logs

    connectivity_log(logs, "info", gitops_module_name, "Starting GitOps repository connectivity validation")

    gitops_repository = os.environ.get("gitops_repository")
    gitops_pat = os.environ.get("gitops_pat")

    gitops_user_name = os.environ.get("gitops_user_name")
    gitops_user_email = os.environ.get("gitops_user_email")

    if not gitops_repository or not gitops_pat or not gitops_user_name or not gitops_user_email:
        gitops_connectivity[message_key] = "Gitops configuration missing"
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        connectivity_log(logs, "error", gitops_module_name, "Missing required GitOps environment variables")
        return gitops_connectivity
    
    gitops_repository_with_pat = gitops_repository.replace("https://", f"https://{gitops_pat}@")

    default_branch = get_default_branch(gitops_repository_with_pat)

    # Check that the repo is reachable
    try:
        subprocess.run(["git", "ls-remote", gitops_repository_with_pat], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        gitops_connectivity[message_key] = "Repository is reachable"
        gitops_connectivity[state_key] = "ok"
        gitops_connectivity[connected_key] = True
        connectivity_log(logs, "info", gitops_module_name, f"Repository reachable: {gitops_repository}")

    except subprocess.CalledProcessError as e:
        gitops_connectivity[message_key] = "Repository is not reachable"
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        connectivity_log(logs, "error", gitops_module_name, f"Repository not reachable: {gitops_repository}")
        return gitops_connectivity
    
    except subprocess.TimeoutExpired:
        gitops_connectivity[message_key] = "Repository check timed out"
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        connectivity_log(logs, "error", gitops_module_name, "Repository connectivity check timed out")
        return gitops_connectivity

    # Check that the repo has the needed branch
    try:
        result = subprocess.run(["git", "ls-remote", "--heads", gitops_repository_with_pat, default_branch], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

        if result.stdout:
            gitops_connectivity[message_key] = f"Repository reachable and branch '{default_branch}' exists"
            gitops_connectivity[state_key] = "ok"
            gitops_connectivity[connected_key] = True
            connectivity_log(logs, "info", gitops_module_name, f"Branch '{default_branch}' exists")

            # Check that the PAT has the needed permissions
            try:
                with tempfile.TemporaryDirectory() as tmp_repo_dir:

                    subprocess.run(["git", "clone", "--depth", "1", "--branch", default_branch, gitops_repository_with_pat, tmp_repo_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)

                    subprocess.run(["git", "config", "--local", "user.name", gitops_user_name], cwd=tmp_repo_dir, check=True)
                    subprocess.run(["git", "config", "--local", "user.email", gitops_user_email], cwd=tmp_repo_dir, check=True)
                    subprocess.run(["git", "config", "--local", "commit.gpgsign", "false"], cwd=tmp_repo_dir, check=True)

                    subprocess.run(["git", "commit", "--allow-empty", "-m", "permission-check"], cwd=tmp_repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    subprocess.run(["git", "push", "--dry-run", "origin", default_branch], cwd=tmp_repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

                    connectivity_log(logs, "info", gitops_module_name, "Repository write permissions validated (dry-run push)")

            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode().lower()

                if "403" in stderr or "permission" in stderr:
                    permissions_message = "PAT lacks permission"
                    gitops_connectivity[state_key] = "error"
                    gitops_connectivity[connected_key] = False
                else:
                    permissions_message = "Permission check failed"
                    gitops_connectivity[state_key] = "warning"
                    gitops_connectivity[connected_key] = False

                gitops_connectivity[message_key] = permissions_message
                connectivity_log(logs, "error", gitops_module_name, f"Permission validation failed: {stderr.strip()}")
                return gitops_connectivity

            except subprocess.TimeoutExpired:
                gitops_connectivity[message_key] = "Permission check timed out"
                gitops_connectivity[state_key] = "error"
                gitops_connectivity[connected_key] = False
                connectivity_log(logs, "error", gitops_module_name, "Repository permission validation timed out")
                return gitops_connectivity

        else:
            gitops_connectivity[message_key] = f"Repository reachable but branch '{default_branch}' missing"
            gitops_connectivity[state_key] = "warning"
            gitops_connectivity[connected_key] = False
            connectivity_log(logs, "warn", gitops_module_name, f"Branch '{default_branch}' missing from repository")

    except subprocess.CalledProcessError as e:
        gitops_connectivity[message_key] = "Repository reachable but branch check failed"
        gitops_connectivity[state_key] = "warning"
        gitops_connectivity[connected_key] = False

        stderr = e.stderr.decode().strip()
        connectivity_log(logs, "warn", gitops_module_name, f"Branch validation failed: {stderr}")
        return gitops_connectivity

    except subprocess.TimeoutExpired:
        gitops_connectivity[message_key] = "Repository check timed out"
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        connectivity_log(logs, "error", gitops_module_name, "Repository connectivity check timed out")
        return gitops_connectivity

    return gitops_connectivity