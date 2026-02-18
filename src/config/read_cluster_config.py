import os
from helpers.expand_env_var import expand_env

def cluster_config(app_config):
    os.environ["cluster_api_server"] = expand_env(app_config.get("backend", {}).get("cluster", {}).get("api_server", False))
    os.environ["cluster_token"] = expand_env(app_config.get("backend", {}).get("cluster", {}).get("token", False))
    os.environ["cluster_ca_cert"] = expand_env(app_config.get("backend", {}).get("cluster", {}).get("ca_cert", False))
    print("[+] Cluster config set")