from src.config.database import Database

class PointSystem:

    @staticmethod
    def add_daily_coins(user_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            # Verificar si ya recibió monedas hoy
            cursor.execute(
                """SELECT last_reward_date FROM user_points 
                WHERE user_id = %s AND last_reward_date = CURRENT_DATE""",
                (user_id,)
            )
            if cursor.fetchone():
                return False  # Ya recibió monedas hoy

            # Dar 3 monedas y actualizar fecha
            cursor.execute(
                """INSERT INTO user_points (user_id, balance, last_reward_date)
                VALUES (%s, 3, CURRENT_DATE)
                ON DUPLICATE KEY UPDATE
                balance = balance + 3,
                last_reward_date = CURRENT_DATE""",
                (user_id,)
            )
            connection.commit()
            return True
        finally:
            Database.close_connection(connection, cursor)


    @staticmethod
    def get_balance(user_id):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT balance FROM user_points WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            return result['balance'] if result else 0
        finally:
            Database.close_connection(connection, cursor)

    @staticmethod
    def subtract_points(user_id, points):
        connection = Database.get_connection()
        cursor = connection.cursor(dictionary=True)
        try:
            # Resta los puntos solo si tiene suficiente saldo
            cursor.execute(
                """UPDATE user_points 
                SET balance = balance - %s 
                WHERE user_id = %s AND balance >= %s""",
                (points, user_id, points)
            )
            connection.commit()
            return cursor.rowcount > 0  # True si se actualizó, False si no
        finally:
            Database.close_connection(connection, cursor)