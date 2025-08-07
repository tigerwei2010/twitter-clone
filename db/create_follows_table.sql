CREATE TABLE follows (
    id BIGINT PRIMARY KEY,
    follower BIGINT,  -- follower's user id
    followee BIGINT,  -- followee's user id
    deleted BOOLEAN DEFAULT FALSE,    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on follower and followee for faster lookups
CREATE INDEX idx_follows_follower ON follows(follower);
CREATE INDEX idx_follows_followee ON follows(followee);