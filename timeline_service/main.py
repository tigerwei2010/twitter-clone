from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth import get_current_user
from idgen import get_snowflake_id
import database as db


app = FastAPI(title="Timeline Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class FollowRequest(BaseModel):
    handle: str


class FollowResponse(BaseModel):
    followee_handle: str
    followee_display_name: str


class TweetRequest(BaseModel):
    content: str


class TweetResponse(BaseModel):
    tweet_id: int
    content: str


@app.post("/follow", response_model=FollowResponse, status_code=status.HTTP_201_CREATED)
async def follow(request: FollowRequest,
                 current_user: dict = Depends(get_current_user)):

    follower = current_user['user_id']
    followee_record = db.get_user_by_handle(request.handle)
    if not followee_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The followee handle not found"
        )

    # Check if follow relationship already exists
    followee = followee_record['user_id']
    relationship = db.get_relationship(follower, followee)
    follow_response = FollowResponse(followee_handle=followee_record['handle'],
                                     followee_display_name=followee_record['display_name']
                                     )
    if relationship:
        unfollowed = relationship['deleted']
        if unfollowed:
            db.update_relationship(relationship['id'], not unfollowed)
            return follow_response
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Already followed"
            )

    # Create relationship
    try:
        # Generate user_id from snowflake service
        relationship_id = await get_snowflake_id()
        db.create_follow_relationship(relationship_id, follower, followee)
        return follow_response
    except HTTPException:
        # Re-raise HTTP exceptions (snowflake service errors)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create follow relationship"
        )


@app.post("/tweet", response_model=TweetResponse, status_code=status.HTTP_201_CREATED)
async def create_tweet_endpoint(request: TweetRequest,
                                current_user: dict = Depends(get_current_user)):

    user_id = current_user['user_id']
    print(f'user_id = {user_id}')
    # Create relationship
    try:
        # Generate user_id from snowflake service
        content = request.content
        tweet_id = await get_snowflake_id()
        print(f'tweet_id = {tweet_id}')

        print(f'content = {content}')
        db_result = db.create_tweet(tweet_id, user_id, content)
        print(f'db_result = {db_result}')

        return TweetResponse(tweet_id=tweet_id, content=content)
    except HTTPException:
        # Re-raise HTTP exceptions (snowflake service errors)
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tweet"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
