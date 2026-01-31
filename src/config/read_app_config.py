import yaml
from config.read_database_config import database_config
from config.read_gitops_config import gitops_config
from config.read_cluster_config import cluster_config
from core.variables import app_config_path

def read_config():
    print("[+] Reading app config...")

    with open(app_config_path, "r") as f:
        app_config = yaml.safe_load(f)

    database_config(app_config)
    gitops_config(app_config)
    cluster_config(app_config)