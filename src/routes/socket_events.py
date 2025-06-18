from flask_socketio import join_room, leave_room
from src import socketio
from src.models.chat import Message
import requests
import datetime 

@socketio.on('connect')
def handle_connect():
    print('Cliente conectado:', request.sid)

@socketio.on('join_chat')
def handle_join_chat(data):
    chat_id = data['chat_id']
    join_room(f"chat_{chat_id}")
    print(f'Usuario {data["user_id"]} unido al chat {chat_id}')

@socketio.on('send_message')
def handle_send_message(data):
    chat_id = data['chat_id']
    user_id = data['user_id']
    content = data['content']
    
    # Guardar en BD
    message_id = Message.create(chat_id, user_id, content)
    
    # Broadcast a los participantes del chat
    socketio.emit('new_message', {
        'id': message_id,
        'chat_id': chat_id,
        'user_id': user_id,
        'content': content,
        'sent_at': str(datetime.utcnow())
    }, room=f"chat_{chat_id}")