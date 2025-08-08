from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from cachebox import LRUCache


all_caches = {}


def get_cache(dataset: str) -> Optional[LRUCache]:
    cache = all_caches.get(dataset, None)
    if not cache:
        cache = LRUCache(maxsize=1_000_000)
        all_caches[dataset] = cache
    return cache


app = FastAPI(title="Cache Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SaveRequest(BaseModel):
    dataset: str
    key: str
    value: str


class SaveResponse(BaseModel):
    dataset: str
    key: str


class DeleteRequest(BaseModel):
    dataset: str
    key: str


class DeleteResponse(BaseModel):
    dataset: str
    key: str
    found: bool


class ReadResponse(BaseModel):
    dataset: str
    key: str
    found: bool
    value: Optional[str]


@app.post("/save", response_model=SaveResponse, status_code=status.HTTP_201_CREATED)
async def save_endpoint(request: SaveRequest):
    dataset = request.dataset
    key = request.key
    value = request.value

    cache = get_cache(request.dataset)
    cache[key] = value
    return SaveResponse(dataset=dataset, key=key)


@app.get("/read", response_model=ReadResponse, status_code=status.HTTP_200_OK)
async def read_endpoint(dataset: str, key: str):
    cache = get_cache(dataset)
    value = cache.get(key, None)
    found = value is not None
    return ReadResponse(dataset=dataset, key=key, found=found, value=value)


@app.post("/delete", response_model=DeleteResponse, status_code=status.HTTP_201_CREATED)
async def delete_endpoint(request: DeleteRequest):
    dataset = request.dataset
    key = request.key

    cache = get_cache(request.dataset)
    value = cache.get(key, None)
    found = value is not None
    cache.pop(key)
    return DeleteResponse(dataset=dataset, key=key, found=found)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
