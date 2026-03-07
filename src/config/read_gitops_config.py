import os
from helpers.expand_env_var import expand_env

def gitops_config(app_config):
    os.environ["gitops_repository"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("repository", False))
    os.environ["gitops_pat"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("pat", False))

    os.environ["gitops_gpg_priv_key"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("gpg_priv_key", False))
    os.environ["gitops_gpg_priv_key_id"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("gpg_priv_key_id", False))

    os.environ["gitops_user_name"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("identity", {}).get("user_name", "Launchpad"))
    os.environ["gitops_user_email"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("gitops", {}).get("identity", {}).get("user_email", False))
    print("[+] Gitops repository config set")