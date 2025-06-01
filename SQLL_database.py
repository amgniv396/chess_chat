import sqlite3
import hashlib
import secrets
from datetime import datetime


class UserDatabase:
    def __init__(self, db_file="user_data.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_file = db_file
        self.create_tables()

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rating INTEGER DEFAULT 0,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
        ''')

        # Pending users table (for storing users before email verification)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            verification_code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Password reset codes table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            reset_code TEXT NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

        # Failed login attempts table (for security)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS login_attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            ip_address TEXT,
            attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            successful BOOLEAN DEFAULT FALSE
        )
        ''')

        conn.commit()
        conn.close()

    def _hash_password(self, password, salt=None):
        """Hash a password with a salt for secure storage"""
        if salt is None:
            salt = secrets.token_hex(16)

        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # Number of iterations
        ).hex()

        return password_hash, salt

    def add_user(self, username, email, password):
        """Add a verified user to the database"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Hash the password with a new salt
            password_hash, salt = self._hash_password(password)

            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, email.lower(), password_hash, salt)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # User already exists
            return False
        finally:
            conn.close()

    def add_pending_user(self, username, email, password, verification_code, expiry_minutes=30):
        """Add a user to pending verification"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Hash the password with a new salt
            password_hash, salt = self._hash_password(password)

            # Calculate expiry time
            expiry_time = datetime.now().timestamp() + (expiry_minutes * 60)

            # First delete any existing pending user with same email or username
            cursor.execute("DELETE FROM pending_users WHERE email = ? OR username = ?",
                           (email.lower(), username))

            # Insert new pending user
            cursor.execute(
                """INSERT INTO pending_users 
                   (username, email, password_hash, salt, verification_code, expires_at) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (username, email.lower(), password_hash, salt, verification_code, expiry_time)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # There was an issue with the insertion
            return False
        finally:
            conn.close()

    def verify_user(self, email, verification_code):
        """Verify a user's email and move them from pending to active users"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Get the pending user info
            cursor.execute(
                "SELECT username, email, password_hash, salt, expires_at FROM pending_users WHERE email = ? AND verification_code = ?",
                (email.lower(), verification_code)
            )
            user_data = cursor.fetchone()

            if not user_data:
                return False, "Invalid verification code"

            username, email, password_hash, salt, expires_at = user_data

            # Check if code is expired
            if float(expires_at) < datetime.now().timestamp():
                return False, "Verification code expired"

            # Add to verified users
            cursor.execute(
                "INSERT INTO users (username, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, salt)
            )

            # Remove from pending users
            cursor.execute("DELETE FROM pending_users WHERE email = ?", (email,))

            conn.commit()
            return True, "User verified successfully"
        except sqlite3.IntegrityError:
            return False, "Username or email already exists"
        finally:
            conn.close()

    def authenticate_user(self, username_or_email, password, ip_address=None):
        """Authenticate a user and return user data if successful"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Check if input is email or username
            if '@' in username_or_email:
                query = "SELECT id, username, email, password_hash, salt FROM users WHERE email = ? AND is_active = TRUE"
            else:
                query = "SELECT id, username, email, password_hash, salt FROM users WHERE username = ? AND is_active = TRUE"

            cursor.execute(query, (username_or_email.lower(),))
            user_data = cursor.fetchone()

            # Record the login attempt
            if ip_address:
                cursor.execute(
                    "INSERT INTO login_attempts (username, ip_address) VALUES (?, ?)",
                    (username_or_email, ip_address)
                )

            if not user_data:
                conn.commit()
                return False, "Invalid username or email"

            user_id, username, email, stored_hash, salt = user_data

            # Verify password
            calculated_hash, _ = self._hash_password(password, salt)

            if calculated_hash == stored_hash:
                # Update last login time
                cursor.execute(
                    "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (user_id,)
                )

                # Mark login attempt as successful
                if ip_address:
                    cursor.execute(
                        "UPDATE login_attempts SET successful = TRUE WHERE username = ? ORDER BY attempt_time DESC LIMIT 1",
                        (username_or_email,)
                    )

                conn.commit()
                return True, {"id": user_id, "username": username, "email": email}
            else:
                conn.commit()
                return False, "Invalid password"
        finally:
            conn.close()

    def create_password_reset(self, email, reset_code, expiry_minutes=30):
        """Create a password reset code for a user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # First check if user exists
            cursor.execute("SELECT id FROM users WHERE email = ? AND is_active = TRUE", (email.lower(),))
            user = cursor.fetchone()

            if not user:
                return False, "Email not found"

            # Calculate expiry time
            expiry_time = datetime.now().timestamp() + (expiry_minutes * 60)

            # Delete any existing reset codes for this email
            cursor.execute("DELETE FROM password_resets WHERE email = ?", (email.lower(),))

            # Insert new reset code
            cursor.execute(
                "INSERT INTO password_resets (email, reset_code, expires_at) VALUES (?, ?, ?)",
                (email.lower(), reset_code, expiry_time)
            )

            conn.commit()
            return True, "Reset code created"
        finally:
            conn.close()

    def verify_reset_code(self, email, reset_code):
        """Verify a password reset code"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT expires_at FROM password_resets WHERE email = ? AND reset_code = ?",
                (email.lower(), reset_code)
            )

            result = cursor.fetchone()

            if not result:
                return False, "Invalid reset code"

            expires_at = float(result[0])

            if expires_at < datetime.now().timestamp():
                return False, "Reset code expired"

            return True, "Valid reset code"
        finally:
            conn.close()

    def reset_password(self, email, reset_code, new_password):
        """Reset a user's password after verification"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # First verify the reset code
            verified, message = self.verify_reset_code(email, reset_code)

            if not verified:
                return False, message

            # Hash the new password
            password_hash, salt = self._hash_password(new_password)

            # Update the user's password
            cursor.execute(
                "UPDATE users SET password_hash = ?, salt = ? WHERE email = ?",
                (password_hash, salt, email.lower())
            )

            # Delete the used reset code
            cursor.execute("DELETE FROM password_resets WHERE email = ?", (email.lower(),))

            conn.commit()
            return True, "Password reset successfully"
        finally:
            conn.close()

    def resend_verification(self, email, new_code, expiry_minutes=30):
        """Update verification code for pending user"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Calculate new expiry time
            expiry_time = datetime.now().timestamp() + (expiry_minutes * 60)

            cursor.execute(
                "UPDATE pending_users SET verification_code = ?, expires_at = ? WHERE email = ?",
                (new_code, expiry_time, email.lower())
            )

            if cursor.rowcount == 0:
                return False, "Email not found in pending users"

            conn.commit()
            return True, "Verification code updated"
        finally:
            conn.close()

    def get_pending_user_email(self, username_or_email):
        """Get email of pending user by username or email"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            if '@' in username_or_email:
                query = "SELECT email FROM pending_users WHERE email = ?"
            else:
                query = "SELECT email FROM pending_users WHERE username = ?"

            cursor.execute(query, (username_or_email.lower(),))
            result = cursor.fetchone()

            if result:
                return result[0]
            return None
        finally:
            conn.close()

    def email_exists(self, email):
        """Check if email exists in users or pending users"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Check in active users
            cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
            if cursor.fetchone():
                return True

            # Check in pending users
            cursor.execute("SELECT id FROM pending_users WHERE email = ?", (email.lower(),))
            if cursor.fetchone():
                return True

            return False
        finally:
            conn.close()

    def username_exists(self, username):
        """Check if username exists in users or pending users"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Check in active users
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                return True

            # Check in pending users
            cursor.execute("SELECT id FROM pending_users WHERE username = ?", (username,))
            if cursor.fetchone():
                return True

            return False
        finally:
            conn.close()

    def cleanup_expired_records(self):
        """Clean up expired password reset codes and pending users"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            current_time = datetime.now().timestamp()

            # Delete expired password reset codes
            cursor.execute(
                "DELETE FROM password_resets WHERE expires_at < ?",
                (current_time,)
            )

            # Delete expired pending users
            cursor.execute(
                "DELETE FROM pending_users WHERE expires_at < ?",
                (current_time,)
            )

            conn.commit()
        finally:
            conn.close()

    def add_sample_user(self):
        """Add a sample user for testing"""
        if not self.email_exists("eyal.shara@gmail.com") and not self.username_exists("eyal"):
            self.add_user("eyal", "eyal.shara@gmail.com", "12345678")

    # Add this function to SQLL_database.py in the UserDatabase class

    def update_username(self, old_username, new_username):
        """Update a user's username"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Check if the old username exists
            cursor.execute("SELECT id FROM users WHERE username = ? AND is_active = TRUE", (old_username,))
            user = cursor.fetchone()

            if not user:
                return False, "User not found"

            # Check if the new username already exists
            cursor.execute("SELECT id FROM users WHERE username = ? AND is_active = TRUE", (new_username,))
            existing_user = cursor.fetchone()

            if existing_user:
                return False, "Username already exists"

            # Update the username
            cursor.execute(
                "UPDATE users SET username = ? WHERE username = ?",
                (new_username, old_username)
            )

            conn.commit()
            return True, "Username updated successfully"
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()

    # Add this function to SQLL_database.py in the UserDatabase class

    def add_rating(self, username, rating_to_add):
        """Add to a user's existing rating"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        try:
            # Check if the username exists and get current rating
            cursor.execute("SELECT id, rating FROM users WHERE username = ? AND is_active = TRUE", (username,))
            user = cursor.fetchone()

            if not user:
                return False, "User not found"

            user_id, current_rating = user
            new_rating = current_rating + rating_to_add

            # Validate that the new rating doesn't go below 0
            if new_rating < 0:
                return False, "Rating cannot go below zero"

            # Update the rating
            cursor.execute(
                "UPDATE users SET rating = ? WHERE username = ?",
                (new_rating, username)
            )

            conn.commit()
            return True, f"Rating updated successfully. New rating: {new_rating}"
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        finally:
            conn.close()


# Example usage
if __name__ == "__main__":
    # Create database instance
    db = UserDatabase()

    # Add a sample user
    db.add_sample_user()

    print("Database initialized with sample user: user@example.com / password123")