import os
import logging
import json
from pathlib import Path
from typing import Dict
import google.auth
from google.cloud import storage

logger = logging.getLogger(__name__)


def download_from_gcs(bucket_name: str, blob_name: str, file_path: str) -> None:
    credentials, project_id = google.auth.default()
    client = storage.Client(
        project=project_id,
        credentials=credentials,
    )
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    logger.info(f"Downloading blob {blob_name} from bucket {bucket_name} to {file_path}")
    blob.download_to_filename(file_path)

def upload_to_gcs(bucket_name: str, blob_name: str, file_path: str) -> None:
    credentials, project_id = google.auth.default()
    client = storage.Client(
        project=project_id,
        credentials=credentials,
    )
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)


def upload_dict_to_gcs(bucket_name: str, blob_name: str, data: dict) -> None:
    credentials, project_id = google.auth.default()
    client = storage.Client(
        project=project_id,
        credentials=credentials,
    )
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    json_data = json.dumps(data, indent=2)
    blob.upload_from_string(
        json_data,
        content_type="application/json"
    )
