from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from service.auth_service import ServiceError


def create_auth_blueprint(auth_service):
    auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

    @auth_bp.route("/register", methods=["POST"])
    def register():
        try:
            payload, status_code = auth_service.register(request.get_json(silent=True) or {})
            return jsonify(payload), status_code
        except ServiceError as e:
            return jsonify({"error": e.message}), e.status_code
        except Exception as e:
            return jsonify({"error": f"請求處理失敗: {str(e)}"}), 500

    @auth_bp.route("/login", methods=["POST"])
    def login():
        try:
            payload, status_code = auth_service.login(request.get_json(silent=True) or {})
            return jsonify(payload), status_code
        except ServiceError as e:
            return jsonify({"error": e.message}), e.status_code
        except Exception as e:
            return jsonify({"error": f"登入失敗: {str(e)}"}), 500

    @auth_bp.route("/profile", methods=["GET"])
    @jwt_required()
    def get_profile():
        try:
            payload, status_code = auth_service.get_profile(get_jwt_identity())
            return jsonify(payload), status_code
        except ServiceError as e:
            return jsonify({"error": e.message}), e.status_code
        except Exception as e:
            return jsonify({"error": f"獲取用戶資料失敗: {str(e)}"}), 500

    @auth_bp.route("/logout", methods=["POST"])
    @jwt_required()
    def logout():
        payload, status_code = auth_service.logout()
        return jsonify(payload), status_code

    return auth_bp
