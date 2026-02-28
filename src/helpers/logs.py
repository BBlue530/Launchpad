from datetime import datetime, timezone

def log_handling(new_entry):
    new_entry["service_timestamp"] = datetime.now(timezone.utc).isoformat()
    print(new_entry)