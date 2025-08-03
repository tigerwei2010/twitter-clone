from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from snowflake_generator import SnowflakeGenerator
import os

app = FastAPI(title="Snowflake ID Service", version="1.0.0")

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

@app.get("/ids/{count}")
async def generate_multiple_ids(count: int = Query(..., ge=1, le=1000)):
    """Generate multiple snowflake IDs"""
    if count > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 IDs per request")
    
    try:
        ids = [snowflake.generate_id() for _ in range(count)]
        return {"ids": ids, "count": len(ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/parse/{snowflake_id}", response_model=SnowflakeParseResponse)
async def parse_id(snowflake_id: int):
    """Parse a snowflake ID into its components"""
    try:
        parsed = snowflake.parse_id(snowflake_id)
        return SnowflakeParseResponse(**parsed)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid snowflake ID: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)