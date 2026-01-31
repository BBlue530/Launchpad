import os
from config.helpers.expand_env_var import expand_env

def gitops_config(app_config):
    os.environ["gitops_repository"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("repository", False))
    os.environ["gitops_pat"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("pat", False))
    os.environ["gitops_branch_name"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("branch_name", False))
    print("[+] Gitops repository config set")