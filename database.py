import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Optional

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


def create_profile_in_db(user_id: int, handle: str, display_name: str, profile_picture_url: Optional[str]):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            if profile_picture_url:
                cursor.execute(
                    "INSERT INTO profiles (user_id, handle, display_name, profile_picture_url) VALUES (%s, %s, %s, %s)",
                    (user_id, handle, display_name, profile_picture_url)
                )
            else:
                cursor.execute(
                    "INSERT INTO profiles (user_id, handle, display_name) VALUES (%s, %s, %s)",
                    (user_id, handle, display_name)
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


def get_profile_by_user_id(user_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT user_id, handle, display_name, profile_picture_url FROM profiles WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchone()


def update_display_name(user_id: int, new_display_name: str):
    """Update the display name for a user profile"""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE profiles SET display_name = %s WHERE user_id = %s",
                (new_display_name, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0  # Returns True if a row was updated
