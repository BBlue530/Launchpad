import os
import tempfile
import base64
import yaml
from cluster_handling.deploy_helm_chart import helm_chart_deploy
from cluster_handling.deploy_backup_helm_chart import helm_chart_deploy_backup

def helm_chart_handling(helm_chart_url, helm_chart_name, helm_chart_version, helm_chart_values, cluster_namespace, cluster_release_name, deploy_backup_helm_chart):
    cluster_api_server = os.environ.get("cluster_api_server")
    cluster_token = os.environ.get("cluster_token")
    cluster_ca_cert = os.environ.get("cluster_ca_cert")

    ca_cert_bytes = base64.b64decode(cluster_ca_cert)

    with tempfile.TemporaryDirectory() as tmpdir:
        ca_path = os.path.join(tmpdir, "ca.crt")
        kubeconfig_path = os.path.join(tmpdir, "kubeconfig.yaml")
        values_path = os.path.join(tmpdir, "values.yaml")

        with open(ca_path, "wb") as f:
            f.write(ca_cert_bytes)

        kubeconfig = {
            "apiVersion": "v1",
            "kind": "Config",
            "clusters": [{
                "name": "cluster",
                "cluster": {
                    "server": cluster_api_server,
                    "certificate-authority": ca_path,
                },
            }],
            "contexts": [{
                "name": "context",
                "context": {
                    "cluster": "cluster",
                    "user": "user",
                    "namespace": cluster_namespace,
                },
            }],
            "current-context": "context",
            "users": [{
                "name": "user",
                "user": {
                    "token": cluster_token,
                },
            }],
        }

        with open(kubeconfig_path, "w") as f:
            yaml.safe_dump(kubeconfig, f)

        with open(values_path, "w") as f:
            yaml.safe_dump(helm_chart_values, f)

        if deploy_backup_helm_chart:
            result_json = helm_chart_deploy_backup(helm_chart_name, helm_chart_version, cluster_namespace, cluster_release_name, values_path, kubeconfig_path)
        else:
            result_json = helm_chart_deploy(helm_chart_url, helm_chart_name, helm_chart_version, cluster_namespace, cluster_release_name, values_path, kubeconfig_path)

        return result_json