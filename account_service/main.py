from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import secrets
import httpx
import os
from database import *
from auth import create_access_token, get_current_user

app = FastAPI(title="Account Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Snowflake service configuration
SNOWFLAKE_URL = os.getenv("SNOWFLAKE_URL", "http://localhost:8001")


async def get_snowflake_id() -> int:
    """Get a unique ID from the snowflake service"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SNOWFLAKE_URL}/id", timeout=5.0)
            response.raise_for_status()
            data = response.json()
            return data["id"]
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Snowflake service unavailable"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate user ID"
            )


class SignupRequest(BaseModel):
    email: EmailStr
    password: str


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class AccountResponse(BaseModel):
    user_id: int
    email: str
    access_token: str
    token_type: str = "bearer"


class CreateProfileRequest(BaseModel):
    user_id: int
    handle: str
    display_name: str
    profile_picture_url: Optional[str] = None


class ProfileResponse(BaseModel):
    user_id: int
    handle: str
    display_name: str
    profile_picture_url: Optional[str] = None


class UpdateDisplayNameRequest(BaseModel):
    display_name: str


class UpdateDisplayNameResponse(BaseModel):
    user_id: int
    display_name: str
    message: str = "Display name updated successfully"


def generate_salt() -> str:
    return secrets.token_hex(32)


def hash_password(email: str, password: str, salt: str) -> str:
    combined = f"{email}{password}{salt}"
    return hashlib.sha256(combined.encode()).hexdigest()


@app.post("/signup", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest):
    # Check if email already exists
    existing_account = get_account_by_email(request.email)
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Generate salt and hash
    salt = generate_salt()
    password_hash = hash_password(request.email, request.password, salt)

    # Create account
    try:
        # Generate user_id from snowflake service
        user_id = await get_snowflake_id()
        create_account(user_id, request.email, salt, password_hash)

        # Create access token
        access_token = create_access_token(
            data={"user_id": user_id, "email": request.email})

        return AccountResponse(
            user_id=user_id,
            email=request.email,
            access_token=access_token
        )
    except HTTPException:
        # Re-raise HTTP exceptions (snowflake service errors)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create account"
        )


@app.post("/signin", response_model=AccountResponse)
async def signin(request: SigninRequest):
    # Get account by email
    account = get_account_by_email(request.email)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    print(account)
    # Verify password
    password_hash = hash_password(
        request.email, request.password, account["salt"])
    if password_hash != account["sha256_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    # Create access token
    access_token = create_access_token(
        data={"user_id": account["user_id"], "email": account["email"]})

    return AccountResponse(
        user_id=account["user_id"],
        email=account["email"],
        access_token=access_token
    )

# Protected endpoint example


@app.get("/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information using JWT token"""
    return {
        "user_id": current_user["user_id"],
        "email": current_user["email"]
    }


@app.post("/verify-token")
async def verify_user_token(current_user: dict = Depends(get_current_user)):
    """Verify if token is valid"""
    return {"valid": True, "user": current_user}


@app.post("/create_profile", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(request: CreateProfileRequest):
    # Check if profile already exists
    existing_profile = get_profile_by_user_id(request.user_id)
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already created"
        )

    # Create profile
    try:
        print(request)
        create_profile_in_db(request.user_id, request.handle,
                             request.display_name, request.profile_picture_url)

        return ProfileResponse(
            user_id=request.user_id,
            handle=request.handle,
            display_name=request.display_name,
            profile_picture_url=request.profile_picture_url
        )
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create profile"
        )


@app.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: int):
    """Get user profile by user_id"""
    try:
        profile = get_profile_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        return ProfileResponse(
            user_id=profile["user_id"],
            handle=profile["handle"],
            display_name=profile["display_name"],
            profile_picture_url=profile["profile_picture_url"]
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error getting profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get profile"
        )


@app.put("/update_display_name", response_model=UpdateDisplayNameResponse)
async def update_display_name_endpoint(
    request: UpdateDisplayNameRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update display name for the authenticated user"""
    try:
        # Validate display name is not empty
        if not request.display_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Display name cannot be empty"
            )

        # Update display name in database
        success = update_display_name(
            current_user["user_id"], request.display_name.strip())

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found"
            )

        return UpdateDisplayNameResponse(
            user_id=current_user["user_id"],
            display_name=request.display_name.strip()
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"Error updating display name: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update display name"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
