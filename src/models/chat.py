from datetime import datetime
from src.config.database import Database

class Chat:
    @staticmethod
    def create(name, is_group, created_by, theme=None, photo_url=None, participants=None):
        """Crea un nuevo chat (individual o grupal)"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            # Insertar el chat principal
            cursor.execute(
                """INSERT INTO chats 
                (name, is_group, theme, created_by, photo_url, created_at, last_message_at) 
                VALUES (%s, %s, %s, %s, %s, NOW(), NOW())""",
                (name, is_group, theme, created_by, photo_url)
            )
            
            chat_id = cursor.lastrowid
            
            # Añadir al creador como participante
            cursor.execute(
                """INSERT INTO chat_participants 
                (chat_id, user_id, is_admin, joined_at, status) 
                VALUES (%s, %s, %s, NOW(), 'active')""",
                (chat_id, created_by, True)
            )
            
            # Añadir otros participantes si es un grupo
            if is_group and participants:
                for user_id in participants:
                    if user_id != created_by:
                        cursor.execute(
                            """INSERT INTO chat_participants 
                            (chat_id, user_id, is_admin, joined_at, status) 
                            VALUES (%s, %s, %s, NOW(), 'active')""",
                            (chat_id, user_id, False)
                        )
            
            connection.commit()
            return chat_id
        except Exception as e:
            connection.rollback()
            print(f"Error en Chat.create(): {str(e)}")
            return 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_or_create_private_chat(user1_id, user2_id):
        """Obtiene o crea un chat privado entre dos usuarios"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            # Buscar si ya existe un chat privado entre estos usuarios
            cursor.execute("""
                SELECT c.id 
                FROM chats c
                JOIN chat_participants cp1 ON c.id = cp1.chat_id AND cp1.user_id = %s
                JOIN chat_participants cp2 ON c.id = cp2.chat_id AND cp2.user_id = %s
                WHERE c.is_group = 0
                LIMIT 1
            """, (user1_id, user2_id))
            
            existing_chat = cursor.fetchone()
            
            if existing_chat:
                return existing_chat['id']
            
            # Si no existe, crear uno nuevo
            chat_name = f"Chat privado {user1_id}-{user2_id}"
            cursor.execute(
                """INSERT INTO chats 
                (name, is_group, created_by, created_at, last_message_at) 
                VALUES (%s, 0, %s, NOW(), NOW())""",
                (chat_name, user1_id)
            )
            
            chat_id = cursor.lastrowid
            
            # Añadir ambos participantes
            for user_id in [user1_id, user2_id]:
                cursor.execute(
                    """INSERT INTO chat_participants 
                    (chat_id, user_id, is_admin, joined_at, status) 
                    VALUES (%s, %s, %s, NOW(), 'active')""",
                    (chat_id, user_id, False)
                )
            
            connection.commit()
            return chat_id
        except Exception as e:
            connection.rollback()
            print(f"Error en Chat.get_or_create_private_chat(): {str(e)}")
            return 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_user_chats(user_id):
        """Obtiene todos los chats del usuario"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT 
                    c.id,
                    c.name,
                    c.is_group,
                    c.theme,
                    c.photo_url,
                    c.last_message_at,
                    (SELECT COUNT(*) FROM messages m 
                     WHERE m.chat_id = c.id AND m.read_at IS NULL AND m.user_id != %s) as unread_count,
                    (SELECT content FROM messages 
                     WHERE chat_id = c.id AND deleted_at IS NULL 
                     ORDER BY sent_at DESC LIMIT 1) as last_message_content,
                    (SELECT u.name FROM messages 
                     JOIN users u ON messages.user_id = u.id 
                     WHERE chat_id = c.id AND deleted_at IS NULL 
                     ORDER BY sent_at DESC LIMIT 1) as last_message_sender
                FROM chats c
                JOIN chat_participants cp ON c.id = cp.chat_id
                WHERE cp.user_id = %s AND cp.left_at IS NULL
                ORDER BY c.last_message_at DESC""",
                (user_id, user_id)
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en Chat.get_user_chats(): {str(e)}")
            return []
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_chat_details(chat_id):
        """Obtiene detalles de un chat específico"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT 
                    c.id, c.name, c.is_group, c.theme, c.photo_url, 
                    c.created_at, c.created_by, u.name as created_by_name
                FROM chats c
                JOIN users u ON c.created_by = u.id
                WHERE c.id = %s""",
                (chat_id,)
            )
            chat = cursor.fetchone()
            
            if not chat:
                return None
                
            return chat
        except Exception as e:
            print(f"Error en Chat.get_chat_details(): {str(e)}")
            return None
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def add_participant(chat_id, user_id, is_admin=False):
        """Añade un participante a un chat"""
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO chat_participants 
                (chat_id, user_id, is_admin, joined_at, status) 
                VALUES (%s, %s, %s, NOW(), 'active')
                ON DUPLICATE KEY UPDATE left_at = NULL, status = 'active'""",
                (chat_id, user_id, is_admin)
            )
            connection.commit()
            return True
        except Exception as e:
            connection.rollback()
            print(f"Error en Chat.add_participant(): {str(e)}")
            return False
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_participants(chat_id):
        """Obtiene participantes de un chat"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT 
                    u.id, u.name, u.avatar_url, cp.is_admin, 
                    cp.joined_at, cp.status
                FROM users u
                JOIN chat_participants cp ON u.id = cp.user_id
                WHERE cp.chat_id = %s AND cp.left_at IS NULL""",
                (chat_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"Error en Chat.get_participants(): {str(e)}")
            return []
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def update_last_message(chat_id):
        """Actualiza la última fecha de mensaje en un chat"""
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """UPDATE chats 
                SET last_message_at = NOW() 
                WHERE id = %s""",
                (chat_id,)
            )
            connection.commit()
        except Exception as e:
            print(f"Error en Chat.update_last_message(): {str(e)}")
            connection.rollback()
        finally:
            Database.close_connection(connection, cursor)


class Message:
    @staticmethod
    def create(chat_id, user_id, content, message_type='text', file_url=None, file_size=None):
        """Crea un nuevo mensaje"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """INSERT INTO messages 
                (chat_id, user_id, content, message_type, file_url, file_size, sent_at, status) 
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), 'sent')""",
                (chat_id, user_id, content, message_type, file_url, file_size)
            )
            
            Chat.update_last_message(chat_id)
            
            message_id = cursor.lastrowid
            connection.commit()
            return message_id
        except Exception as e:
            connection.rollback()
            print(f"Error en Message.create(): {str(e)}")
            return 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_by_chat(chat_id, limit=50, before_message_id=None):
        """Obtiene mensajes de un chat"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            query = """SELECT 
                      m.id, m.chat_id, m.user_id, m.content, m.message_type, 
                      m.file_url, m.file_size, m.sent_at, m.read_at, 
                      m.status as message_status, u.name as user_name, 
                      u.avatar_url as user_avatar
                      FROM messages m
                      JOIN users u ON m.user_id = u.id
                      WHERE m.chat_id = %s AND m.deleted_at IS NULL"""
            
            params = [chat_id]
            
            if before_message_id:
                query += " AND m.id < %s"
                params.append(before_message_id)
            
            query += " ORDER BY m.sent_at DESC LIMIT %s"
            params.append(limit)
            
            cursor.execute(query, params)
            messages = cursor.fetchall()
            return list(reversed(messages))
        except Exception as e:
            print(f"Error en Message.get_by_chat(): {str(e)}")
            return []
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_message(message_id):
        """Obtiene un mensaje específico"""
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT m.*, u.name as user_name, u.avatar_url as user_avatar
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.id = %s AND m.deleted_at IS NULL""",
                (message_id,)
            )
            return cursor.fetchone()
        except Exception as e:
            print(f"Error en Message.get_message(): {str(e)}")
            return None
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def mark_as_read(message_id, user_id):
        """Marca un mensaje como leído"""
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """UPDATE messages 
                SET read_at = NOW(), status = 'read' 
                WHERE id = %s AND user_id != %s AND read_at IS NULL""",
                (message_id, user_id)
            )
            connection.commit()
        except Exception as e:
            print(f"Error en Message.mark_as_read(): {str(e)}")
            connection.rollback()
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def delete(message_id, user_id):
        """Elimina un mensaje (borrado lógico)"""
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                """UPDATE messages 
                SET deleted_at = NOW() 
                WHERE id = %s AND user_id = %s AND deleted_at IS NULL""",
                (message_id, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error en Message.delete(): {str(e)}")
            connection.rollback()
            return False
        finally:
            Database.close_connection(connection, cursor)