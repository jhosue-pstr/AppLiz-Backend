import os
import jwt
from datetime import timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_socketio import SocketIO

# Configuración Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'tu_clave_secreta_aleatoria')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'tu_clave_jwt_secreta')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=1440)

# Configuración SocketIO
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True)

# Decorador JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Token no proporcionado o formato inválido"}), 401
            
        try:
            token = auth_header.split()[1]
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            request.user_id = payload['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expirado"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido"}), 401
        except Exception as e:
            return jsonify({"error": f"Error de autenticación: {str(e)}"}), 401
            
        return f(*args, **kwargs)
    return decorated

# Configuración CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

# Importar blueprints
from src.routes.auth import auth_bp
from src.routes.users import users_bp
from src.routes.chat import chats_bp

# Registrar blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(chats_bp, url_prefix='/api/chats')

# Importar y registrar namespaces de SocketIO
from src.sockets.chat import ChatNamespace
socketio.on_namespace(ChatNamespace('/chat'))

# Ruta de estado
@app.route('/api/status')
def status_check():
    return jsonify({
        "status": "active",
        "message": "Servidor funcionando correctamente",
        "socketio": "running"
    })

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # En producción, sin debug ni recarga automática
    socketio.run(app, host='0.0.0.0', port=5000)
