from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from beanie import PydanticObjectId
from backend.models.user import User
from backend.models.profile import Profile, GeoJSONPoint
from typing import Optional
import jwt, os

router = APIRouter(prefix="/api/profiles")
security = HTTPBearer()

SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")
ALG = "HS256"


async def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(creds.credentials, SECRET, algorithms=[ALG])
        if payload.get("token_type") != "access":
            raise HTTPException(401, "Invalid token type")
        user = await User.get(payload["sub"])
        if not user:
            raise HTTPException(401, "User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")


class LocationInput(BaseModel):
    lat: float
    lng: float


class CreateProfileRequest(BaseModel):
    display_name: str
    bio: Optional[str]
    age: int
    price_per_message: int
    location: LocationInput


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str]
    bio: Optional[str]
    age: Optional[int]
    price_per_message: Optional[int]
    location: Optional[LocationInput]


class StatusRequest(BaseModel):
    is_online: bool


@router.get("/{id}")
async def get_profile(id: PydanticObjectId):
    profile = await Profile.get(id)
    if not profile:
        raise HTTPException(404, "Profile not found")
    return profile.dict(by_alias=True)


@router.post("/")
async def create_profile(req: CreateProfileRequest, user: User = Depends(get_current_user)):
    existing = await Profile.find_one(Profile.user_id == user.id)
    if existing:
        raise HTTPException(400, "Profile already exists")

    geo_location = GeoJSONPoint(coordinates=[req.location.lng, req.location.lat])

    profile = Profile(
        user_id=user.id,
        display_name=req.display_name,
        bio=req.bio,
        age=req.age,
        price_per_message=req.price_per_message,
        location=geo_location,
        gallery=[]
    )

    await profile.insert()
    return profile.dict(by_alias=True)


@router.patch("/me")
async def update_profile(req: UpdateProfileRequest, user: User = Depends(get_current_user)):
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")

    update_data = req.dict(exclude_unset=True)

    for key, value in update_data.items():
        if key == "location":
            profile.location = GeoJSONPoint(coordinates=[value.lng, value.lat])
        else:
            setattr(profile, key, value)

    await profile.save()
    return profile.dict(by_alias=True)


@router.post("/status")
async def update_status(req: StatusRequest, user: User = Depends(get_current_user)):
    profile = await Profile.find_one(Profile.user_id == user.id)
    if not profile:
        raise HTTPException(404, "Profile not found")

    profile.is_online = req.is_online
    await profile.save()

    return {"is_online": profile.is_online}
