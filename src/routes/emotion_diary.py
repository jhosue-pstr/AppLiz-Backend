from flask import Blueprint, request, jsonify
from src.config.settings import token_required
from src.models.EmotionDiary import EmotionDiary
from datetime import datetime
from src.config.database import Database

emotion_bp = Blueprint('emotion', __name__)

@emotion_bp.errorhandler(400)
def handle_bad_request(error):
    return jsonify({
        "success": False,
        "error": "Bad Request",
        "message": str(error)
    }), 400

@emotion_bp.errorhandler(500)
def handle_server_error(error):
    return jsonify({
        "success": False,
        "error": "Internal Server Error",
        "message": "Ocurrió un error inesperado"
    }), 500

@emotion_bp.route('/entries', methods=['POST'])
@token_required
def log_emotion():
    """Registra una nueva entrada emocional"""
    data = request.get_json()
    
    required_fields = ['emotion', 'intensity']
    if not all(field in data for field in required_fields):
        return jsonify({
            "success": False,
            "error": "Missing required fields",
            "required": required_fields
        }), 400

    try:
        intensity = int(data['intensity'])
        if intensity < 1 or intensity > 5:
            raise ValueError("Intensity must be between 1 and 5")
            
        entry_id = EmotionDiary.log_emotion(
            user_id=request.user_id,
            emotion=data['emotion'],
            intensity=intensity,
            content=data.get('content', ''),
            tags=data.get('tags')
        )
        
        return jsonify({
            "success": True,
            "data": {
                "entry_id": entry_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "error": "Validation Error",
            "message": str(e)
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Database Error",
            "message": str(e)
        }), 500

@emotion_bp.route('/entries', methods=['GET'])
@token_required
def get_entries():
    """Obtiene el historial de entradas emocionales"""
    try:
        days = min(int(request.args.get('days', 30)), 365)  # Limit to 1 year max
        page = max(int(request.args.get('page', 1)), 1)
        per_page = min(max(int(request.args.get('per_page', 10)), 1), 100)  # Limit 100 per page
        
        history = EmotionDiary.get_emotional_history(
            user_id=request.user_id,
            days=days
        )
        
        # Implementación básica de paginación
        start_idx = (page - 1) * per_page
        paginated_data = history[start_idx:start_idx + per_page]
        
        return jsonify({
            "success": True,
            "data": paginated_data,
            "pagination": {
                "total_entries": len(history),
                "page": page,
                "per_page": per_page,
                "total_pages": (len(history) + per_page - 1) // per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Server Error",
            "message": str(e)
        }), 500

@emotion_bp.route('/stats', methods=['GET'])
@token_required
def get_emotional_stats():
    """Obtiene estadísticas emocionales"""
    try:
        # Obtener datos crudos
        stats = EmotionDiary.get_emotional_stats(request.user_id)
        weekly_data = EmotionDiary.get_weekly_summary(request.user_id)
        patterns = EmotionDiary.detect_patterns(request.user_id)
        
        # Procesar estadísticas
        emotion_counts = {}
        total_intensity = 0
        for entry in stats:
            emotion = entry['emotion']
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
            total_intensity += entry['avg_intensity']
        
        avg_intensity = total_intensity / len(stats) if stats else 0
        
        return jsonify({
            "success": True,
            "data": {
                "emotion_distribution": emotion_counts,
                "average_intensity": round(avg_intensity, 2),
                "weekly_summary": weekly_data,
                "patterns": patterns
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Server Error",
            "message": str(e)
        }), 500

@emotion_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@token_required
def delete_entry(entry_id):
    """Elimina una entrada específica del diario emocional
    
    Verifica que la entrada pertenezca al usuario antes de eliminarla
    """
    connection = None
    cursor = None
    
    try:
        # 1. Obtener conexión a la base de datos
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        
        # 2. Verificar que la entrada pertenece al usuario
        cursor.execute(
            """SELECT user_id FROM diary_entries 
            WHERE id = %s""",
            (entry_id,)
        )
        entry = cursor.fetchone()
        
        if not entry:
            return jsonify({
                "success": False,
                "error": "Not Found",
                "message": "La entrada no existe"
            }), 404
            
        if entry['user_id'] != request.user_id:
            return jsonify({
                "success": False,
                "error": "Forbidden",
                "message": "No tienes permiso para eliminar esta entrada"
            }), 403
            
        # 3. Eliminar la entrada
        cursor.execute(
            """DELETE FROM diary_entries 
            WHERE id = %s AND user_id = %s""",
            (entry_id, request.user_id)
        )
        
        if cursor.rowcount == 0:
            return jsonify({
                "success": False,
                "error": "Delete Failed",
                "message": "No se pudo eliminar la entrada"
            }), 500
            
        connection.commit()
        
        # 4. Registrar la acción (opcional)
        cursor.execute(
            """INSERT INTO diary_deletion_log 
            (user_id, entry_id, deleted_at) 
            VALUES (%s, %s, NOW())""",
            (request.user_id, entry_id)
        )
        connection.commit()
        
        return jsonify({
            "success": True,
            "data": {
                "entry_id": entry_id,
                "deleted_at": datetime.utcnow().isoformat()
            },
            "message": "Entrada eliminada exitosamente"
        }), 200
        
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({
            "success": False,
            "error": "Server Error",
            "message": str(e)
        }), 500
        
    finally:
        if cursor:
            cursor.close()
        if connection:
            Database.close_connection(connection)

@emotion_bp.route('/patterns', methods=['GET'])
@token_required
def get_emotional_patterns():
    """Obtiene patrones emocionales detectados"""
    try:
        patterns = EmotionDiary.detect_patterns(request.user_id)
        return jsonify({
            "success": True,
            "data": patterns
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": "Server Error",
            "message": str(e)
        }), 500            