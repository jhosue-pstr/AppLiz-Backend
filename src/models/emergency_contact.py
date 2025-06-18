from src.config.database import Database

class EmergencyContact:
    @staticmethod
    def create(name, phone, description, category):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """INSERT INTO emergency_contacts 
                (name, phone, description, category) 
                VALUES (%s, %s, %s, %s)""",
                (name, phone, description, category)
            )
            connection.commit()
            return cursor.lastrowid
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_all():
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM emergency_contacts")
            return cursor.fetchall()
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_by_id(contact_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM emergency_contacts WHERE id = %s",
                (contact_id,)
            )
            return cursor.fetchone()
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def update(contact_id, name, phone, description, category):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """UPDATE emergency_contacts 
                SET name=%s, phone=%s, description=%s, category=%s
                WHERE id=%s""",
                (name, phone, description, category, contact_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def delete(contact_id):
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM emergency_contacts WHERE id = %s",
                (contact_id,)
            )
            connection.commit()
            return cursor.rowcount > 0
        finally:
            Database.close_connection(connection, cursor)