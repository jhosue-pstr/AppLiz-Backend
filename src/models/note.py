from src.config.database import Database

class Note:
    @staticmethod
    def create(user_id, title, content, color="#FFFFFF", pinned=False):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """INSERT INTO notes 
                (user_id, title, content, color, pinned) 
                VALUES (%s, %s, %s, %s, %s)""",
                (user_id, title, content, color, pinned)
            )
            connection.commit()
            return cursor.lastrowid
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_by_user(user_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, title, content, color, pinned FROM notes WHERE user_id = %s",
                (user_id,)
            )
            return cursor.fetchall()
        except Exception as e:
            raise e
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def update(note_id, user_id, data):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """UPDATE notes 
                SET title = %s, content = %s, color = %s, pinned = %s 
                WHERE id = %s AND user_id = %s""",
                (data['title'], data['content'], data.get('color'), data.get('pinned', False), 
                note_id, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def delete(note_id, user_id):
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM notes WHERE id = %s AND user_id = %s",
                (note_id, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def search(user_id, query):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT id, title, content 
                FROM notes 
                WHERE user_id = %s AND (title LIKE %s OR content LIKE %s)""",
                (user_id, f"%{query}%", f"%{query}%")
            )
            return cursor.fetchall()
        finally:
            Database.close_connection(connection, cursor)