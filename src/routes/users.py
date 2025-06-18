from flask import Blueprint, request, jsonify
from src.models.user import User
from src.config.settings import token_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/me', methods=['GET'])
@token_required
def get_profile():
    user = User.get_by_id(request.user_id)
    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404
    return jsonify(user), 200

@users_bp.route('/me', methods=['PATCH'])
@token_required
def update_profile():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Datos requeridos"}), 400
    
    try:
        allowed_fields = ['name',
            'lastname_paternal',
            'lastname_maternal',
            'avatar_url',
            'bio',
            'currently_working',
            'working_hours_per_day',
            'stress_frequency']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return jsonify({"error": "Ningún campo válido para actualizar"}), 400
        
        if User.update(request.user_id, update_data):
            return jsonify({"message": "Perfil actualizado"}), 200
        return jsonify({"error": "No se pudo actualizar"}), 400
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@users_bp.route('/me', methods=['DELETE'])
@token_required
def delete_profile():
    try:
        if User.delete(request.user_id):
            return jsonify({"message": "Cuenta eliminada"}), 200
        return jsonify({"error": "No se pudo eliminar"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@users_bp.route('/me/password', methods=['PUT'])
@token_required
def update_password():
    data = request.get_json()
    required_fields = ['current_password', 'new_password']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Contraseña actual y nueva requeridas"}), 400
    
    try:
        if not User.verify_password(request.user_id, data['current_password']):
            return jsonify({"error": "Contraseña actual incorrecta"}), 401
        
        if User.update_password(request.user_id, data['new_password']):
            return jsonify({"message": "Contraseña actualizada"}), 200
        return jsonify({"error": "Error al actualizar"}), 500
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
