from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from snowflake_generator import SnowflakeGenerator
import os

app = FastAPI(title="Snowflake ID Service", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize snowflake generator with machine ID from environment or default to 0
machine_id = int(os.getenv("MACHINE_ID", "0"))
snowflake = SnowflakeGenerator(machine_id=machine_id)


class SnowflakeResponse(BaseModel):
    id: int


class SnowflakeParseResponse(BaseModel):
    id: int
    timestamp: int
    machine_id: int
    sequence: int
    datetime: str


@app.get("/")
async def root():
    return {"message": "Snowflake ID Service", "machine_id": machine_id}


@app.get("/id", response_model=SnowflakeResponse)
async def generate_id():
    """Generate a new snowflake ID"""
    try:
        snowflake_id = snowflake.generate_id()
        return SnowflakeResponse(id=snowflake_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/parse/{snowflake_id}", response_model=SnowflakeParseResponse)
async def parse_id(snowflake_id: int):
    """Parse a snowflake ID into its components"""
    try:
        parsed = snowflake.parse_id(snowflake_id)
        return SnowflakeParseResponse(**parsed)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid snowflake ID: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
