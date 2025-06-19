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
    data = request.get_json()
    points_to_subtract = data['points']
    
    # Llama directamente al método para restar puntos
    success = PointSystem.subtract_points(request.user_id, points_to_subtract)
    
    if success:
        return jsonify({"message": "Puntos restados correctamente", "new_balance": PointSystem.get_balance(request.user_id)}), 200
    return jsonify({"error": "No tienes suficientes puntos"}), 400