from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import hashlib
import secrets
import httpx
import os
from database import create_account, get_account_by_email

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
        return AccountResponse(user_id=user_id, email=request.email)
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

    return AccountResponse(user_id=account["user_id"], email=account["email"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
