from src.config.database import Database
from datetime import datetime

class Period:
    @staticmethod
    def close_period(user_id, name, start_date, end_date, summary=None):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            # Verificar si el usuario es admin
            cursor.execute(
                "SELECT is_admin FROM users WHERE id = %s",
                (user_id,)
            )
            user = cursor.fetchone()
            
            if not user or not user['is_admin']:
                return False

            # Cerrar el periodo
            cursor.execute(
                """INSERT INTO periods 
                (user_id, name, start_date, end_date, is_closed, summary, closed_at) 
                VALUES (%s, %s, %s, %s, %s, %s, NOW())""",
                (user_id, name, start_date, end_date, True, summary)
            )
            connection.commit()
            return True
        except Exception as e:
            print(f"Error closing period: {e}")
            connection.rollback()
            return False
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def get_closed_periods():
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT 
                    p.id, 
                    CONCAT(u.name, ' ', u.lastname_paternal) as user_name,
                    p.name as period_name,
                    p.start_date,
                    p.end_date,
                    p.summary as description,
                    DATE_FORMAT(p.closed_at, '%Y-%m-%d %H:%i:%s') as closed_at
                FROM periods p
                JOIN users u ON p.user_id = u.id
                WHERE p.is_closed = 1
                ORDER BY p.closed_at DESC"""
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"Error getting closed periods: {e}")
            return []
        finally:
            Database.close_connection(connection, cursor)