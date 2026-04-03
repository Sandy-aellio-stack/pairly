from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
from uuid import uuid4

router = APIRouter()

UPLOAD_DIR = Path(__file__).resolve().parents[2] / 'uploads'
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post('/api/upload')
async def upload_image(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='File must be an image')

    filename = f"{uuid4().hex}_{file.filename}"
    path = UPLOAD_DIR / filename

    try:
        contents = await file.read()
        with open(path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Upload failed: {e}')

    # Return absolute URL pointing to mounted static files (assumes backend host/port)
    url = f"/uploads/{filename}"
    return JSONResponse({'url': url})

