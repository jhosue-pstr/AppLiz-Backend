from flask_socketio import Namespace
from src.models.chat import Chat, Message
from datetime import datetime

class ChatNamespace(Namespace):
    def on_connect(self):
        print('Cliente conectado')

    def on_disconnect(self):
        print('Cliente desconectado')

    def on_join_chat(self, data):
        chat_id = data['chat_id']
        self.enter_room(str(chat_id))
        self.emit('user_joined', {
            'user_id': data['user_id'],
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat()
        }, room=str(chat_id), skip_sid=self.request.sid)

    def on_leave_chat(self, data):
        chat_id = data['chat_id']
        self.leave_room(str(chat_id))
        self.emit('user_left', {
            'user_id': data['user_id'],
            'chat_id': chat_id,
            'timestamp': datetime.now().isoformat()
        }, room=str(chat_id))

    def on_typing(self, data):
        self.emit('typing_indicator', {
            'chat_id': data['chat_id'],
            'user_id': data['user_id'],
            'is_typing': data['is_typing']
        }, room=str(data['chat_id']), skip_sid=self.request.sid)

    def on_mark_as_read(self, data):
        Message.mark_as_read(data['message_id'], data['user_id'])
        self.emit('message_read', {
            'message_id': data['message_id'],
            'chat_id': data['chat_id'],
            'user_id': data['user_id']
        }, room=str(data['chat_id']))

    def on_new_message(self, data):
        message_id = Message.create(
            chat_id=data['chat_id'],
            user_id=data['user_id'],
            content=data['content'],
            message_type=data.get('message_type', 'text'),
            file_url=data.get('file_url'),
            file_size=data.get('file_size')
        )
        
        if message_id:
            message = Message.get_message(message_id)
            if message:
                self.emit('new_message', {
                    'chat_id': data['chat_id'],
                    'message': message
                }, room=str(data['chat_id']))