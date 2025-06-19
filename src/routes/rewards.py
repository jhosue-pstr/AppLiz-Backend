from flask import Blueprint, request, jsonify
from src.models.points import PointSystem, RewardSystem
from src.config.settings import token_required

rewards_bp = Blueprint('rewards', __name__)

@rewards_bp.route('/balance', methods=['GET'])
@token_required
def get_balance():
    balance = PointSystem.get_balance(request.user_id)
    return jsonify({"balance": balance}), 200

@rewards_bp.route('/rewards', methods=['GET'])
@token_required
def list_rewards():
    rewards = RewardSystem.get_available_rewards()
    return jsonify(rewards), 200

@rewards_bp.route('/redeem', methods=['POST'])
@token_required
def redeem_reward():
    data = request.get_json()
    success = RewardSystem.redeem_reward(
        request.user_id,
        data['reward_id']
    )
    if success:
        return jsonify({"message": "Recompensa canjeada"}), 200
    return jsonify({"error": "Puntos insuficientes o recompensa no disponible"}), 400




@rewards_bp.route('/subtract-points', methods=['POST'])
@token_required
def subtract_points():
    try:
        data = request.get_json()
        
        # Validar entrada
        if not data or 'points' not in data or not isinstance(data['points'], int):
            return jsonify({"error": "El campo 'points' (entero) es requerido"}), 400

        points_to_subtract = data['points']
        
        # Restar puntos
        success = PointSystem.subtract_points(request.user_id, points_to_subtract)
        
        if success:
            new_balance = PointSystem.get_balance(request.user_id)
            return jsonify({
                "message": "Puntos restados correctamente",
                "new_balance": new_balance
            }), 200
        else:
            return jsonify({
                "error": "No tienes suficientes puntos o no existe registro en la base de datos"
            }), 400

    except Exception as e:
        print(f"Error en subtract_points endpoint: {str(e)}")  # Log en Railway
        return jsonify({"error": "Error interno del servidor"}), 500