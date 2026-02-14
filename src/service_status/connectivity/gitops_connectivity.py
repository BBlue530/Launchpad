import subprocess
import os
from datetime import datetime
from core.variables import gitops_name, gitops_logs_endpoint, gitops_module_name, state_key, message_key, logs_key

def check_gitops_connectivity():
    gitops_connectivity = {"name": gitops_name, "url": gitops_logs_endpoint, "module": gitops_module_name, state_key: "neutral", message_key: "Not checked", logs_key: []}
    logs = []
    gitops_connectivity[logs_key] = logs

    gitops_repository = os.environ.get("gitops_repository")
    gitops_pat = os.environ.get("gitops_pat")
    gitops_branch_name = os.environ.get("gitops_branch_name")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if not gitops_repository or not gitops_pat:
        message = "Gitops configuration missing"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        logs.append(f"missing environment variables. timestamp: [{timestamp}]")
        print(f"[!] {message}")
        return gitops_connectivity
    
    gitops_repository_with_pat = gitops_repository.replace("https://", f"https://{gitops_pat}@")

    try:
        subprocess.run(["git", "ls-remote", gitops_repository_with_pat], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)
        message = "Repository is reachable"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "ok"
        logs.append(f"repository is reachable. timestamp: [{timestamp}]. repository [{gitops_repository}].")
        print(f"[+] {message}")

    except subprocess.CalledProcessError as e:
        message = "Repository is not reachable"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        logs.append(f"repository is not reachable. timestamp: [{timestamp}]. repository [{gitops_repository}].")
        print(f"[!] {message}")
        return gitops_connectivity
    
    except subprocess.TimeoutExpired:
        message = "Repository check timed out"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        logs.append("repository check timed out")
        print(f"[!] {message}")
        return gitops_connectivity

    try:
        result = subprocess.run(["git", "ls-remote", "--heads", gitops_repository_with_pat, gitops_branch_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15)

        if result.stdout:
            message = f"Repository reachable and branch '{gitops_branch_name}' exists"
            gitops_connectivity[message_key] = message
            gitops_connectivity[state_key] = "ok"
            logs.append(f"branch {gitops_branch_name} exists at [{timestamp}]")
            print(f"[+] {message}")

        else:
            message = f"Repository reachable but branch '{gitops_branch_name}' missing"
            gitops_connectivity[message_key] = message
            gitops_connectivity[state_key] = "warning"
            logs.append(f"branch {gitops_branch_name} missing at [{timestamp}]")
            print(f"[!] {message}")
            return gitops_connectivity

    except subprocess.CalledProcessError as e:
        message = "Repository reachable but branch check failed"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "warning"
        logs.append(e.stderr.decode().strip())
        print(f"[!] {message}")
        return gitops_connectivity

    except subprocess.TimeoutExpired:
        message = "Repository check timed out"
        gitops_connectivity[message_key] = message
        gitops_connectivity[state_key] = "error"
        logs.append("repository check timed out")
        print(f"[!] {message}")
        return gitops_connectivity

# Should check that the pat has the permissions needed and whatever else that could be useful

    return gitops_connectivity