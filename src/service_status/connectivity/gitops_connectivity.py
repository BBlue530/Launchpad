import subprocess
import os
from datetime import datetime

def check_gitops_connectivity():
    logs = []
    message = ""
    state = ""

    gitops_repository = os.environ.get("gitops_repository")
    gitops_pat = os.environ.get("gitops_pat")
    gitops_branch_name = os.environ.get("gitops_branch_name")

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    gitops_repository_with_pat = gitops_repository.replace("https://", f"https://{gitops_pat}@")

    try:
        subprocess.run(["git", "ls-remote", gitops_repository_with_pat], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[+] Repository is reachable")
        logs.append(f"repository is reachable. timestamp: [{timestamp}]. repository [{gitops_repository}].")
        message = "Repository is reachable"
        state = "ok"
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to reach repository: {e.stderr.decode().strip()}")
        logs.append(f"repository is not reachable. timestamp: [{timestamp}]. repository [{gitops_repository}].")
        message = "Repository is not reachable"
        state = "error"
        return {"name": "Gitops", "url": "/logs/connectivity/gitops", "module": "gitops.repository", "state": state, "message": message, "logs": logs}

# Should check that the pat has the permissions needed and whatever else that could be useful

    return {"name": "Gitops", "url": "/logs/connectivity/gitops", "module": "gitops.repository", "state": state, "message": message, "logs": logs}