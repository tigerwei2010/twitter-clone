CREATE TABLE tweets (
    id BIGINT PRIMARY KEY,
    user_id BIGINT,
    content VARCHAR(511) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_tweets_user_id ON tweets(user_id);