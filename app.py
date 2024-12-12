from flask import Flask, request, jsonify
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
import logging
import sys
import time
import boto3

load_dotenv()
app = Flask(__name__)

# Configure Azure Blob Storage
AZURE_CONNECTION_STRING = os.environ.get("AZURE_CONNECTION_STRING")
# Configure S3
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY")

CONTAINER_NAME = os.environ.get("CONTAINER_NAME", "dvr")

s3_client = boto3.client(
    "s3", aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY
)

# Initialize BlobServiceClient
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)

app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

@app.route("/ping", methods=["GET"])
def ping():
    if not AZURE_CONNECTION_STRING or (not S3_ACCESS_KEY and not S3_SECRET_KEY):
        return jsonify({"error": "connection string not found", "code": -1}), 500
    return jsonify({"status": "pong"}), 200

@app.route("/dvr/azure", methods=["POST"])
def upload_file_azure():
    data = request.get_json()

    app.logger.debug("Received payload: %s", data)

    # Extract file path from the received data
    file_path = data.get("file")
    if not file_path or not os.path.isfile(file_path):
        return jsonify({"error": "File not found", "code": -1}), 404

    # Extract the filename and use it for Blob Storage
    file_name = os.path.basename(file_path)
    blob_client = blob_service_client.get_blob_client(
        container=CONTAINER_NAME,
        blob=f"{data.get('stream')}/{data.get('stream_id')}-{data.get('client_id')}/{file_name}",
    )

    # Upload the file to Azure Blob Storage
    try:
        start_time = time.time()
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data)
        app.logger.debug("Time taken to upload file: %s", time.time() - start_time)
    except Exception as e:
        app.logger.error("Failed to upload file: %s", str(e))
        os.remove(file_path)
        return jsonify({"error": f"Failed to upload file: {str(e)}", "code": -1}), 500

    # Delete the file from the local server
    try:
        os.remove(file_path)
    except Exception as e:
        app.logger.error("Failed to delete file: %s", str(e))
        return jsonify({"error": f"Failed to delete file: {str(e)}", "code": -1}), 500

    return jsonify({"status": "File uploaded and deleted successfully", "code": 0}), 200


@app.route("/dvr/s3", methods=["POST"])
def upload_file_s3():
    data = request.get_json()

    app.logger.debug("Received payload: %s", data)

    # Extract file path from the received data
    file_path = data.get("file")
    if not file_path or not os.path.isfile(file_path):
        return jsonify({"error": "File not found", "code": -1}), 404

    # Extract the filename and use it for Blob Storage
    file_name = os.path.basename(file_path)
    start_time = time.time()
    try:
        s3_client.upload_file(
            file_path,
            CONTAINER_NAME,
            f"{data.get('stream')}/{data.get('stream_id')}-{data.get('client_id')}/{file_name}",
        )
        app.logger.debug("Time taken to upload file: %s", time.time() - start_time)
    except Exception as e:
        app.logger.error("Failed to upload file: %s", str(e))
        os.remove(file_path)
        return jsonify({"error": f"Failed to upload file: {str(e)}", "code": -1}), 500
    
    # Delete the file from the local server
    try:
        os.remove(file_path)
    except Exception as e:
        app.logger.error("Failed to delete file: %s", str(e))
        return jsonify({"error": f"Failed to delete file: {str(e)}", "code": -1}), 500
    
    return jsonify({"status": "File uploaded and deleted successfully", "code": 0}), 200


if __name__ == "__main__":
    load_dotenv()
    app.run(debug=True, host="0.0.0.0")
