from flask import Blueprint, request, jsonify
from src.models.task import Task
from src.config.settings import token_required

tasks_bp = Blueprint('tasks', __name__)

# Crear tarea
@tasks_bp.route('', methods=['POST'])
@token_required
def create_task():
    data = request.get_json()
    task_id = Task.create(
        request.user_id,
        data['title'],
        data.get('description'),
        data.get('due_date'),
        data.get('priority', 'media')
    )
    return jsonify({"id": task_id}), 201

# Listar todas las tareas
@tasks_bp.route('', methods=['GET'])
@token_required
def list_tasks():
    tasks = Task.get_by_user(request.user_id)
    return jsonify(tasks), 200

# Actualizar tarea
@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@token_required
def update_task(task_id):
    data = request.get_json()
    if Task.update(task_id, request.user_id, data):
        return jsonify({"message": "Tarea actualizada"}), 200
    return jsonify({"error": "Tarea no encontrada"}), 404

# Eliminar tarea
@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(task_id):
    if Task.delete(task_id, request.user_id):
        return jsonify({"message": "Tarea eliminada"}), 200
    return jsonify({"error": "Tarea no encontrada"}), 404

# Buscar tareas
@tasks_bp.route('/search', methods=['GET'])
@token_required
def search_tasks():
    query = request.args.get('q', '')
    tasks = Task.search(request.user_id, query)
    return jsonify(tasks), 200

# Marcar como completada
@tasks_bp.route('/<int:task_id>/complete', methods=['PATCH'])
@token_required
def complete_task(task_id):
    if Task.update(task_id, request.user_id, {"status": "completada"}):
        return jsonify({"message": "Tarea completada"}), 200
    return jsonify({"error": "No se pudo actualizar"}), 400