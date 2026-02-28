from flask import request, flash
import time
import subprocess
import json
from helpers.logs import log_handling

def run_kubectl(kubeconfig_path, args):
    start_time = time.time()

    try:
        result = subprocess.run(["kubectl", "--kubeconfig", kubeconfig_path] + args, capture_output=True, text=True, check=True,)

        duration_ms = int((time.time() - start_time) * 1000)

        log_handling({
            "message": f"Cluster called using [{args}] and took: [{duration_ms} ms]",
            "level": "info",
            "module": "run_kubectl",
            "client_ip": request.remote_addr,
        })

        return json.loads(result.stdout)
    
    except subprocess.CalledProcessError as e:
        duration_ms = int((time.time() - start_time) * 1000)

        log_handling({
            "message": f"Cluster called failed using [{args}] and took: [{duration_ms}] error: [{e}]",
            "level": "Error",
            "module": "run_kubectl",
            "client_ip": request.remote_addr,
        })

        flash(
            f"Cluster Calling failed after [{duration_ms} ms]",
            "message-status-false",
        )

        return None