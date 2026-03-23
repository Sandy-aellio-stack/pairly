import os
import boto3
import uuid
from fastapi import UploadFile
import logging

logger = logging.getLogger("storage")

# Configuration for AWS S3 compatible providers (S3, Cloudflare R2, Supabase Storage)
# The user can configure these environment variables to connect to their preferred provider.
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION_NAME", "us-east-1")
AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "luveloop-media")
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")  # Useful for R2 or Supabase

class StorageService:
    @staticmethod
    def get_client():
        return boto3.client(
            "s3",
            region_name=AWS_REGION,
            endpoint_url=AWS_ENDPOINT_URL,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

    @classmethod
    async def upload_file(cls, file: UploadFile, directory="messages") -> str:
        """
        Uploads a file to an S3-compatible cloud storage bucket.
        Returns the public URL of the uploaded object.
        """
        if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
            # Fallback if S3 is not configured yet (avoids crashing in dev if they haven't set env vars)
            logger.warning("AWS_ACCESS_KEY_ID or AWS_SECRET_ACCESS_KEY not configured. Falling back to local/mock URL.")
            return f"https://mock-storage.luveloop.local/{directory}/{file.filename}"

        try:
            # Generate a unique file name
            extension = os.path.splitext(file.filename)[1] if file.filename else ".bin"
            unique_filename = f"{directory}/{uuid.uuid4().hex}{extension}"

            s3 = cls.get_client()
            
            # Read file contents and upload
            contents = await file.read()
            s3.put_object(
                Bucket=AWS_BUCKET_NAME,
                Key=unique_filename,
                Body=contents,
                ContentType=file.content_type,
                ACL="public-read"  # Assuming public readable bucket for media
            )
            
            # Construct standard endpoint URL (adjust logic if using Cloudflare R2 custom domain)
            if AWS_ENDPOINT_URL:
                url = f"{AWS_ENDPOINT_URL.rstrip('/')}/{AWS_BUCKET_NAME}/{unique_filename}"
            else:
                url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{unique_filename}"
                
            return url
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise RuntimeError(f"Storage upload failed: {e}")
