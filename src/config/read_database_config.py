import os
from config.helpers.expand_env_var import expand_env

def database_config(app_config):
    os.environ["db_username"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("database", {}).get("postgresql", {}).get("username", False))
    os.environ["db_password"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("database", {}).get("postgresql", {}).get("password", False))
    os.environ["db_name"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("database", {}).get("postgresql", {}).get("db_name", False))
    os.environ["db_host"] = expand_env(app_config.get("backend", {}).get("storage", {}).get("database", {}).get("postgresql", {}).get("db_host", False))
    print("[+] Database config set")