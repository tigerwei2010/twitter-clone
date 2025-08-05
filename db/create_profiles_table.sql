CREATE TABLE profiles (
    user_id BIGINT PRIMARY KEY,
    handle VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    profile_picture_url VARCHAR(1023),
    -- profile_picture_thumbnail VARCHAR(1023),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX idx_profiles_handle ON profiles(handle);