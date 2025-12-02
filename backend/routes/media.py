from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from backend.models.user import User
from backend.models.profile import Profile
from backend.routes.profiles import get_current_user
from backend.services.audit import log_event
import boto3
import os
import uuid
from typing import List

router = APIRouter(prefix="/api/media")

# S3 Configuration
S3_BUCKET = os.getenv("S3_BUCKET", "pairly-uploads")
S3_REGION = os.getenv("S3_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

def get_s3_client():
    if not AWS_ACCESS_KEY or not AWS_SECRET_KEY:
        return None
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=S3_REGION
    )

@router.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Upload profile picture to S3"""
    s3_client = get_s3_client()
    
    if not s3_client:
        raise HTTPException(500, "S3 not configured")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only images are allowed")
    
    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    file_key = f"profiles/{user.id}/{uuid.uuid4()}.{file_ext}"
    
    try:
        # Upload to S3
        contents = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file_key,
            Body=contents,
            ContentType=file.content_type
        )
        
        # Generate URL
        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file_key}"
        
        # Update profile
        profile = await Profile.find_one(Profile.user_id == user.id)
        if profile:
            profile.profile_picture_url = file_url
            await profile.save()
        
        await log_event(
            actor_user_id=user.id,
            action="profile_picture_uploaded",
            details={"url": file_url},
            severity="info"
        )
        
        return {"url": file_url}
    
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.post("/upload-gallery")
async def upload_gallery_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user)
):
    """Upload gallery image to S3"""
    s3_client = get_s3_client()
    
    if not s3_client:
        raise HTTPException(500, "S3 not configured")
    
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(400, "Only images are allowed")
    
    # Get profile
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    
    # Limit gallery size
    if len(profile.gallery_urls) >= 10:
        raise HTTPException(400, "Maximum 10 gallery images allowed")
    
    # Generate unique filename
    file_ext = file.filename.split(".")[-1]
    file_key = f"gallery/{user.id}/{uuid.uuid4()}.{file_ext}"
    
    try:
        # Upload to S3
        contents = await file.read()
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=file_key,
            Body=contents,
            ContentType=file.content_type
        )
        
        # Generate URL
        file_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file_key}"
        
        # Add to gallery
        profile.gallery_urls.append(file_url)
        await profile.save()
        
        await log_event(
            actor_user_id=user.id,
            action="gallery_image_uploaded",
            details={"url": file_url},
            severity="info"
        )
        
        return {"url": file_url, "gallery_urls": profile.gallery_urls}
    
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

@router.delete("/gallery/{image_index}")
async def delete_gallery_image(
    image_index: int,
    user: User = Depends(get_current_user)
):
    """Delete gallery image"""
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    
    if image_index < 0 or image_index >= len(profile.gallery_urls):
        raise HTTPException(400, "Invalid image index")
    
    # Remove from gallery
    removed_url = profile.gallery_urls.pop(image_index)
    await profile.save()
    
    await log_event(
        actor_user_id=user.id,
        action="gallery_image_deleted",
        details={"url": removed_url},
        severity="info"
    )
    
    return {"message": "Image deleted", "gallery_urls": profile.gallery_urls}