from flask import Flask
from config.read_app_config import read_config

app = Flask(__name__)

app.secret_key = "secret-key"

from routes.home_route import home_bp
from routes.service_handling_route import service_handling_bp

app.register_blueprint(home_bp)
app.register_blueprint(service_handling_bp)

if __name__ == "__main__":
    read_config()
    app.run(debug=True)