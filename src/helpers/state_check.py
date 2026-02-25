from core.variables import cluster_error_message, cluster_warning_message, cluster_neutral_message, cluster_ok_message

def check_state(stored_state, entry_state):
    if entry_state == "error" or stored_state == "error":
        stored_state = "error"
        state_message = cluster_error_message

    elif entry_state == "warning" or stored_state == "warning":
        stored_state = "warning"
        state_message = cluster_warning_message

    elif entry_state == "neutral" or stored_state == "neutral":
        stored_state = "neutral"
        state_message = cluster_neutral_message

    elif entry_state == "ok" or stored_state == "ok":
        stored_state = "ok"
        state_message = cluster_ok_message

    return state_message, stored_state