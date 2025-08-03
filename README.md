# Twitter Clone Services

A collection of microservices for building a Twitter-like application, including account management and unique ID generation.

## Services

### Account Service
FastAPI-based user account management system with secure authentication.

**Features:**
- User registration (`/signup`)
- User authentication (`/signin`)
- Password hashing with salt using SHA256
- PostgreSQL database integration
- Email validation

**API Endpoints:**
- `POST /signup` - Create new user account
- `POST /signin` - Authenticate user

### Snowflake ID Service
High-performance distributed unique ID generator based on Twitter's Snowflake algorithm.

**Features:**
- 64-bit unique IDs with timestamp, machine ID, and sequence components
- Thread-safe ID generation
- Support for multiple machine instances
- ID parsing and component extraction
- Custom epoch (January 1, 2025)

**API Endpoints:**
- `GET /id` - Generate single unique ID
- `GET /ids/{count}` - Generate multiple IDs (max 1000)
- `GET /parse/{id}` - Parse ID into components

## Project Structure

```
├── CLAUDE.md                 # Development guidance for Claude Code
├── README.md                 # This file
├── requirements.txt          # Account service dependencies
├── main.py                   # Account service FastAPI app
├── database.py               # Database operations
├── db/
│   └── create_accounts_table.sql  # Database schema
└── snowflake/
    ├── main.py               # Snowflake service FastAPI app
    ├── snowflake_generator.py # Core ID generation logic
    ├── test_snowflake_generator.py # Comprehensive tests
    ├── run_tests.py          # Test runner utility
    └── requirements.txt      # Snowflake service dependencies
```

## Quick Start

### Prerequisites
- Python 3.8+
- PostgreSQL database

### Account Service Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up database:
   ```bash
   # Create PostgreSQL database
   createdb your_database
   
   # Run schema migration
   psql -d your_database -f db/create_accounts_table.sql
   ```

3. Set environment variables:
   ```bash
   export DATABASE_URL="postgresql://user:password@localhost/your_database"
   ```

4. Run the service:
   ```bash
   uvicorn main:app --reload
   ```

### Snowflake Service Setup

1. Navigate to snowflake directory:
   ```bash
   cd snowflake
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the service:
   ```bash
   uvicorn main:app --port 8001 --reload
   ```

4. Set machine ID (optional):
   ```bash
   export MACHINE_ID=1
   uvicorn main:app --port 8001 --reload
   ```

### Running Tests

For the Snowflake service:
```bash
cd snowflake
pytest test_snowflake_generator.py -v
```

## Database Schema

### Accounts Table
```sql
CREATE TABLE accounts (
    user_id PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    salt VARCHAR(255) NOT NULL,
    sha256_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Configuration

### Environment Variables

**Account Service:**
- `DATABASE_URL` - PostgreSQL connection string

**Snowflake Service:**
- `MACHINE_ID` - Unique machine identifier (0-1023, default: 0)

## Security Features

- **Password Security**: Uses random salt generation with SHA256 hashing
- **Email Validation**: Pydantic email validation
- **SQL Injection Protection**: Parameterized queries
- **Thread Safety**: Concurrent ID generation support

## API Documentation

Both services provide interactive API documentation:
- Account Service: http://localhost:8000/docs
- Snowflake Service: http://localhost:8001/docs

## Development

This project uses:
- **FastAPI** for REST API framework
- **Pydantic** for data validation
- **psycopg2** for PostgreSQL connectivity
- **pytest** for testing
- **uvicorn** for ASGI server

## License

MIT License