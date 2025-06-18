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
