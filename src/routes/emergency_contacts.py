from flask import Blueprint, request, jsonify
from src.models.emergency_contact import EmergencyContact
from src.config.settings import token_required

contacts_bp = Blueprint('emergency_contacts', __name__)

# Crear contacto (solo admin)
@contacts_bp.route('', methods=['POST'])
@token_required
def create_contact():
    data = request.get_json()
    contact_id = EmergencyContact.create(
        data['name'],
        data['phone'],
        data.get('description', ''),
        data['category']
    )
    return jsonify({"id": contact_id}), 201

# Listar todos (público o con token)
@contacts_bp.route('', methods=['GET'])
@token_required
def list_contacts():
    contacts = EmergencyContact.get_all()
    return jsonify(contacts), 200

# Obtener por ID
@contacts_bp.route('/<int:contact_id>', methods=['GET'])
@token_required
def get_contact(contact_id):
    contact = EmergencyContact.get_by_id(contact_id)
    if contact:
        return jsonify(contact), 200
    return jsonify({"error": "Contacto no encontrado"}), 404

# Actualizar (solo admin)
@contacts_bp.route('/<int:contact_id>', methods=['PUT'])
@token_required
def update_contact(contact_id):
    data = request.get_json()
    if EmergencyContact.update(
        contact_id,
        data['name'],
        data['phone'],
        data.get('description', ''),
        data['category']
    ):
        return jsonify({"message": "Contacto actualizado"}), 200
    return jsonify({"error": "Contacto no encontrado"}), 404

# Eliminar (solo admin)
@contacts_bp.route('/<int:contact_id>', methods=['DELETE'])
@token_required
def delete_contact(contact_id):
    if EmergencyContact.delete(contact_id):
        return jsonify({"message": "Contacto eliminado"}), 200
    return jsonify({"error": "Contacto no encontrado"}), 404