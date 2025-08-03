CREATE TABLE accounts (
    user_id PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    salt VARCHAR(255) NOT NULL,
    sha256_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on email for faster lookups
CREATE INDEX idx_accounts_email ON accounts(email);