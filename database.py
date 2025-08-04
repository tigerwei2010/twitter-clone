import psycopg2
from psycopg2.extras import RealDictCursor
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://localhost/postgres")


def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def create_account(user_id: int, email: str, salt: str, sha256_hash: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO accounts (user_id, email, salt, sha256_hash) VALUES (%s, %s, %s, %s)",
                (user_id, email, salt, sha256_hash)
            )
            conn.commit()


def get_account_by_email(email: str):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, email, salt, sha256_hash FROM accounts WHERE email = %s",
                (email,)
            )
            return cursor.fetchone()
