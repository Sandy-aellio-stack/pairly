"""Media validation and processing utilities.

Functions:
    - verify_media_meta: Validate media metadata
    - generate_video_thumbnail: FFmpeg stub for thumbnail generation
"""
import re
from typing import Dict, Any, Optional
import subprocess
import tempfile
import os


# Size limits
VIDEO_MAX_SIZE = 100_000_000  # 100MB
IMAGE_MAX_SIZE = 10_000_000   # 10MB

# Allowed MIME types
ALLOWED_IMAGE_MIMES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/gif'
}
ALLOWED_VIDEO_MIMES = {
    'video/mp4', 'video/quicktime', 'video/webm', 'video/mpeg'
}


def verify_media_meta(media_item: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize media metadata.
    
    Args:
        media_item: Dict with keys: type, url, thumb_url (optional), meta
        
    Returns:
        Normalized media dict
        
    Raises:
        ValueError: If validation fails
    """
    # Validate required fields
    if 'type' not in media_item:
        raise ValueError('Media item must have type field')
    if 'url' not in media_item:
        raise ValueError('Media item must have url field')
    
    media_type = media_item['type']
    url = media_item['url']
    
    # Validate type
    if media_type not in ['image', 'video']:
        raise ValueError(f'Invalid media type: {media_type}')
    
    # Validate URL format (basic S3 URL check)
    if not url.startswith('https://') and not url.startswith('http://'):
        raise ValueError('Media URL must be a valid HTTP(S) URL')
    
    # S3 URL pattern check (optional but recommended)
    s3_pattern = r'https?://[\w.-]+\.s3[\w.-]*\.amazonaws\.com/'
    if not re.match(s3_pattern, url):
        # Also accept cloudfront URLs
        cf_pattern = r'https?://[\w.-]+\.cloudfront\.net/'
        if not re.match(cf_pattern, url):
            # Allow any HTTPS for flexibility
            pass
    
    # Validate metadata if present
    meta = media_item.get('meta', {})
    if 'size_bytes' in meta:
        size_bytes = int(meta['size_bytes'])
        if media_type == 'video':
            if size_bytes > VIDEO_MAX_SIZE:
                raise ValueError(f'Video size {size_bytes} exceeds limit of {VIDEO_MAX_SIZE} bytes')
        elif media_type == 'image':
            if size_bytes > IMAGE_MAX_SIZE:
                raise ValueError(f'Image size {size_bytes} exceeds limit of {IMAGE_MAX_SIZE} bytes')
    
    # Validate MIME type if present
    if 'mime' in meta:
        mime = meta['mime'].lower()
        if media_type == 'image' and mime not in ALLOWED_IMAGE_MIMES:
            raise ValueError(f'Unsupported image MIME type: {mime}')
        elif media_type == 'video' and mime not in ALLOWED_VIDEO_MIMES:
            raise ValueError(f'Unsupported video MIME type: {mime}')
    
    # Normalize and return
    normalized = {
        'type': media_type,
        'url': url,
        'meta': meta
    }
    
    if 'thumb_url' in media_item:
        normalized['thumb_url'] = media_item['thumb_url']
    
    return normalized


def generate_video_thumbnail(s3_url: str, output_path: Optional[str] = None) -> Optional[str]:
    """Generate video thumbnail using FFmpeg.
    
    This is a STUB implementation. In production:
    1. Download video from S3 to temp file
    2. Run FFmpeg to extract frame at 1 second
    3. Upload thumbnail to S3
    4. Return thumbnail S3 URL
    
    Worker Implementation Notes:
    ---------------------------
    This should be called by a background worker (Celery/RQ) after video upload:
    
    Example worker task:
    ```python
    @celery.task
    def process_video_thumbnail(post_id: str, video_url: str):
        thumb_url = generate_video_thumbnail(video_url)
        if thumb_url:
            # Update post with thumbnail URL
            post = await Post.get(post_id)
            for media in post.media:
                if media['url'] == video_url:
                    media['thumb_url'] = thumb_url
            await post.save()
    ```
    
    FFmpeg Command:
    ```bash
    ffmpeg -i input.mp4 -ss 00:00:01.000 -vframes 1 thumbnail.jpg
    ```
    
    Args:
        s3_url: S3 URL of the video
        output_path: Optional output path for thumbnail
        
    Returns:
        Thumbnail URL or None if FFmpeg not available
    """
    try:
        # Check if FFmpeg is available
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            timeout=5
        )
        if result.returncode != 0:
            print('FFmpeg not available')
            return None
        
        # In production, implement:
        # 1. Download video from S3
        # 2. Extract thumbnail
        # 3. Upload to S3
        # 4. Return S3 URL
        
        # For now, return None (stub)
        print(f'FFmpeg available but thumbnail generation not implemented for: {s3_url}')
        return None
        
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print('FFmpeg not available')
        return None


def validate_media_list(media_list: list) -> list:
    """Validate a list of media items.
    
    Args:
        media_list: List of media dicts
        
    Returns:
        List of validated and normalized media items
        
    Raises:
        ValueError: If any validation fails
    """
    if len(media_list) > 10:
        raise ValueError('Maximum 10 media items allowed')
    
    validated = []
    for item in media_list:
        validated.append(verify_media_meta(item))
    
    return validated
