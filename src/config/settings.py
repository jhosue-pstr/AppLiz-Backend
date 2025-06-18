import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import os

# Configuración (en producción usa variables de entorno)
JWT_SECRET = os.getenv('JWT_SECRET', '1')  # ¡Cambia esto!
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_HOURS = 24

def generate_token(user_id):
    """Genera un nuevo token JWT"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token):
    """Decodifica y verifica un token JWT"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expirado
    except jwt.InvalidTokenError:
        return None  # Token inválido

def token_required(f):
    """Decorador para proteger endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Obtener token del header 'Authorization'
        if 'Authorization' in request.headers:
            parts = request.headers['Authorization'].split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            return jsonify({"error": "Token faltante"}), 401
        
        payload = decode_token(token)
        if not payload:
            return jsonify({"error": "Token inválido o expirado"}), 401
        
        # Añade el user_id al contexto de la solicitud
        request.user_id = payload['user_id']
        return f(*args, **kwargs)
    
    return decorated




# Configuración de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp4'}

# Configuración de WebSocket
SOCKETIO_MESSAGE_QUEUE = 'redis://localhost:6379/0'  # Para producción con múltiples workers