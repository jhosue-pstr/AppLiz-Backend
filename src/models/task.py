from src.config.database import Database

class Task:
    @staticmethod
    def create(user_id, title, description=None, due_date=None, priority='media'):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """INSERT INTO tasks 
                (user_id, title, description, due_date, priority) 
                VALUES (%s, %s, %s, %s, %s)""",
                (user_id, title, description, due_date, priority)
            )
            connection.commit()
            return cursor.lastrowid
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_by_user(user_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT id, title, description, due_date, priority, status 
                FROM tasks WHERE user_id = %s""",
                (user_id,)
            )
            return cursor.fetchall()
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def update(task_id, user_id, data):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """UPDATE tasks 
                SET title=%s, description=%s, due_date=%s, priority=%s, status=%s
                WHERE id=%s AND user_id=%s""",
                (data.get('title'), data.get('description'), data.get('due_date'),
                 data.get('priority'), data.get('status'), task_id, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def delete(task_id, user_id):
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM tasks WHERE id = %s AND user_id = %s",
                (task_id, user_id)
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
                """SELECT id, title, description 
                FROM tasks 
                WHERE user_id = %s AND (title LIKE %s OR description LIKE %s)""",
                (user_id, f"%{query}%", f"%{query}%")
            )
            return cursor.fetchall()
        finally:
            Database.close_connection(connection, cursor)