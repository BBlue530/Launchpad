from flask import Flask
import threading
from config.read_app_config import read_config
from service_status.external_connectivity import check_external_connectivity

app = Flask(__name__)

app.secret_key = "secret-key"

from routes.home_route import home_bp
from routes.service_handling_route import service_handling_bp
from routes.cluster_observability_route import observability_handling_bp

app.register_blueprint(home_bp)
app.register_blueprint(service_handling_bp)
app.register_blueprint(observability_handling_bp)

check_connectivity_process_thread = threading.Thread(target=check_external_connectivity, args=(True,), daemon=True)

if __name__ == "__main__":
    read_config()
    check_connectivity_process_thread.start()
    app.run(debug=True)