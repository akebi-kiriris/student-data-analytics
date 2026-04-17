from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from service import database_service


def create_database_blueprint():
    db_bp = Blueprint("database", __name__)

    def to_http(result):
        if isinstance(result, tuple) and len(result) == 2:
            payload, status = result
        else:
            payload, status = result, 200
        return jsonify(payload), status

    @db_bp.route('/api/database/tables', methods=['GET'])
    @jwt_required()
    def list_database_tables_new():
        result = database_service.list_database_tables_new(current_user_id=get_jwt_identity())
        return to_http(result)

    @db_bp.route('/api/table_columns', methods=['POST'])
    @jwt_required()
    def get_table_columns():
        data = request.get_json(silent=True) or {}
        return to_http(database_service.get_table_columns(data.get('table_name')))

    @db_bp.route('/api/database/tables/<table_name>/count', methods=['GET'])
    @jwt_required()
    def get_table_row_count(table_name):
        return to_http(database_service.get_table_row_count(table_name))

    @db_bp.route('/api/database/tables/<table_name>/data', methods=['GET'])
    @jwt_required()
    def get_table_data(table_name):
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '')
        return to_http(
            database_service.get_table_data(
                table_name=table_name,
                current_user_id=get_jwt_identity(),
                page=page,
                limit=limit,
                search=search,
            )
        )

    @db_bp.route('/api/database/tables/<table_name>/data', methods=['POST'])
    @jwt_required()
    def create_table_row(table_name):
        data = request.get_json(silent=True) or {}
        return to_http(database_service.create_table_row(table_name, get_jwt_identity(), data))

    @db_bp.route('/api/database/tables/<table_name>/data/<int:row_id>', methods=['PUT'])
    @jwt_required()
    def update_table_row(table_name, row_id):
        data = request.get_json(silent=True) or {}
        return to_http(database_service.update_table_row(table_name, row_id, get_jwt_identity(), data))

    @db_bp.route('/api/database/tables/<table_name>/data/<int:row_id>', methods=['DELETE'])
    @jwt_required()
    def delete_table_row(table_name, row_id):
        return to_http(database_service.delete_table_row(table_name, row_id, get_jwt_identity()))

    return db_bp
