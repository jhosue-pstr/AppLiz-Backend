from flask import Blueprint, request, jsonify
from src.models.chat import Chat, Message
from src.config.settings import token_required
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from src.config.database import Database

chats_bp = Blueprint('chats', __name__)

# Configuración de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp4', 'mp3'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@chats_bp.route('/', methods=['GET'])
@token_required
def get_user_chats():
    """Obtiene todos los chats del usuario"""
    try:
        chats = Chat.get_user_chats(request.user_id)
        return jsonify({
            "success": True,
            "data": chats,
            "count": len(chats)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chats_bp.route('/<int:chat_id>', methods=['GET'])
@token_required
def get_chat_details(chat_id):
    """Obtiene detalles de un chat específico"""
    try:
        chat = Chat.get_chat_details(chat_id)
        if not chat:
            return jsonify({"success": False, "error": "Chat no encontrado"}), 404
            
        participants = Chat.get_participants(chat_id)
        chat['participants'] = participants
        
        return jsonify({
            "success": True,
            "data": chat
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chats_bp.route('/private', methods=['POST'])
@token_required
def create_private_chat():
    """Crea o obtiene un chat privado con otro usuario"""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"success": False, "error": "Se requiere user_id"}), 400
    
    if data['user_id'] == request.user_id:
        return jsonify({"success": False, "error": "No puedes chatear contigo mismo"}), 400
    
    try:
        chat_id = Chat.get_or_create_private_chat(request.user_id, data['user_id'])
        if not chat_id:
            return jsonify({"success": False, "error": "No se pudo crear el chat"}), 500
        
        # Obtener detalles del chat recién creado
        chat = Chat.get_chat_details(chat_id)
        participants = Chat.get_participants(chat_id)
            
        return jsonify({
            "success": True,
            "chat_id": chat_id,
            "chat_name": chat['name'],
            "participants": participants
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@chats_bp.route('/group', methods=['POST'])
@token_required
def create_group_chat():
    """Crea un nuevo grupo"""
    data = request.get_json()
    required_fields = ['name', 'participants']
    if not all(field in data for field in required_fields):
        return jsonify({"success": False, "error": "Faltan campos requeridos"}), 400
    
    if request.user_id not in data['participants']:
        data['participants'].append(request.user_id)
    
    try:
        chat_id = Chat.create(
            name=data['name'],
            is_group=True,
            created_by=request.user_id,
            participants=data['participants']
        )
        
        if not chat_id:
            return jsonify({"success": False, "error": "No se pudo crear el grupo"}), 500
            
        return jsonify({
            "success": True,
            "chat_id": chat_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chats_bp.route('/<int:chat_id>/messages', methods=['GET'])
@token_required
def get_chat_messages(chat_id):
    """Obtiene mensajes de un chat"""
    try:
        before_message_id = request.args.get('before', type=int)
        messages = Message.get_by_chat(chat_id, before_message_id=before_message_id)
        return jsonify({
            "success": True,
            "data": messages
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chats_bp.route('/<int:chat_id>/messages', methods=['POST'])
@token_required
def send_message(chat_id):
    """Envía un mensaje a un chat"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({"success": False, "error": "Se requiere contenido"}), 400

        message_id = Message.create(
            chat_id=chat_id,
            user_id=request.user_id,
            content=data['content'],
            message_type=data.get('message_type', 'text'),
            file_url=data.get('file_url'),
            file_size=data.get('file_size')
        )
        
        if not message_id:
            return jsonify({"success": False, "error": "No se pudo enviar el mensaje"}), 500
            
        return jsonify({
            "success": True,
            "message_id": message_id
        }), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chats_bp.route('/messages/<int:message_id>/read', methods=['POST'])
@token_required
def mark_message_as_read(message_id):
    """Marca un mensaje como leído"""
    try:
        message = Message.get_message(message_id)
        if not message:
            return jsonify({"success": False, "error": "Mensaje no encontrado"}), 404
            
        if message['user_id'] == request.user_id:
            return jsonify({"success": False, "error": "No puedes marcar tus propios mensajes como leídos"}), 400
            
        Message.mark_as_read(message_id, request.user_id)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chats_bp.route('/messages/<int:message_id>', methods=['DELETE'])
@token_required
def delete_message(message_id):
    """Elimina un mensaje"""
    try:
        success = Message.delete(message_id, request.user_id)
        if not success:
            return jsonify({"success": False, "error": "No se pudo eliminar el mensaje"}), 400
            
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@chats_bp.route('/upload', methods=['POST'])
@token_required
def upload_file():
    """Sube un archivo adjunto"""
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No se encontró el archivo"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"success": False, "error": "Nombre de archivo vacío"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        file_url = f"/uploads/{filename}"
        return jsonify({
            "success": True,
            "file_url": file_url,
            "file_name": file.filename,
            "file_size": os.path.getsize(filepath)
        }), 200
        
    return jsonify({"success": False, "error": "Tipo de archivo no permitido"}), 400





@chats_bp.route('/<int:chat_id>/participants', methods=['GET'])
@token_required
def get_chat_participants(chat_id):
    """Obtiene la lista de participantes de un chat"""
    try:
        participants = Chat.get_participants(chat_id)
        return jsonify({
            "success": True,
            "participants": participants
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@chats_bp.route('/<int:chat_id>/participants', methods=['POST'])
@token_required
def add_participant(chat_id):
    """Agrega un nuevo participante a un chat grupal"""
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({"success": False, "error": "user_id requerido"}), 400

    try:
        success = Chat.add_participant(chat_id, data['user_id'], data.get('is_admin', False))
        if success:
            return jsonify({"success": True}), 200
        return jsonify({"success": False, "error": "No se pudo agregar participante"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500



@chats_bp.route('/<int:chat_id>', methods=['DELETE'])
@token_required
def delete_chat(chat_id):
    """Elimina un chat"""
    try:
        success = Chat.delete_chat(chat_id, request.user_id)
        if success:
            return jsonify({"success": True}), 200
        return jsonify({"success": False, "error": "No tienes permisos o el chat no existe"}), 403
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500