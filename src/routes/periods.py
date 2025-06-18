from flask import Blueprint, request, jsonify
from src.models.period import Period
from src.config.settings import token_required

period_bp = Blueprint('period', __name__)

@period_bp.route('/close', methods=['POST'])
@token_required
def close_period():
    data = request.get_json()
    required_fields = ['name', 'start_date', 'end_date']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    if Period.close_period(
        request.user_id,
        data['name'],
        data['start_date'],
        data['end_date'],
        data.get('summary')
    ):
        return jsonify({"message": "Período cerrado exitosamente"}), 200
    return jsonify({"error": "No se pudo cerrar el periodo"}), 400

@period_bp.route('/history', methods=['GET'])
@token_required
def get_period_history():
    try:
        periods = Period.get_closed_periods()
        if not periods:
            return jsonify({"message": "No hay periodos cerrados", "data": []}), 200
        return jsonify({"data": periods}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500