from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("app")

async def http_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error", exc_info=exc, extra={"path": request.url.path})
    return JSONResponse({"detail":"Internal server error"}, status_code=500)
