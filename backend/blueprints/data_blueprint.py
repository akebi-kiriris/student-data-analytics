from flask import Blueprint, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity, jwt_required

from service import data_service


def _to_http(result):
    if isinstance(result, tuple) and len(result) == 2:
        payload, status = result
    else:
        payload, status = result, 200

    if isinstance(payload, dict) and payload.get('action') == 'send_file':
        return send_from_directory(payload['directory'], payload['filename']), status

    return jsonify(payload), status


def create_data_blueprint():
    data_bp = Blueprint('data', __name__)

    @data_bp.route('/api/upload', methods=['POST'])
    @jwt_required()
    def upload_file():
        file = request.files.get('file')
        sheet_name = request.form.get('sheet_name', None)
        result = data_service.upload_file(file, sheet_name, get_jwt_identity())
        return _to_http(result)

    @data_bp.route('/api/sheets', methods=['POST'])
    @jwt_required()
    def list_excel_sheets():
        data = request.get_json(silent=True) or {}
        return _to_http(data_service.list_excel_sheets(data.get('filename')))

    @data_bp.route('/api/read_columns', methods=['POST'])
    @jwt_required()
    def read_columns_from_file():
        data = request.get_json(silent=True) or {}
        return _to_http(data_service.read_columns_from_file(data.get('filename'), data.get('sheet')))

    @data_bp.route('/api/data', methods=['POST'])
    @jwt_required()
    def get_excel_data_post():
        data = request.get_json(silent=True) or {}
        return _to_http(data_service.get_excel_data_post(data.get('filename')))

    @data_bp.route('/api/data/<path:filename>', methods=['GET'])
    @jwt_required()
    def get_excel_data_get(filename):
        sheet = request.args.get('sheet')
        return _to_http(data_service.get_excel_data_get(filename, sheet))

    @data_bp.route('/api/files', methods=['GET'])
    @jwt_required()
    def list_user_files():
        return _to_http(data_service.list_user_files(get_jwt_identity()))

    @data_bp.route('/api/files/<file_id>/download', methods=['GET'])
    @jwt_required()
    def download_file(file_id):
        return _to_http(data_service.download_file(file_id, get_jwt_identity()))

    @data_bp.route('/api/files/<file_id>', methods=['DELETE'])
    @jwt_required()
    def delete_file(file_id):
        return _to_http(data_service.delete_file(file_id, get_jwt_identity()))

    @data_bp.route('/api/backup', methods=['POST'])
    @jwt_required()
    def manual_backup():
        return _to_http(data_service.manual_backup())

    return data_bp
