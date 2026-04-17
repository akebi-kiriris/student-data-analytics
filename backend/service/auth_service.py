from datetime import datetime, timezone


class ServiceError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthService:
    """處理認證相關商業邏輯。"""

    def __init__(self, repository, hash_password_fn, check_password_fn, token_factory):
        self.repository = repository
        self.hash_password_fn = hash_password_fn
        self.check_password_fn = check_password_fn
        self.token_factory = token_factory

    def register(self, data):
        required_fields = ["username", "email", "password"]
        for field in required_fields:
            if not data.get(field):
                raise ServiceError(f"缺少必要欄位: {field}", 400)

        username = str(data["username"]).strip()
        email = str(data["email"]).strip()
        password = str(data["password"])
        full_name = str(data.get("full_name", "")).strip()

        if len(username) < 3:
            raise ServiceError("使用者名稱至少需要3個字元", 400)

        if len(password) < 6:
            raise ServiceError("密碼至少需要6個字元", 400)

        if self.repository.user_exists(username, email):
            raise ServiceError("使用者名稱或 Email 已存在", 400)

        password_hash = self.hash_password_fn(password)
        self.repository.create_user(
            username=username,
            email=email,
            password_hash=password_hash,
            full_name=full_name,
            role="user",
            is_active=True,
        )

        return {
            "success": True,
            "message": "註冊成功",
            "user": {
                "username": username,
                "email": email,
                "full_name": full_name,
                "role": "user",
            },
        }, 201

    def login(self, data):
        username = str(data.get("username", "")).strip()
        password = str(data.get("password", ""))

        if not username or not password:
            raise ServiceError("請輸入使用者名稱和密碼", 400)

        user_data = self.repository.get_active_user_by_username(username)
        if not user_data:
            raise ServiceError("使用者名稱或密碼錯誤", 401)

        stored_password_hash = user_data.get("password_hash")
        if isinstance(stored_password_hash, str):
            stored_password_hash = stored_password_hash.encode("utf-8")

        if not self.check_password_fn(password, stored_password_hash):
            raise ServiceError("使用者名稱或密碼錯誤", 401)

        self.repository.update_last_login(user_data["id"], datetime.now(timezone.utc))

        access_token = self.token_factory(
            identity=str(user_data["id"]),
            additional_claims={
                "username": user_data["username"],
                "role": user_data["role"],
            },
        )

        return {
            "success": True,
            "message": "登入成功",
            "access_token": access_token,
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "full_name": user_data.get("full_name"),
                "role": user_data["role"],
            },
        }, 200

    def get_profile(self, jwt_identity):
        try:
            user_id = int(jwt_identity)
        except (TypeError, ValueError):
            raise ServiceError("無效的使用者識別", 401)

        user_data = self.repository.get_active_user_by_id(user_id)
        if not user_data:
            raise ServiceError("用戶不存在", 404)

        return {
            "success": True,
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "email": user_data["email"],
                "full_name": user_data.get("full_name"),
                "role": user_data["role"],
                "created_at": user_data.get("created_at").isoformat() if user_data.get("created_at") else None,
                "last_login": user_data.get("last_login").isoformat() if user_data.get("last_login") else None,
            },
        }, 200

    def logout(self):
        return {"success": True, "message": "登出成功"}, 200
