from flask import Blueprint
from flask import jsonify
from flask import send_file

from database.fetch import (
    get_flagged_transactions
)

from database.metrics import (
    get_metrics
)

from reports.csv_report import (
    export_csv
)

api = Blueprint(
    "api",
    __name__
)


@api.route("/flagged")

def flagged():

    rows = get_flagged_transactions()

    return jsonify(

        [dict(r) for r in rows]

    )


@api.route("/metrics")

def metrics():

    rows = get_metrics()

    return jsonify(

        [dict(r) for r in rows]

    )


@api.route("/download")

def download():

    file = export_csv()

    if file is None:

        return {

            "message":"No fraud detected."

        }

    return send_file(
        file,
        as_attachment=True
    )