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
    logger.debug(f"Downloading blob {blob_name} from bucket {bucket_name} to {file_path}")
    blob.download_to_filename(file_path)

def download_folder_from_gcs(bucket_name: str, gcs_prefix: str, local_dir: str) -> None:
    credentials, project_id = google.auth.default()
    client = storage.Client(project=project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)
    gcs_prefix = gcs_prefix.strip("/")
    blobs = client.list_blobs(bucket, prefix=gcs_prefix)

    for blob in blobs:
        if blob.name.endswith('/'):
            continue

        relative_path = os.path.relpath(blob.name, gcs_prefix)
        local_file_path = os.path.join(local_dir, relative_path)
        local_file_dir = os.path.dirname(local_file_path)
        if not os.path.exists(local_file_dir):
            os.makedirs(local_file_dir, exist_ok=True)

        logger.info(f"Downloading {blob.name} -> {local_file_path}")
        blob.download_to_filename(local_file_path)

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

def upload_folder_to_gcs(bucket_name: str, local_folder: str, gcs_prefix: str) -> None:
    credentials, project_id = google.auth.default()
    client = storage.Client(project=project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)

    gcs_prefix = gcs_prefix.strip("/")

    for root, dirs, files in os.walk(local_folder):
        logger.info(f"Uploading folder {root}")
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_folder)

            blob_name = f"{gcs_prefix}/{relative_path}".replace("\\", "/")

            blob = bucket.blob(blob_name)
            logger.debug(f"Uploading {local_path} -> gs://{bucket_name}/{blob_name}")
            blob.upload_from_filename(local_path)