from flask import Flask
from flask import render_template

from flask_cors import CORS

from config import DEBUG

from database.database import initialize_database

from api.routes import api

app = Flask(__name__)

CORS(app)

initialize_database()

app.register_blueprint(
    api,
    url_prefix="/api"
)


@app.route("/")

def dashboard():

    return render_template(
        "dashboard.html"
    )


if __name__ == "__main__":

    app.run(

        debug=DEBUG,

        host="0.0.0.0",

        port=5000

    )