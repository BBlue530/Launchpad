from time import sleep
from service_status.connectivity.gitops_connectivity import check_gitops_connectivity

system_connectivity_status = []

def check_external_connectivity():
    global system_connectivity_status

    gitops_connectivity = check_gitops_connectivity()

    system_connectivity_status.append(gitops_connectivity)

    sleep(300)