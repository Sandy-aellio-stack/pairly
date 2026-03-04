from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from typing import Union
from beanie import PydanticObjectId

def validate_object_id(id_str: str, entity_name: str = "User") -> PydanticObjectId:
    """
    Safely convert string to PydanticObjectId with consistent error handling.
    
    Args:
        id_str: The string ID to convert
        entity_name: Name of the entity for the error message (e.g. "User", "Message")
        
    Returns:
        PydanticObjectId
        
    Raises:
        HTTPException: 400 if ID is invalid
    """
    if not id_str:
        raise HTTPException(status_code=400, detail=f"{entity_name} ID is required")
        
    try:
        return PydanticObjectId(id_str)
    except (InvalidId, Exception):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid {entity_name} ID format"
        )

def to_object_id(id_str: str) -> ObjectId:
    """Convert string to raw BSON ObjectId for low-level queries"""
    try:
        return ObjectId(id_str)
    except (InvalidId, Exception):
        raise HTTPException(
            status_code=400, 
            detail="Invalid ID format"
        )
