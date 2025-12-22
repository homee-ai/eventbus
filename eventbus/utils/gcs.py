import os
import logging
import json
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
        if blob.name.endswith("/"):
            continue

        relative_path = os.path.relpath(blob.name, gcs_prefix)
        local_file_path = os.path.join(local_dir, relative_path)
        local_file_dir = os.path.dirname(local_file_path)
        if not os.path.exists(local_file_dir):
            os.makedirs(local_file_dir, exist_ok=True)

        logger.debug(f"Downloading {blob.name} -> {local_file_path}")
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
    blob.upload_from_string(json_data, content_type="application/json")


def upload_folder_to_gcs(bucket_name: str, local_folder: str, gcs_prefix: str) -> None:
    credentials, project_id = google.auth.default()
    client = storage.Client(project=project_id, credentials=credentials)
    bucket = client.bucket(bucket_name)

    gcs_prefix = gcs_prefix.strip("/")

    for root, dirs, files in os.walk(local_folder):
        logger.debug(f"Uploading folder {root}")
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, local_folder)

            blob_name = f"{gcs_prefix}/{relative_path}".replace("\\", "/")

            blob = bucket.blob(blob_name)
            logger.debug(f"Uploading {local_path} -> gs://{bucket_name}/{blob_name}")
            blob.upload_from_filename(local_path)


def copy_gcs_folder(
    src_bucket_name: str,
    src_blob_prefix: str,
    target_bucket_name: str,
    target_blob_prefix: str,
) -> None:
    """Copy all blobs under a given prefix from one GCS bucket to another.

    This function copies every object in the source bucket whose name starts
    with ``src_blob_prefix`` into the target bucket under the corresponding
    path below ``target_blob_prefix``. Directory placeholder blobs (objects
    whose names end with ``"/"``) are skipped.

    The source and target prefixes have leading and trailing ``"/"`` stripped
    before being used. For each source blob, the path relative to
    ``src_blob_prefix`` is computed and appended to ``target_blob_prefix`` so
    that the directory structure is preserved in the target bucket.

    The copy operation uses the GCS ``rewrite`` API, which supports efficient
    copying of large objects and may perform the copy in multiple calls for a
    single blob.

    :param src_bucket_name: Name of the bucket to copy objects from.
    :param src_blob_prefix: Prefix (virtual folder) of the blobs to copy in
        the source bucket.
    :param target_bucket_name: Name of the bucket to copy objects to. This may
        be the same as ``src_bucket_name``.
    :param target_blob_prefix: Prefix (virtual folder) under which the copied
        blobs will be written in the target bucket.
    """
    credentials, project_id = google.auth.default()
    client = storage.Client(project=project_id, credentials=credentials)

    src_bucket = client.bucket(src_bucket_name)
    target_bucket = client.bucket(target_bucket_name)

    src_blob_prefix = src_blob_prefix.strip("/")
    target_blob_prefix = target_blob_prefix.strip("/")

    blobs = client.list_blobs(src_bucket, prefix=src_blob_prefix)

    for src_blob in blobs:
        if src_blob.name.endswith("/"):
            continue

        relative_path = os.path.relpath(src_blob.name, src_blob_prefix)
        target_blob_name = f"{target_blob_prefix}/{relative_path}".replace("\\", "/")

        logger.debug(f"Copying gs://{src_bucket_name}/{src_blob.name} -> gs://{target_bucket_name}/{target_blob_name}")

        # Use rewrite for better performance with large files
        target_blob = target_bucket.blob(target_blob_name)
        rewrite_token = None
        while True:
            rewrite_token, bytes_rewritten, total_bytes = target_blob.rewrite(src_blob, token=rewrite_token)
            if rewrite_token is None:
                break


def copy_gcs_file(
    src_bucket_name: str,
    src_blob_name: str,
    target_bucket_name: str,
    target_blob_name: str,
) -> None:
    """
    Copy a single file from one GCS location to another

    Args:
        src_bucket_name: Source bucket name
        src_blob_name: Source blob path
        target_bucket_name: Target bucket name
        target_blob_name: Target blob path
    """
    credentials, project_id = google.auth.default()
    client = storage.Client(project=project_id, credentials=credentials)

    src_bucket = client.bucket(src_bucket_name)
    target_bucket = client.bucket(target_bucket_name)

    src_blob = src_bucket.blob(src_blob_name)
    target_blob = target_bucket.blob(target_blob_name)

    logger.debug(f"Copying gs://{src_bucket_name}/{src_blob_name} -> gs://{target_bucket_name}/{target_blob_name}")

    # Use rewrite for better performance with large files
    rewrite_token = None
    while True:
        rewrite_token, bytes_rewritten, total_bytes = target_blob.rewrite(src_blob, token=rewrite_token)
        if rewrite_token is None:
            break

    logger.debug(f"Successfully copied file to gs://{target_bucket_name}/{target_blob_name}")


def make_blob_public(bucket_name: str, blob_name: str) -> str:
    """
    Make a GCS blob publicly accessible

    Args:
        bucket_name: Bucket name
        blob_name: Blob path

    Returns:
        Public URL of the blob
    """
    credentials, project_id = google.auth.default()
    client = storage.Client(project=project_id, credentials=credentials)

    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    logger.debug(f"Making gs://{bucket_name}/{blob_name} publicly accessible")

    # Make blob public
    blob.make_public()

    public_url = blob.public_url
    logger.debug(f"Blob is now public: {public_url}")

    return public_url
