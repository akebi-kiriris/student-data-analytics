from sqlalchemy import text


class AuthRepository:
    """負責 users 表的資料存取。"""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    def user_exists(self, username, email):
        session = self._session_factory()
        try:
            count = session.execute(
                text("SELECT COUNT(*) FROM users WHERE username = :username OR email = :email"),
                {"username": username, "email": email},
            ).scalar()
            return int(count or 0) > 0
        finally:
            session.close()

    def create_user(self, username, email, password_hash, full_name, role="user", is_active=True):
        session = self._session_factory()
        try:
            session.execute(
                text(
                    """
                    INSERT INTO users (username, email, password_hash, full_name, role, is_active)
                    VALUES (:username, :email, :password_hash, :full_name, :role, :is_active)
                    """
                ),
                {
                    "username": username,
                    "email": email,
                    "password_hash": password_hash,
                    "full_name": full_name,
                    "role": role,
                    "is_active": is_active,
                },
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_active_user_by_username(self, username):
        session = self._session_factory()
        try:
            result = session.execute(
                text(
                    """
                    SELECT id, username, email, password_hash, full_name, role, is_active
                    FROM users
                    WHERE username = :username AND is_active = 1
                    """
                ),
                {"username": username},
            ).mappings().first()
            return dict(result) if result else None
        finally:
            session.close()

    def update_last_login(self, user_id, login_time):
        session = self._session_factory()
        try:
            session.execute(
                text("UPDATE users SET last_login = :now WHERE id = :user_id"),
                {"now": login_time, "user_id": user_id},
            )
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_active_user_by_id(self, user_id):
        session = self._session_factory()
        try:
            result = session.execute(
                text(
                    """
                    SELECT id, username, email, full_name, role, created_at, last_login
                    FROM users
                    WHERE id = :user_id AND is_active = 1
                    """
                ),
                {"user_id": user_id},
            ).mappings().first()
            return dict(result) if result else None
        finally:
            session.close()
