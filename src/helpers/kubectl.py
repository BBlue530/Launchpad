import subprocess
import json

def run_kubectl(kubeconfig_path, args):
    result = subprocess.run(["kubectl", "--kubeconfig", kubeconfig_path] + args, capture_output=True, text=True, check=True,)
    return json.loads(result.stdout)