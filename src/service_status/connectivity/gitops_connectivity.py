import subprocess
import os
from datetime import datetime
import tempfile
from helpers.branch_helpers import get_default_branch
from core.variables import name_key, gitops_name, url_key, gitops_logs_endpoint, module_key, gitops_module_name, state_key, default_state, connected_key, default_connected_state, message_key, default_message, logs_key

def check_gitops_connectivity():
    gitops_connectivity = {name_key: gitops_name, url_key: gitops_logs_endpoint, module_key: gitops_module_name, state_key: default_state, connected_key: default_connected_state, message_key: default_message, logs_key: []}
    logs = []
    gitops_connectivity[logs_key] = logs

    gitops_repository = os.environ.get("gitops_repository")
    gitops_pat = os.environ.get("gitops_pat")

    gitops_user_name = os.environ.get("gitops_user_name")
    gitops_user_email = os.environ.get("gitops_user_email")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if not gitops_repository or not gitops_pat:
        message = "Gitops configuration missing"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        logs.append(f"missing environment variables. timestamp: [{timestamp}]")
        print(f"[!] {message}")
        return gitops_connectivity
    
    gitops_repository_with_pat = gitops_repository.replace("https://", f"https://{gitops_pat}@")

    default_branch = get_default_branch(gitops_repository_with_pat)

    # Check that the repo is reachable
    try:
        subprocess.run(["git", "ls-remote", gitops_repository_with_pat], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        message = "Repository is reachable"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "ok"
        gitops_connectivity[connected_key] = True
        logs.append(f"repository is reachable. timestamp: [{timestamp}]. repository [{gitops_repository}].")
        print(f"[+] {message}")

    except subprocess.CalledProcessError as e:
        message = "Repository is not reachable"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        logs.append(f"repository is not reachable. timestamp: [{timestamp}]. repository [{gitops_repository}].")
        print(f"[!] {message}")
        return gitops_connectivity
    
    except subprocess.TimeoutExpired:
        message = "Repository check timed out"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        logs.append("repository check timed out")
        print(f"[!] {message}")
        return gitops_connectivity

    # Check that the repo has the needed branch
    try:
        result = subprocess.run(["git", "ls-remote", "--heads", gitops_repository_with_pat, default_branch], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

        if result.stdout:
            message = f"Repository reachable and branch '{default_branch}' exists"
            gitops_connectivity[message_key] = message
            gitops_connectivity[state_key] = "ok"
            gitops_connectivity[connected_key] = True
            logs.append(f"branch {default_branch} exists at [{timestamp}]")
            print(f"[+] {message}")

            # Check that the PAT has the needed permissions
            try:
                with tempfile.TemporaryDirectory() as tmp_repo_dir:

                    subprocess.run(["git", "clone", "--depth", "1", "--branch", default_branch, gitops_repository_with_pat, tmp_repo_dir], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)

                    subprocess.run(["git", "config", "--local", "user.name", gitops_user_name], cwd=tmp_repo_dir, check=True)
                    subprocess.run(["git", "config", "--local", "user.email", gitops_user_email], cwd=tmp_repo_dir, check=True)
                    subprocess.run(["git", "config", "--local", "commit.gpgsign", "false"], cwd=tmp_repo_dir, check=True)

                    subprocess.run(["git", "commit", "--allow-empty", "-m", "permission-check"], cwd=tmp_repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    subprocess.run(["git", "push", "--dry-run", "origin", default_branch], cwd=tmp_repo_dir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

                    logs.append(f"permission verified at [{timestamp}]")
                    print(f"[+] {message}")

            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode().lower()

                if "403" in stderr or "permission" in stderr:
                    message = "PAT lacks permission"
                    gitops_connectivity[state_key] = "error"
                    gitops_connectivity[connected_key] = False
                else:
                    message = "Permission check failed"
                    gitops_connectivity[state_key] = "warning"
                    gitops_connectivity[connected_key] = False

                gitops_connectivity[message_key] = message
                logs.append(stderr.strip())
                print(f"[!] {message}")
                return gitops_connectivity

            except subprocess.TimeoutExpired:
                message = "Permission check timed out"
                gitops_connectivity[message_key] = message
                gitops_connectivity[state_key] = "error"
                gitops_connectivity[connected_key] = False
                logs.append("Permission check timed out")
                print(f"[!] {message}")
                return gitops_connectivity

        else:
            message = f"Repository reachable but branch '{default_branch}' missing"
            gitops_connectivity[message_key] = message
            gitops_connectivity[state_key] = "warning"
            gitops_connectivity[connected_key] = False
            logs.append(f"branch {default_branch} missing at [{timestamp}]")
            print(f"[!] {message}")

    except subprocess.CalledProcessError as e:
        message = "Repository reachable but branch check failed"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "warning"
        gitops_connectivity[connected_key] = False
        logs.append(e.stderr.decode().strip())
        print(f"[!] {message}")
        return gitops_connectivity

    except subprocess.TimeoutExpired:
        message = "Repository check timed out"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        gitops_connectivity[connected_key] = False
        logs.append("repository check timed out")
        print(f"[!] {message}")
        return gitops_connectivity

    return gitops_connectivity