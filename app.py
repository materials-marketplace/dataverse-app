"""Simple flask app to connect the dataverse to Marketplace."""

import json
import logging

from flask import Flask, jsonify, make_response, request, send_file

from dataverse_query.dataset import Dataset
from dataverse_query.dataverse_query import DataverseQuery

DATAVERSE_URL = "https://entrepot.recherche.data.gouv.fr/"


app = Flask(__name__)


@app.route("/headers")
def headers():
    return json.dumps(dict(request.headers))


dq = DataverseQuery(DATAVERSE_URL)


@app.route("/heartbeat")
def heartbeat():
    return "Dataverse app: application running."


@app.route("/dataset", methods=["GET"])
def getCollection():
    logging.info("Request for all datasets.")
    return dq.get_all_datasets()


@app.route("/dataset/<path:datasetId>", methods=["GET"])
def getDataset(datasetId: str):
    logging.info(f"Request for dataset {datasetId}.")
    file = dq.get_dataset(datasetId)
    return make_response(file)


@app.route("/metadata/<path:datasetId>", methods=["HEAD"])
def getMetadata(datasetId: str):
    logging.info(f"Request for dataset's {datasetId} metadata.")
    dataset = Dataset(dq.get_dataset_metadata(datasetId))
    filename = "".join(i for i in datasetId if i not in "\\/:*?<>|") + ".ttl"
    dataset.to_dcat_file(filename)
    return send_file(filename)


@app.route("/globalSearch", methods=["GET"])
def globalSearch():
    query = request.args.get("q")
    logging.info(f"Global search request with query: {query}")
    return make_response(jsonify(dq.global_search(query)))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8080)
