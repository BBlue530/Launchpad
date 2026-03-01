from time import sleep
from service_status.connectivity.gitops_connectivity import check_gitops_connectivity
from service_status.connectivity.cluster_connectivity import check_cluster_connectivity

system_connectivity_status = []

def check_external_connectivity(sleep_loop):
    global system_connectivity_status

    while True:

        gitops_connectivity = check_gitops_connectivity()
        cluster_connectivity = check_cluster_connectivity()

        system_connectivity_status.clear()
        system_connectivity_status.append(gitops_connectivity)
        system_connectivity_status.append(cluster_connectivity)

        if not sleep_loop:
            break
        
        sleep(300)