from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from app.core.config import settings

# Initialize the MinIO object_storage_client
object_storage_client = Minio(
    settings.S3_ENDPOINT_URL,  # MinIO address
    access_key=settings.S3_ACCESS_KEY,  # MinIO access key
    secret_key=settings.S3_SECRET_ACCESS_KEY,  # MinIO secret key
    secure=False,  # Set to True if using https
)

# Check if the bucket already exists
if not object_storage_client.bucket_exists(settings.S3_BUCKET_NAME):
    try:
        # Create the bucket
        object_storage_client.make_bucket(settings.S3_BUCKET_NAME)
    except S3Error as e:
        print(f"Error occurred: {e}")


def upload_file(file_path, bucket_name, object_name):
    object = object_storage_client.fput_object(bucket_name, object_name, file_path)
    return object


# Function to generate a presigned URL for uploading a file
def generate_presigned_url(object_name, expiration=3600):
    try:
        # Generate the presigned URL to upload a file
        presigned_url = object_storage_client.presigned_put_object(
            settings.S3_BUCKET_NAME, object_name, expires=timedelta(seconds=expiration)
        )
        return presigned_url
    except S3Error as e:
        print(f"Error generating presigned URL: {e}")
        return None


def generate_presigned_url_for_download(object_name, expiration=3600, filename=None):
    try:
        response_headers = None
        if filename:
            response_headers = {
                "response-content-disposition": f'attachment; filename="{filename}"'
            }

        presigned_url = object_storage_client.presigned_get_object(
            settings.S3_BUCKET_NAME,
            object_name,
            expires=timedelta(seconds=expiration),
            response_headers=response_headers,  # type: ignore
        )
        return presigned_url
    except S3Error as e:
        print(f"Error generating presigned URL: {e}")
        return None


def get_head_object(object_name):
    try:
        # Fetch metadata of the object (like head request in S3)
        head_object = object_storage_client.stat_object(
            settings.S3_BUCKET_NAME, object_name
        )
        return head_object
    except S3Error as e:
        print(f"Error fetching head object: {e}")
        return None


def get_object(object_name):
    try:
        # Retrieve the actual object from MinIO
        object = object_storage_client.get_object(settings.S3_BUCKET_NAME, object_name)
        return object
    except S3Error as e:
        print(f"Error retrieving object: {e}")
        return None
