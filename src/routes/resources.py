from flask import Blueprint, request, jsonify
from src.models.resource import Resource
from src.config.settings import token_required

resources_bp = Blueprint('resources', __name__)

# Crear recurso (admin)
@resources_bp.route('', methods=['POST'])
@token_required
def create_resource():
    data = request.get_json()
    resource_id = Resource.create(
        data['title'],
        data['url'],
        data['type'],
        data.get('description')
    )
    return jsonify({"id": resource_id}), 201

# Listar recursos (público o con token)
@resources_bp.route('', methods=['GET'])
@token_required
def list_resources():
    resource_type = request.args.get('type')
    resources = Resource.get_all(resource_type)
    return jsonify(resources), 200

# Obtener por ID
@resources_bp.route('/<int:resource_id>', methods=['GET'])
@token_required
def get_resource(resource_id):
    resource = Resource.get_by_id(resource_id)
    if resource:
        return jsonify(resource), 200
    return jsonify({"error": "Recurso no encontrado"}), 404

# Actualizar recurso (admin)
@resources_bp.route('/<int:resource_id>', methods=['PUT'])
@token_required
def update_resource(resource_id):
    data = request.get_json()
    if Resource.update(
        resource_id,
        data['title'],
        data['url'],
        data['type'],
        data.get('description')
    ):
        return jsonify({"message": "Recurso actualizado"}), 200
    return jsonify({"error": "Recurso no encontrado"}), 404

# Eliminar recurso (admin)
@resources_bp.route('/<int:resource_id>', methods=['DELETE'])
@token_required
def delete_resource(resource_id):
    if Resource.delete(resource_id):
        return jsonify({"message": "Recurso eliminado"}), 200
    return jsonify({"error": "Recurso no encontrado"}), 404