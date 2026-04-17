from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from service import analysis_service


def create_analysis_blueprint():
    analysis_bp = Blueprint("analysis", __name__)

    def to_http(result):
        if isinstance(result, tuple) and len(result) == 2:
            payload, status = result
        else:
            payload, status = result, 200
        return jsonify(payload), status

    @analysis_bp.route('/api/column_stats', methods=['POST'])
    @jwt_required()
    def column_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.column_stats(data))

    @analysis_bp.route('/api/multi_subject_stats', methods=['POST'])
    @jwt_required()
    def multi_subject_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.multi_subject_stats(data))

    @analysis_bp.route('/api/yearly_admission_stats', methods=['POST'])
    @jwt_required()
    def yearly_admission_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.yearly_admission_stats(data))

    @analysis_bp.route('/api/school_source_stats', methods=['POST'])
    @jwt_required()
    def school_source_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.school_source_stats(data))

    @analysis_bp.route('/api/admission_method_stats', methods=['POST'])
    @jwt_required()
    def admission_method_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.admission_method_stats(data))

    @analysis_bp.route('/api/geographic_stats', methods=['POST'])
    @jwt_required()
    def geographic_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.geographic_stats(data))

    @analysis_bp.route('/api/top_schools_stats', methods=['POST'])
    @jwt_required()
    def top_schools_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.top_schools_stats(data))

    @analysis_bp.route('/api/subject_average_stats', methods=['POST'])
    @jwt_required()
    def subject_average_stats():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.subject_average_stats(data))

    @analysis_bp.route('/api/analysis/gender-subject', methods=['POST'])
    @jwt_required()
    def gender_subject_analysis():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.gender_subject_analysis(data))

    @analysis_bp.route('/api/analysis/admission-subject', methods=['POST'])
    @jwt_required()
    def admission_subject_analysis():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.admission_subject_analysis(data))

    @analysis_bp.route('/api/analysis/school-type-subject', methods=['POST'])
    @jwt_required()
    def school_type_subject_analysis():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.school_type_subject_analysis(data))

    @analysis_bp.route('/api/analysis/region-subject', methods=['POST'])
    @jwt_required()
    def region_subject_analysis():
        data = request.get_json(silent=True) or {}
        return to_http(analysis_service.region_subject_analysis(data))

    return analysis_bp
