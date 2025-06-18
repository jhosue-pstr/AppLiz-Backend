from flask import Blueprint, request, jsonify
from src.models.event import Event
from src.config.settings import token_required

events_bp = Blueprint('events', __name__)

@events_bp.route('', methods=['POST'])
@token_required
def create_event():
    data = request.get_json()
    event_id = Event.create(
        request.user_id,
        data['title'],
        data['description'],
        data['start_datetime'],  
        data.get('end_datetime'),  
        data.get('location')
    )
    return jsonify({"id": event_id}), 201

@events_bp.route('', methods=['GET'])
@token_required
def list_events():
    events = Event.get_by_user(request.user_id)
    return jsonify(events), 200

@events_bp.route('/<int:event_id>', methods=['PUT'])
@token_required
def update_event(event_id):
    data = request.get_json()
    if Event.update(event_id, request.user_id, data):
        return jsonify({"message": "Evento actualizado"}), 200
    return jsonify({"error": "Evento no encontrado"}), 404

@events_bp.route('/<int:event_id>', methods=['DELETE'])
@token_required
def delete_event(event_id):
    if Event.delete(event_id, request.user_id):
        return jsonify({"message": "Evento eliminado"}), 200
    return jsonify({"error": "Evento no encontrado"}), 404

@events_bp.route('/upcoming', methods=['GET'])
@token_required
def upcoming_events():
    limit = request.args.get('limit', default=5, type=int)
    events = Event.get_upcoming(request.user_id, limit)
    return jsonify(events), 200