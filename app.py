import os
import jwt
import requests
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_socketio import SocketIO

# Configuración Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET', 'tu_clave_secreta')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', '1')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=1440)

# Configuración SocketIO
socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    async_mode='eventlet',
                    logger=True,
                    engineio_logger=True)

# Crear carpeta de uploads si no existe
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, PATCH, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Importar blueprints
from src.routes.auth import auth_bp
from src.routes.users import users_bp
from src.routes.emotion_diary import emotion_bp
from src.routes.notes import notes_bp
from src.routes.tasks import tasks_bp
from src.routes.events import events_bp
from src.routes.periods import period_bp
from src.routes.emergency_contacts import contacts_bp
from src.routes.resources import resources_bp
from src.routes.chat import chats_bp
from src.routes.rewards import rewards_bp
# Registrar todos los blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(emotion_bp, url_prefix='/api/emotion')
app.register_blueprint(notes_bp, url_prefix='/api/notes')
app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
app.register_blueprint(events_bp, url_prefix='/api/events')
app.register_blueprint(period_bp, url_prefix='/api/period')
app.register_blueprint(contacts_bp, url_prefix='/api/emergency-contacts')
app.register_blueprint(resources_bp, url_prefix='/api/resources')
app.register_blueprint(chats_bp, url_prefix='/api/chats')
app.register_blueprint(rewards_bp, url_prefix='/api/rewards')
# Importar y registrar namespaces de SocketIO
from src.sockets.chat import ChatNamespace
socketio.on_namespace(ChatNamespace('/chat'))

# Ruta de prueba
@app.route('/')
def home():
    return jsonify({
        "message": "¡Bienvenido a Uni-Pulse API!",
        "status": "operativo",
        "version": "1.0",
        "endpoints": {
            "auth": "/api/auth",
            "users": "/api/users",
            "chats": "/api/chats",
            "emotions": "/api/emotion",
            "notes": "/api/notes",
            "tasks": "/api/tasks",
            "events": "/api/events",
            "periods": "/api/period",
            "contacts": "/api/emergency-contacts",
            "resources": "/api/resources"
        }
    })

# Ruta de status
@app.route('/api/status')
def status_check():
    return jsonify({
        "status": "active",
        "message": "Servidor funcionando correctamente",
        "socketio": "running"
    })

# ➕ RUTA INTEGRADA: Obtener empleos desde Adzuna API
@app.route('/api/jobs/adzuna', methods=['GET'])
def get_adzuna_jobs():
    query = request.args.get('q', '')
    location = request.args.get('loc', '')

    countries = ['br', 'ar', 'mx', 'cl', 'co']  # Países LATAM soportados

    app_id = 'd7c74245'
    app_key = 'ee7940b64c32d867305cc0c7395a514c'

    all_jobs = []

    for country in countries:
        url = f'https://api.adzuna.com/v1/api/jobs/{country}/search/1'
        params = {
            'app_id': app_id,
            'app_key': app_key,
            'results_per_page': 20,
            'content-type': 'application/json'
        }
        if query:
            params['what'] = query
        if location:
            params['where'] = location

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            jobs = [
                {
                    'title': job.get('title', ''),
                    'company': job.get('company', {}).get('display_name', ''),
                    'location': job.get('location', {}).get('display_name', ''),
                    'link': job.get('redirect_url', ''),
                    'country': country.upper()
                }
                for job in data.get('results', [])
            ]
            all_jobs.extend(jobs)
        except requests.RequestException as e:
            print(f'Error al conectar con Adzuna para {country}:', str(e))
            continue

    return jsonify(all_jobs)

# Manejo de errores global
@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Solicitud incorrecta", "details": str(error)}), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({"error": "No autorizado"}), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

# Ejecutar servidor
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Usa el puerto de Railway o 5000 local
    print(f"🔧 Servidor iniciando en http://0.0.0.0:{port}")
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,  # ¡Importante! Usa la variable PORT
        debug=False,  # En producción, debug debe ser False
        use_reloader=False  # Desactiva el reloader en producción
    )