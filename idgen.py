from fastapi import HTTPException, status
import httpx
import os


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
