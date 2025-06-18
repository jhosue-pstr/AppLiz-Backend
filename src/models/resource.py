from src.config.database import Database

class Resource:
    @staticmethod
    def create(title, url, resource_type, description=None):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """INSERT INTO resources 
                (title, url, type, description) 
                VALUES (%s, %s, %s, %s)""",
                (title, url, resource_type, description)
            )
            connection.commit()
            return cursor.lastrowid
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_all(resource_type=None):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            if resource_type:
                cursor.execute(
                    "SELECT * FROM resources WHERE type = %s",
                    (resource_type,)
                )
            else:
                cursor.execute("SELECT * FROM resources")
            return cursor.fetchall()
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_by_id(resource_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM resources WHERE id = %s",
                (resource_id,)
            )
            return cursor.fetchone()
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def update(resource_id, title, url, resource_type, description=None):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """UPDATE resources 
                SET title=%s, url=%s, type=%s, description=%s
                WHERE id=%s""",
                (title, url, resource_type, description, resource_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def delete(resource_id):
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM resources WHERE id = %s",
                (resource_id,)
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            Database.close_connection(connection, cursor)