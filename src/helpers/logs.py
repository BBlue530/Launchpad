from datetime import datetime, timezone

def log_handling(new_entry):
    new_entry["service_timestamp"] = datetime.now(timezone.utc).isoformat()
    print(new_entry)

def connectivity_log(logs, level, module, message):
    timestamp = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    logs.append(f"{timestamp}  {level.upper():<5}  {module}  {message}")