from flask import Blueprint, request, jsonify
from src.config.database import Database
import jwt
import bcrypt
import os
from datetime import datetime, timedelta
import mysql.connector
from src.models.points import PointSystem



auth_bp = Blueprint('auth', __name__)
JWT_SECRET = "1"
JWT_EXPIRATION = timedelta(hours=24)

@auth_bp.route('/register', methods=['POST'])
def register():
    connection = Database.get_connection()
    cursor = connection.cursor(dictionary=True)
    
    try:
        data = request.get_json()

        email = data['email']
        password = data['password']
        name = data['name']
        lastname_paternal = data['lastname_paternal']

        lastname_maternal = data.get('lastname_maternal', None)
        avatar_url = data.get('avatar_url', None)
        bio = data.get('bio', None)
        currently_working = data.get('currently_working', 0)
        working_hours_per_day = data.get('working_hours_per_day', 0)
        stress_frequency = data.get('stress_frequency', 'medio')
        points = data.get('points', 0)
        language = data.get('language', 'es')
        theme = data.get('theme', 'light')

        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"error": "El email ya está registrado"}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        query = """
            INSERT INTO users 
            (email, password_hash, name, lastname_paternal, lastname_maternal, avatar_url, bio, 
            currently_working, working_hours_per_day, stress_frequency, points, language, theme, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        cursor.execute(query, (
            email, hashed_password, name, lastname_paternal, lastname_maternal, avatar_url, bio,
            currently_working, working_hours_per_day, stress_frequency, points, language, theme
        ))
        connection.commit()

        # Generar token JWT
        user_id = cursor.lastrowid
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + JWT_EXPIRATION
        }, JWT_SECRET, algorithm='HS256')

        return jsonify({"token": token, "user_id": user_id}), 201

    except mysql.connector.Error as err:
        return jsonify({"error": str(err)}), 500
    finally:
        Database.close_connection(connection, cursor)

@auth_bp.route('/login', methods=['POST'])
def login():
    connection = Database.get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        data = request.get_json()
        email = data['email']
        password = data['password']

        cursor.execute("""
            SELECT id, email, name, lastname_paternal, lastname_maternal,
                   avatar_url, bio, currently_working, working_hours_per_day,
                   stress_frequency, points, language, theme, password_hash, last_login
            FROM users WHERE email = %s
        """, (email,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            today = datetime.now().date()
            last_login = user['last_login'].date() if user['last_login'] else None
            
            points_to_add = 0
            if last_login != today:
                points_to_add = 3  # Dar 3 puntos por primer login del día
                cursor.execute("UPDATE users SET points = points + %s, last_login = NOW() WHERE id = %s", 
                             (points_to_add, user['id']))
                connection.commit()
                user['points'] += points_to_add  

            token = jwt.encode({
                'user_id': user['id'],
                'exp': datetime.utcnow() + JWT_EXPIRATION
            }, JWT_SECRET, algorithm='HS256')

            return jsonify({
    'token': token,
    'user_id': user['id'],
    'email': user['email'],
    'name': user['name'],
    'lastname_paternal': user['lastname_paternal'],
    'lastname_maternal': user['lastname_maternal'],
    'avatar_url': user['avatar_url'] if user['avatar_url'] else "assets/images/avatar1.png",
    'bio': user['bio'],
    'currently_working': user['currently_working'],
    'working_hours_per_day': user['working_hours_per_day'],
    'stress_frequency': user['stress_frequency'],
    'points': user['points'],
    'language': user['language'],
    'theme': user['theme'],
    'daily_points_added': points_to_add
}), 200

        else:
            return jsonify({'error': 'Credenciales inválidas'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        Database.close_connection(connection, cursor)