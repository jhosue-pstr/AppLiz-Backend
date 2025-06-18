from flask import Blueprint, request, jsonify
from src.models.note import Note
from src.config.settings import token_required

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('', methods=['POST'])
@token_required
def create_note():
    try:
        data = request.get_json()
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({"error": "Título y contenido son requeridos"}), 400
            
        note_id = Note.create(
            request.user_id,
            data['title'],
            data['content'],
            data.get('color', '#FFFFFF'),
            data.get('pinned', False)
        )
        return jsonify({
            "id": note_id,
            "message": "Nota creada exitosamente"
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notes_bp.route('', methods=['GET'])
@token_required
def list_notes():
    try:
        notes = Note.get_by_user(request.user_id)
        return jsonify({
            "success": True,
            "count": len(notes),
            "notes": notes
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Error al obtener las notas",
            "details": str(e)
        }), 500

@notes_bp.route('/<int:note_id>', methods=['PUT'])
@token_required
def update_note(note_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos de actualización requeridos"}), 400
            
        if Note.update(note_id, request.user_id, data):
            return jsonify({"message": "Nota actualizada exitosamente"}), 200
        return jsonify({"error": "Nota no encontrada o no pertenece al usuario"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notes_bp.route('/<int:note_id>', methods=['DELETE'])
@token_required
def delete_note(note_id):
    try:
        if Note.delete(note_id, request.user_id):
            return jsonify({"message": "Nota eliminada exitosamente"}), 200
        return jsonify({"error": "Nota no encontrada o no pertenece al usuario"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@notes_bp.route('/search', methods=['GET'])
@token_required
def search_notes():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Parámetro de búsqueda 'q' requerido"}), 400
            
        notes = Note.search(request.user_id, query)
        return jsonify({
            "success": True,
            "count": len(notes),
            "results": notes
        }), 200
    except Exception as e:
        return jsonify({
            "error": "Error en la búsqueda",
            "details": str(e)
        }), 500