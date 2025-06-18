from src.config.database import Database
from datetime import datetime

class Event:
    @staticmethod   
    def create(user_id, title, description, start_datetime, end_datetime=None, location=None):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
        # Manejar diferentes formatos de fecha
            if isinstance(start_datetime, str):
                try:
                # Primero intentar con formato ISO (de Flutter)
                    start_datetime = datetime.fromisoformat(start_datetime.replace('Z', ''))
                except ValueError:
                # Si falla, intentar con el formato antiguo
                    start_datetime = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
        
            if end_datetime and isinstance(end_datetime, str):
                try:
                    end_datetime = datetime.fromisoformat(end_datetime.replace('Z', ''))
                except ValueError:
                    end_datetime = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')

            cursor.execute( 
                """INSERT INTO events 
                (user_id, title, description, start_datetime, end_datetime, location) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, title, description, start_datetime, end_datetime, location)
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
                """SELECT id, title, description, 
                    start_datetime, 
                    end_datetime, 
                    location 
                FROM events WHERE user_id = %s""",
                (user_id,)
            )
            events = cursor.fetchall()
            
            # Formatear fechas a strings
            for event in events:
                if event['start_datetime']:
                    event['start_datetime'] = event['start_datetime'].strftime('%Y-%m-%d %H:%M:%S')
                if event['end_datetime']:
                    event['end_datetime'] = event['end_datetime'].strftime('%Y-%m-%d %H:%M:%S')
            
            return events
        except Exception as e:
            raise e
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def update(event_id, user_id, data):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            # Convertir fechas si vienen como strings
            start_datetime = data.get('start_datetime')
            if start_datetime and isinstance(start_datetime, str):
                start_datetime = datetime.strptime(start_datetime, '%Y-%m-%d %H:%M:%S')
            
            end_datetime = data.get('end_datetime')
            if end_datetime and isinstance(end_datetime, str):
                end_datetime = datetime.strptime(end_datetime, '%Y-%m-%d %H:%M:%S')

            cursor.execute(
                """UPDATE events 
                SET title=%s, description=%s, start_datetime=%s, end_datetime=%s, location=%s
                WHERE id=%s AND user_id=%s""",
                (data.get('title'), data.get('description'), 
                start_datetime, end_datetime,
                data.get('location'), event_id, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def delete(event_id, user_id):
        connection = Database.get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM events WHERE id = %s AND user_id = %s",
                (event_id, user_id)
            )
            connection.commit()
            return cursor.rowcount > 0
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_upcoming(user_id, limit=5):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT id, title, start_datetime 
                FROM events 
                WHERE user_id = %s AND start_datetime >= NOW() 
                ORDER BY start_datetime ASC LIMIT %s""",
                (user_id, limit)
            )
            events = cursor.fetchall()
            
            # Formatear fechas a strings
            for event in events:
                if event['start_datetime']:
                    event['start_datetime'] = event['start_datetime'].strftime('%Y-%m-%d %H:%M:%S')
            
            return events
        except Exception as e:
            raise e
        finally:
            Database.close_connection(connection, cursor)